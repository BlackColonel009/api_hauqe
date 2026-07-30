from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import write_audit_event
from app.database.session import get_db
from app.models.referentiel import Referentiel, ValeurReferentiel
from app.permissions.auth import require_permission
from app.schemas.referentiel import (
    ReferentielCreate,
    ReferentielListResponse,
    ReferentielResponse,
    ReferentielUpdate,
    ValeurReferentielCreate,
    ValeurReferentielResponse,
    ValeurReferentielUpdate,
)
from app.services.auth_service import AuthContext


router = APIRouter(prefix="/referentiels", tags=["Référentiels"])

DEFAULT_REFERENTIALS = [
    ("STATUT_ENTREPRISE", "Statuts des entreprises", ["ACTIVE", "INACTIVE", "A_COMPLETER", "SUSPENDUE"]),
    ("STATUT_CERTIFICATION", "Statuts des certifications", ["BROUILLON", "VALIDE", "EXPIRE", "SUSPENDU", "RETIRE"]),
    ("TYPE_CERTIFICATION", "Types de certifications", ["SYSTEME", "PRODUIT", "SERVICE", "PERSONNE"]),
    ("DOMAINE_NORMATIF", "Domaines et référentiels normatifs", ["QUALITE", "ENVIRONNEMENT", "SECURITE_ALIMENTAIRE", "SANTE_SECURITE", "BIO"]),
    ("TYPE_ORGANISME", "Types d’organismes", ["CERTIFICATION", "ACCREDITATION", "CONTROLE", "PARTENAIRE"]),
    ("PRIORITE", "Niveaux de priorité", ["BASSE", "NORMALE", "HAUTE", "CRITIQUE"]),
    ("TYPE_ECHEANCE", "Types d’échéances", ["AUDIT_SURVEILLANCE", "RENOUVELLEMENT", "EXPIRATION", "RELANCE", "ACTION"]),
    ("TYPE_DECISION", "Types de décisions", ["VALIDATION", "REJET", "SUSPENSION", "RETRAIT", "MESURE_CORRECTIVE"]),
    ("RISQUE_SNCC", "Niveaux de risque SNCC", ["R1", "R2", "R3", "R4", "R5"]),
    ("CLASSE_SNCC", "Classes SNCC", ["A_PLUS", "A", "B", "C", "D"]),
    ("CANAL_ECHANGE", "Canaux d’échange", ["EMAIL", "COURRIER", "TELEPHONE", "INTERFACE"]),
    ("CONFIDENTIALITE", "Niveaux de confidentialité", ["PUBLIC", "INTERNE", "CONFIDENTIEL", "RESTREINT"]),
]


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


async def ref_response(db: AsyncSession, item: Referentiel) -> ReferentielResponse:
    count = await db.scalar(
        select(func.count(ValeurReferentiel.id)).where(
            ValeurReferentiel.referentiel_id == item.id
        )
    )
    return ReferentielResponse(
        id=item.id, code=item.code, libelle=item.libelle,
        description=item.description, type_valeur=item.type_valeur,
        statut=item.statut, valeurs_count=int(count or 0),
        created_at=item.created_at, updated_at=item.updated_at,
    )


async def require_ref(db: AsyncSession, ref_id: UUID) -> Referentiel:
    item = await db.get(Referentiel, ref_id)
    if item is None:
        raise HTTPException(404, "Référentiel introuvable.")
    return item


async def require_value(db: AsyncSession, ref_id: UUID, value_id: UUID) -> ValeurReferentiel:
    item = await db.scalar(
        select(ValeurReferentiel).where(
            ValeurReferentiel.id == value_id,
            ValeurReferentiel.referentiel_id == ref_id,
        )
    )
    if item is None:
        raise HTTPException(404, "Valeur de référentiel introuvable.")
    return item


@router.get("", response_model=ReferentielListResponse)
async def list_referentiels(
    q: str | None = Query(default=None, max_length=255),
    statut_filtre: str | None = Query(default=None, alias="statut", max_length=255),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.LIRE")),
):
    filters = []
    if q:
        term = f"%{q.strip()}%"
        filters.append(or_(Referentiel.code.ilike(term), Referentiel.libelle.ilike(term)))
    if statut_filtre:
        filters.append(Referentiel.statut == statut_filtre.strip().upper())
    rows = list((await db.scalars(
        select(Referentiel).where(*filters).order_by(Referentiel.libelle, Referentiel.code)
    )).all())
    return ReferentielListResponse(
        total=len(rows),
        items=[await ref_response(db, row) for row in rows],
    )


@router.post("", response_model=ReferentielResponse, status_code=status.HTTP_201_CREATED)
async def create_referentiel(
    payload: ReferentielCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.ADMINISTRER_REGLES")),
):
    code = payload.code.strip().upper()
    if await db.scalar(select(Referentiel.id).where(Referentiel.code == code)):
        raise HTTPException(409, "Ce code de référentiel existe déjà.")
    item = Referentiel(
        code=code, libelle=payload.libelle.strip(),
        description=payload.description, type_valeur=payload.type_valeur,
        statut="ACTIF",
    )
    db.add(item)
    await db.flush()
    await write_audit_event(
        db, action="REFERENTIEL_CREATE", categorie="REFERENTIEL",
        resultat="SUCCES", utilisateur_id=actor.user.id,
        ressource_type="referentiel", ressource_id=item.id,
        adresse_ip=client_ip(request), valeurs_apres={"code": code},
    )
    await db.commit()
    await db.refresh(item)
    return await ref_response(db, item)


@router.post("/initialiser-type", response_model=ReferentielListResponse)
async def seed_default_referentials(
    request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.ADMINISTRER_REGLES")),
):
    """Ajoute uniquement les référentiels types encore absents."""
    existing = set((await db.scalars(select(Referentiel.code))).all())
    created = []
    for code, label, values in DEFAULT_REFERENTIALS:
        if code in existing:
            continue
        ref = Referentiel(
            code=code,
            libelle=label,
            description="Proposition HAUQE modifiable après initialisation.",
            type_valeur="LISTE",
            statut="ACTIF",
        )
        db.add(ref)
        await db.flush()
        for order, value_code in enumerate(values, start=1):
            db.add(ValeurReferentiel(
                referentiel_id=ref.id,
                code=value_code,
                libelle=value_code.replace("_", " ").title(),
                ordre_affichage=order,
                statut="ACTIF",
            ))
        created.append(ref)
    await write_audit_event(
        db, action="REFERENTIEL_TYPE_INITIALISE", categorie="REFERENTIEL",
        resultat="SUCCES", utilisateur_id=actor.user.id,
        ressource_type="referentiel", adresse_ip=client_ip(request),
        valeurs_apres={"codes_crees": [x.code for x in created]},
    )
    await db.commit()
    rows = list((await db.scalars(
        select(Referentiel).order_by(Referentiel.libelle, Referentiel.code)
    )).all())
    return ReferentielListResponse(
        total=len(rows),
        items=[await ref_response(db, row) for row in rows],
    )


@router.patch("/{ref_id}", response_model=ReferentielResponse)
async def update_referentiel(
    ref_id: UUID, payload: ReferentielUpdate, request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.ADMINISTRER_REGLES")),
):
    item = await require_ref(db, ref_id)
    before = {"libelle": item.libelle, "statut": item.statut}
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value.strip().upper() if key == "statut" and value else value)
    await write_audit_event(
        db, action="REFERENTIEL_UPDATE", categorie="REFERENTIEL",
        resultat="SUCCES", utilisateur_id=actor.user.id,
        ressource_type="referentiel", ressource_id=item.id,
        adresse_ip=client_ip(request), valeurs_avant=before,
        valeurs_apres={"libelle": item.libelle, "statut": item.statut},
    )
    await db.commit()
    await db.refresh(item)
    return await ref_response(db, item)


@router.get("/{ref_id}/valeurs", response_model=list[ValeurReferentielResponse])
async def list_values(
    ref_id: UUID,
    statut_filtre: str | None = Query(default=None, alias="statut", max_length=255),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.LIRE")),
):
    await require_ref(db, ref_id)
    filters = [ValeurReferentiel.referentiel_id == ref_id]
    if statut_filtre:
        filters.append(ValeurReferentiel.statut == statut_filtre.strip().upper())
    return list((await db.scalars(
        select(ValeurReferentiel).where(*filters).order_by(
            ValeurReferentiel.ordre_affichage.asc().nullslast(),
            ValeurReferentiel.libelle,
        )
    )).all())


@router.post("/{ref_id}/valeurs", response_model=ValeurReferentielResponse, status_code=201)
async def create_value(
    ref_id: UUID, payload: ValeurReferentielCreate, request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.ADMINISTRER_REGLES")),
):
    await require_ref(db, ref_id)
    code = payload.code.strip().upper()
    duplicate = await db.scalar(select(ValeurReferentiel.id).where(
        ValeurReferentiel.referentiel_id == ref_id,
        ValeurReferentiel.code == code,
    ))
    if duplicate:
        raise HTTPException(409, "Ce code existe déjà dans ce référentiel.")
    if payload.parent_id:
        await require_value(db, ref_id, payload.parent_id)
    item = ValeurReferentiel(
        referentiel_id=ref_id, code=code, libelle=payload.libelle.strip(),
        description=payload.description, parent_id=payload.parent_id,
        ordre_affichage=payload.ordre_affichage,
        date_debut_validite=payload.date_debut_validite,
        date_fin_validite=payload.date_fin_validite, statut="ACTIF",
    )
    db.add(item)
    await db.flush()
    await write_audit_event(
        db, action="REFERENTIEL_VALUE_CREATE", categorie="REFERENTIEL",
        resultat="SUCCES", utilisateur_id=actor.user.id,
        ressource_type="valeur_referentiel", ressource_id=item.id,
        adresse_ip=client_ip(request), valeurs_apres={"code": code},
    )
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/{ref_id}/valeurs/{value_id}", response_model=ValeurReferentielResponse)
async def update_value(
    ref_id: UUID, value_id: UUID, payload: ValeurReferentielUpdate, request: Request,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(require_permission("GOUVERNANCE.ADMINISTRER_REGLES")),
):
    item = await require_value(db, ref_id, value_id)
    before = {"code": item.code, "libelle": item.libelle, "statut": item.statut}
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("parent_id"):
        if changes["parent_id"] == item.id:
            raise HTTPException(422, "Une valeur ne peut pas être son propre parent.")
        await require_value(db, ref_id, changes["parent_id"])
    for key, value in changes.items():
        if key in {"code", "statut"} and value:
            value = value.strip().upper()
        setattr(item, key, value)
    await write_audit_event(
        db, action="REFERENTIEL_VALUE_UPDATE", categorie="REFERENTIEL",
        resultat="SUCCES", utilisateur_id=actor.user.id,
        ressource_type="valeur_referentiel", ressource_id=item.id,
        adresse_ip=client_ip(request), valeurs_avant=before,
        valeurs_apres={"code": item.code, "libelle": item.libelle, "statut": item.statut},
    )
    await db.commit()
    await db.refresh(item)
    return item
