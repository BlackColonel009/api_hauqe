from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import and_, case, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.affectation_mission import AffectationMission
from app.models.campagne import Campagne
from app.models.entreprise import Entreprise
from app.models.fiche_collecte import FicheCollecte
from app.models.mission_collecte import MissionCollecte
from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.utilisateur import Utilisateur
from app.models.utilisateur_role import UtilisateurRole
from app.models.zone_administrative import ZoneAdministrative


class CollecteWorkspaceRepository:
    @staticmethod
    async def filters(db: AsyncSession) -> dict:
        campaigns_result = await db.execute(
            select(
                Campagne.id,
                Campagne.code,
                Campagne.nom,
            )
            .order_by(
                Campagne.date_debut.desc().nullslast(),
                Campagne.code.desc(),
            )
            .limit(200)
        )

        zones_result = await db.execute(
            select(
                ZoneAdministrative.id,
                ZoneAdministrative.code,
                ZoneAdministrative.nom,
                ZoneAdministrative.type_zone,
            )
            .where(
                or_(
                    ZoneAdministrative.statut.is_(None),
                    func.upper(ZoneAdministrative.statut) == "ACTIF",
                )
            )
            .order_by(
                ZoneAdministrative.type_zone,
                ZoneAdministrative.nom,
            )
        )

        # Candidats d'affectation : utilisateurs actifs possédant réellement
        # une permission de création ou modification de collecte.
        today = date.today()

        collectors_result = await db.execute(
            select(
                Utilisateur.id,
                Utilisateur.prenoms,
                Utilisateur.nom,
                Utilisateur.email,
            )
            .select_from(Utilisateur)
            .join(
                UtilisateurRole,
                UtilisateurRole.utilisateur_id == Utilisateur.id,
            )
            .join(Role, Role.id == UtilisateurRole.role_id)
            .join(
                RolePermission,
                RolePermission.role_id == Role.id,
            )
            .join(
                Permission,
                Permission.id == RolePermission.permission_id,
            )
            .where(
                or_(
                    Utilisateur.statut.is_(None),
                    func.upper(Utilisateur.statut) == "ACTIF",
                ),
                or_(
                    UtilisateurRole.statut.is_(None),
                    func.upper(UtilisateurRole.statut) == "ACTIF",
                ),
                or_(
                    UtilisateurRole.date_debut.is_(None),
                    UtilisateurRole.date_debut <= today,
                ),
                or_(
                    UtilisateurRole.date_fin.is_(None),
                    UtilisateurRole.date_fin >= today,
                ),
                Permission.code.in_(
                    [
                        "COLLECTE.CREER",
                        "COLLECTE.MODIFIER",
                    ]
                ),
            )
            .distinct()
            .order_by(
                Utilisateur.prenoms,
                Utilisateur.nom,
                Utilisateur.email,
            )
        )

        mission_statuses_result = await db.execute(
            select(MissionCollecte.statut)
            .where(
                MissionCollecte.statut.is_not(None),
                func.trim(MissionCollecte.statut) != "",
            )
            .distinct()
            .order_by(MissionCollecte.statut)
        )

        fiche_statuses_result = await db.execute(
            select(FicheCollecte.statut)
            .where(
                FicheCollecte.statut.is_not(None),
                func.trim(FicheCollecte.statut) != "",
            )
            .distinct()
            .order_by(FicheCollecte.statut)
        )

        campaigns = [
            {
                "id": row.id,
                "code": row.code,
                "label": (
                    f"{row.code} — {row.nom}"
                    if row.nom
                    else row.code
                ),
            }
            for row in campaigns_result.all()
        ]

        zones = [
            {
                "id": row.id,
                "code": row.code,
                "type": row.type_zone,
                "label": (
                    f"{row.nom} ({row.type_zone})"
                    if row.type_zone
                    else (row.nom or row.code or "Zone")
                ),
            }
            for row in zones_result.all()
        ]

        collectors = []
        for row in collectors_result.all():
            full_name = " ".join(
                part
                for part in (row.prenoms, row.nom)
                if part
            ).strip()

            collectors.append(
                {
                    "id": row.id,
                    "code": row.email,
                    "label": full_name or row.email,
                }
            )

        return {
            "campaigns": campaigns,
            "zones": zones,
            "collectors": collectors,
            "mission_statuses": [
                str(value).strip()
                for value in mission_statuses_result.scalars().all()
                if value
            ],
            "fiche_statuses": [
                str(value).strip()
                for value in fiche_statuses_result.scalars().all()
                if value
            ],
        }

    @staticmethod
    def current_revision_subquery():
        return (
            select(
                FicheCollecte.mission_id.label("mission_id"),
                func.max(
                    FicheCollecte.numero_revision
                ).label("numero_revision"),
            )
            .group_by(FicheCollecte.mission_id)
            .subquery()
        )

    @staticmethod
    def active_assignment_names():
        return (
            select(
                func.string_agg(
                    func.concat_ws(
                        literal(" "),
                        Utilisateur.prenoms,
                        Utilisateur.nom,
                    ),
                    literal(", "),
                )
            )
            .select_from(AffectationMission)
            .join(
                Utilisateur,
                Utilisateur.id == AffectationMission.utilisateur_id,
            )
            .where(
                AffectationMission.mission_id == MissionCollecte.id,
                or_(
                    AffectationMission.statut.is_(None),
                    func.upper(AffectationMission.statut) == "ACTIF",
                ),
            )
            .correlate(MissionCollecte)
            .scalar_subquery()
        )

    @staticmethod
    def build_filters(
        *,
        search: str | None,
        campagne_id: UUID | None,
        zone_id: UUID | None,
        assigned_user_id: UUID | None,
        mission_statut: str | None,
        fiche_statut: str | None,
    ):
        filters = []

        if campagne_id:
            filters.append(
                MissionCollecte.campagne_id == campagne_id
            )

        if zone_id:
            filters.append(
                MissionCollecte.zone_id == zone_id
            )

        if mission_statut:
            filters.append(
                func.upper(MissionCollecte.statut)
                == mission_statut.strip().upper()
            )

        if fiche_statut:
            normalized = fiche_statut.strip().upper()

            if normalized == "SANS_FICHE":
                filters.append(FicheCollecte.id.is_(None))
            else:
                filters.append(
                    func.upper(FicheCollecte.statut)
                    == normalized
                )

        if assigned_user_id:
            filters.append(
                select(AffectationMission.id)
                .where(
                    AffectationMission.mission_id
                    == MissionCollecte.id,
                    AffectationMission.utilisateur_id
                    == assigned_user_id,
                    or_(
                        AffectationMission.statut.is_(None),
                        func.upper(
                            AffectationMission.statut
                        ) == "ACTIF",
                    ),
                )
                .exists()
            )

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    MissionCollecte.code.ilike(pattern),
                    MissionCollecte.objet.ilike(pattern),
                    Campagne.code.ilike(pattern),
                    Campagne.nom.ilike(pattern),
                    ZoneAdministrative.nom.ilike(pattern),
                    Entreprise.identifiant_national.ilike(pattern),
                    Entreprise.raison_sociale.ilike(pattern),
                    Entreprise.nom_commercial.ilike(pattern),
                )
            )

        return filters

    @staticmethod
    def base_query():
        current_revision = (
            CollecteWorkspaceRepository
            .current_revision_subquery()
        )

        return (
            select(
                MissionCollecte,
                Campagne.code.label("campaign_code"),
                Campagne.nom.label("campaign_name"),
                ZoneAdministrative.nom.label("zone_name"),
                ZoneAdministrative.type_zone.label("zone_type"),
                FicheCollecte.id.label("fiche_id"),
                FicheCollecte.statut.label("fiche_status"),
                FicheCollecte.taux_completude.label("completeness"),
                FicheCollecte.numero_revision.label("revision_number"),
                FicheCollecte.collecte_at.label("collected_at"),
                FicheCollecte.soumise_at.label("submitted_at"),
                FicheCollecte.entreprise_id.label("entreprise_id"),
                Entreprise.raison_sociale.label("enterprise_name"),
                Entreprise.nom_commercial.label("enterprise_trade_name"),
                CollecteWorkspaceRepository
                .active_assignment_names()
                .label("assigned_names"),
            )
            .select_from(MissionCollecte)
            .join(
                Campagne,
                Campagne.id == MissionCollecte.campagne_id,
            )
            .join(
                ZoneAdministrative,
                ZoneAdministrative.id == MissionCollecte.zone_id,
            )
            .outerjoin(
                current_revision,
                current_revision.c.mission_id
                == MissionCollecte.id,
            )
            .outerjoin(
                FicheCollecte,
                and_(
                    FicheCollecte.mission_id
                    == MissionCollecte.id,
                    FicheCollecte.numero_revision
                    == current_revision.c.numero_revision,
                ),
            )
            .outerjoin(
                Entreprise,
                Entreprise.id == FicheCollecte.entreprise_id,
            )
        )

    @staticmethod
    async def registry(
        db: AsyncSession,
        *,
        search: str | None,
        campagne_id: UUID | None,
        zone_id: UUID | None,
        assigned_user_id: UUID | None,
        mission_statut: str | None,
        fiche_statut: str | None,
        sort: str,
        limit: int,
        offset: int,
    ):
        filters = CollecteWorkspaceRepository.build_filters(
            search=search,
            campagne_id=campagne_id,
            zone_id=zone_id,
            assigned_user_id=assigned_user_id,
            mission_statut=mission_statut,
            fiche_statut=fiche_statut,
        )

        order_by = {
            "recent": MissionCollecte.created_at.desc(),
            "campaign": Campagne.code.asc(),
            "zone": ZoneAdministrative.nom.asc(),
            "completion": FicheCollecte.taux_completude.desc().nullslast(),
            "status": MissionCollecte.statut.asc().nullslast(),
        }.get(
            sort,
            MissionCollecte.date_debut_prevue.asc().nullslast(),
        )

        stmt = (
            CollecteWorkspaceRepository.base_query()
            .where(*filters)
            .order_by(
                order_by,
                MissionCollecte.code.asc().nullslast(),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(stmt)

        count_stmt = (
            CollecteWorkspaceRepository.base_query()
            .with_only_columns(
                func.count(MissionCollecte.id)
            )
            .order_by(None)
            .where(*filters)
        )

        count_result = await db.execute(count_stmt)
        total = int(count_result.scalar_one() or 0)

        return result.all(), total

    @staticmethod
    async def summary(
        db: AsyncSession,
        *,
        search: str | None,
        campagne_id: UUID | None,
        zone_id: UUID | None,
        assigned_user_id: UUID | None,
        mission_statut: str | None,
        fiche_statut: str | None,
    ) -> dict:
        filters = CollecteWorkspaceRepository.build_filters(
            search=search,
            campagne_id=campagne_id,
            zone_id=zone_id,
            assigned_user_id=assigned_user_id,
            mission_statut=mission_statut,
            fiche_statut=fiche_statut,
        )

        query = (
            CollecteWorkspaceRepository.base_query()
            .with_only_columns(
                func.count(MissionCollecte.id).label("total_missions"),
                func.sum(
                    case(
                        (FicheCollecte.id.is_(None), 1),
                        else_=0,
                    )
                ).label("without_fiche"),
                func.sum(
                    case(
                        (
                            func.upper(
                                func.coalesce(
                                    FicheCollecte.statut,
                                    "",
                                )
                            ) == "BROUILLON",
                            1,
                        ),
                        else_=0,
                    )
                ).label("drafts"),
                func.sum(
                    case(
                        (
                            func.upper(
                                func.coalesce(
                                    FicheCollecte.statut,
                                    "",
                                )
                            ) == "SOUMISE",
                            1,
                        ),
                        else_=0,
                    )
                ).label("submitted"),
                func.sum(
                    case(
                        (
                            func.upper(
                                func.coalesce(
                                    FicheCollecte.statut,
                                    "",
                                )
                            ).in_(
                                [
                                    "A_CORRIGER",
                                    "À_CORRIGER",
                                    "CORRECTION",
                                ]
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("corrections"),
                func.avg(
                    FicheCollecte.taux_completude
                ).label("average_completeness"),
            )
            .order_by(None)
            .where(*filters)
        )

        result = await db.execute(query)
        row = result.one()

        return {
            "total_missions": int(row.total_missions or 0),
            "without_fiche": int(row.without_fiche or 0),
            "drafts": int(row.drafts or 0),
            "submitted": int(row.submitted or 0),
            "corrections": int(row.corrections or 0),
            "average_completeness": row.average_completeness,
        }

    @staticmethod
    async def find_exact_enterprise(
        db: AsyncSession,
        *,
        name: str,
        zone_id: UUID,
    ) -> Entreprise | None:
        result = await db.execute(
            select(Entreprise).where(
                func.lower(func.trim(Entreprise.raison_sociale))
                == name.strip().lower(),
                Entreprise.zone_siege_id == zone_id,
                or_(
                    Entreprise.statut.is_(None),
                    Entreprise.statut != "ARCHIVE",
                ),
            )
        )
        return result.scalars().first()

    @staticmethod
    async def get_zone(db: AsyncSession, zone_id: UUID) -> ZoneAdministrative | None:
        result = await db.execute(
            select(ZoneAdministrative).where(
                ZoneAdministrative.id == zone_id,
                or_(
                    ZoneAdministrative.statut.is_(None),
                    func.upper(ZoneAdministrative.statut) == "ACTIF",
                ),
            )
        )
        return result.scalar_one_or_none()
