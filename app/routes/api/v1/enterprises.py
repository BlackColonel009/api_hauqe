"""
Routes HTTP du module Entreprises.

RÔLE DU FICHIER
---------------
Exposer les opérations Entreprises dans /api/v1.

SÉCURITÉ
--------
Chaque opération est protégée par une permission serveur.

Le frontend ne peut pas contourner ces règles en masquant ou en
affichant simplement un bouton.

Permissions :
    ENTREPRISES.LIRE
    ENTREPRISES.CREER
    ENTREPRISES.MODIFIER
    ENTREPRISES.ARCHIVER
"""

from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.permissions.auth import (
    require_permission,
)
from app.schemas.entreprise import (
    EntrepriseArchiveRequest,
    EntrepriseControlSummaryResponse,
    EntrepriseCreateRequest,
    EntrepriseFiltersResponse,
    EntrepriseListResponse,
    EntrepriseRegistryResponse,
    EntrepriseResponse,
    EntrepriseUpdateRequest,
)
from app.services.auth_service import (
    AuthContext,
)
from app.services.entreprise_service import (
    EntrepriseService,
)


router = APIRouter(
    prefix="/entreprises",
    tags=["Entreprises"],
)


# ============================================================
# LISTE / RECHERCHE
# ============================================================

@router.get(
    "",
    response_model=EntrepriseListResponse,
)
async def list_entreprises(
    search: str | None = Query(
        default=None,
        max_length=255,
    ),

    statut: str | None = Query(
        default=None,
        max_length=255,
    ),

    zone_siege_id: UUID | None = Query(
        default=None
    ),

    secteur: str | None = Query(
        default=None,
        max_length=255,
    ),

    include_archived: bool = Query(
        default=False
    ),

    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),

    offset: int = Query(
        default=0,
        ge=0,
    ),

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.LIRE"
        )
    ),
):
    """
    Liste paginée et filtrable.

    Exemples :
        ?search=TOGO
        ?statut=ACTIF
        ?zone_siege_id=<uuid>
        ?limit=25&offset=0
    """

    return await (
        EntrepriseService.list_entreprises(
            db,
            search=search,
            statut=statut,
            zone_siege_id=zone_siege_id,
            secteur=secteur,
            include_archived=include_archived,
            limit=limit,
            offset=offset,
        )
    )


# ============================================================
# FILTRES DU REGISTRE
# ============================================================

@router.get(
    "/filters",
    response_model=EntrepriseFiltersResponse,
)
async def entreprise_filters(
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ENTREPRISES.LIRE")
    ),
):
    return await EntrepriseService.registry_filters(db)


# ============================================================
# REGISTRE ENRICHI
# ============================================================

@router.get(
    "/registry",
    response_model=EntrepriseRegistryResponse,
)
async def entreprise_registry(
    search: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    zone_id: UUID | None = Query(default=None),
    secteur: str | None = Query(default=None, max_length=255),
    include_archived: bool = Query(default=False),
    sort: str = Query(default="name", pattern="^(name|recent|score|expiry)$"),
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ENTREPRISES.LIRE")
    ),
):
    return await EntrepriseService.registry(
        db,
        search=search,
        statut=statut,
        zone_id=zone_id,
        secteur=secteur,
        include_archived=include_archived,
        sort=sort,
        limit=limit,
        offset=offset,
    )


# ============================================================
# EXPORT CSV DU REGISTRE
# ============================================================

@router.get("/export")
async def export_entreprises(
    request: Request,
    motif: str = Query(min_length=3, max_length=2000),
    search: str | None = Query(default=None, max_length=255),
    statut: str | None = Query(default=None, max_length=255),
    zone_id: UUID | None = Query(default=None),
    secteur: str | None = Query(default=None, max_length=255),
    include_archived: bool = Query(default=False),
    sort: str = Query(default="name", pattern="^(name|recent|score|expiry)$"),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ENTREPRISES.EXPORTER")
    ),
):
    content = await EntrepriseService.export_registry_csv(
        db,
        search=search,
        statut=statut,
        zone_id=zone_id,
        secteur=secteur,
        include_archived=include_archived,
        sort=sort,
        motif=motif,
        actor=actor,
        request=request,
    )

    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="hauqe-entreprises.csv"'
            )
        },
    )


# ============================================================
# LISTE DES ENTREPRISES ARCHIVÉES
# ============================================================

@router.get(
    "/archives",
    response_model=EntrepriseListResponse,
)
async def list_archived_entreprises(
    search: str | None = Query(
        default=None,
        max_length=255,
    ),

    zone_siege_id: UUID | None = Query(
        default=None
    ),

    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),

    offset: int = Query(
        default=0,
        ge=0,
    ),

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.LIRE"
        )
    ),
):
    """
    Retourne uniquement les entreprises archivées.

    Cette route est séparée de la liste opérationnelle afin de
    permettre au frontend d'avoir une page dédiée aux archives.

    Aucun enregistrement n'est supprimé physiquement.
    Une entreprise archivée reste présente dans PostgreSQL avec :

        statut = ARCHIVE
    """

    return await (
        EntrepriseService.list_entreprises(
            db,
            search=search,

            # ------------------------------------------------
            # On impose ARCHIVE côté serveur.
            # Le frontend ne peut donc pas détourner ce endpoint
            # pour consulter un autre statut.
            # ------------------------------------------------
            statut="ARCHIVE",

            zone_siege_id=zone_siege_id,

            # ------------------------------------------------
            # Obligatoire ici, sinon le repository exclurait
            # les archives par défaut.
            # ------------------------------------------------
            include_archived=True,

            limit=limit,
            offset=offset,
        )
    )

# ============================================================
# DÉTAIL
# ============================================================

# ============================================================
# EXPORT DU DOSSIER ENTREPRISE
# ============================================================

@router.get("/{entreprise_id}/export")
async def export_entreprise_dossier(
    entreprise_id: UUID,
    request: Request,
    motif: str = Query(min_length=3, max_length=2000),
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("ENTREPRISES.EXPORTER")
    ),
):
    content = await EntrepriseService.export_dossier_csv(
        db,
        entreprise_id=entreprise_id,
        motif=motif,
        actor=actor,
        request=request,
    )

    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="hauqe-entreprise-{entreprise_id}.csv"'
            )
        },
    )


@router.get(
    "/{entreprise_id}",
    response_model=EntrepriseResponse,
)
async def get_entreprise(
    entreprise_id: UUID,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.LIRE"
        )
    ),
):

    return await (
        EntrepriseService.get_entreprise(
            db,
            entreprise_id=entreprise_id,
        )
    )


# ============================================================
# CONTRÔLES FUCCS RATTACHÉS À L'ENTREPRISE
# ============================================================

@router.get(
    "/{entreprise_id}/controls-summary",
    response_model=EntrepriseControlSummaryResponse,
)
async def entreprise_controls_summary(
    entreprise_id: UUID,
    db: AsyncSession = Depends(get_db),
    actor: AuthContext = Depends(
        require_permission("FUCCS.LIRE")
    ),
):
    return await EntrepriseService.controls_summary(
        db,
        entreprise_id=entreprise_id,
    )


# ============================================================
# CRÉATION
# ============================================================

@router.post(
    "",
    response_model=EntrepriseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_entreprise(
    payload: EntrepriseCreateRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.CREER"
        )
    ),
):

    return await (
        EntrepriseService.create_entreprise(
            db,
            payload=payload,
            actor=actor,
            request=request,
        )
    )


# ============================================================
# MODIFICATION
# ============================================================

@router.patch(
    "/{entreprise_id}",
    response_model=EntrepriseResponse,
)
async def update_entreprise(
    entreprise_id: UUID,
    payload: EntrepriseUpdateRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.MODIFIER"
        )
    ),
):

    return await (
        EntrepriseService.update_entreprise(
            db,
            entreprise_id=entreprise_id,
            payload=payload,
            actor=actor,
            request=request,
        )
    )


# ============================================================
# ARCHIVAGE LOGIQUE
# ============================================================

@router.post(
    "/{entreprise_id}/archive",
    response_model=EntrepriseResponse,
)
async def archive_entreprise(
    entreprise_id: UUID,
    payload: EntrepriseArchiveRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.ARCHIVER"
        )
    ),
):
    """
    Aucun DELETE physique.

    L'entreprise reste dans PostgreSQL avec :
        statut = ARCHIVE
    """

    return await (
        EntrepriseService.archive_entreprise(
            db,
            entreprise_id=entreprise_id,
            motif=payload.motif,
            actor=actor,
            request=request,
        )
    )

# ============================================================
# DÉSARCHIVAGE / RESTAURATION
# ============================================================

@router.post(
    "/{entreprise_id}/restore",
    response_model=EntrepriseResponse,
)
async def restore_entreprise(
    entreprise_id: UUID,
    payload: EntrepriseArchiveRequest,
    request: Request,

    db: AsyncSession = Depends(get_db),

    actor: AuthContext = Depends(
        require_permission(
            "ENTREPRISES.ARCHIVER"
        )
    ),
):
    """
    Restaure une entreprise archivée.

    Pour le moment, la permission ENTREPRISES.ARCHIVER
    couvre les deux opérations de cycle de vie :
    archivage et restauration.
    """

    return await (
        EntrepriseService.restore_entreprise(
            db,
            entreprise_id=entreprise_id,
            motif=payload.motif,
            actor=actor,
            request=request,
        )
    )