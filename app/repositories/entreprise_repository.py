"""
Repository PostgreSQL du module Entreprises.

RÔLE DU FICHIER
---------------
Centraliser les requêtes SQLAlchemy relatives aux entreprises.

Le repository :
    - lit PostgreSQL ;
    - recherche les entreprises ;
    - vérifie les zones administratives.

Le repository NE décide PAS :
    - des permissions ;
    - des règles métier ;
    - du contenu du journal d'audit.

Ces responsabilités appartiennent aux couches supérieures.
"""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import (
    and_,
    case,
    distinct,
    func,
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certification import Certification
from app.models.classification_entreprise import ClassificationEntreprise
from app.models.controle_fuccs import ControleFuccs
from app.models.dossier_verification import DossierVerification
from app.models.entreprise import Entreprise
from app.models.fiche_collecte import FicheCollecte
from app.models.zone_administrative import (
    ZoneAdministrative,
)


class EntrepriseRepository:

    # ========================================================
    # RECHERCHE PAR IDENTIFIANT TECHNIQUE
    # ========================================================

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        entreprise_id: UUID,
    ) -> Entreprise | None:

        result = await db.execute(
            select(Entreprise).where(
                Entreprise.id == entreprise_id
            )
        )

        return result.scalar_one_or_none()


    # ========================================================
    # RECHERCHE PAR IDENTIFIANT NATIONAL
    # ========================================================

    @staticmethod
    async def get_by_identifiant_national(
        db: AsyncSession,
        identifiant_national: str,
    ) -> Entreprise | None:
        """
        identifiant_national possède une contrainte UNIQUE
        dans PostgreSQL.
        """

        result = await db.execute(
            select(Entreprise).where(
                Entreprise.identifiant_national
                == identifiant_national
            )
        )

        return result.scalar_one_or_none()


    # ========================================================
    # VÉRIFICATION DE LA ZONE ADMINISTRATIVE
    # ========================================================

    @staticmethod
    async def zone_exists(
        db: AsyncSession,
        zone_id: UUID,
    ) -> bool:
        """
        Évite de laisser PostgreSQL découvrir tardivement
        une zone_siege_id inexistante via une erreur FK.
        """

        result = await db.execute(
            select(ZoneAdministrative.id).where(
                ZoneAdministrative.id == zone_id
            )
        )

        return (
            result.scalar_one_or_none()
            is not None
        )


    # ========================================================
    # LISTE / RECHERCHE
    # ========================================================

    @staticmethod
    async def list_entreprises(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        zone_siege_id: UUID | None,
        secteur: str | None = None,
        include_archived: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[Entreprise], int]:
        """
        Recherche paginée.

        search recherche notamment dans :
        - identifiant national ;
        - raison sociale ;
        - nom commercial ;
        - RCCM ;
        - NIF ;
        - IFU.
        """

        filters = []

        # ----------------------------------------------------
        # Par défaut, les archives ne polluent pas la liste
        # opérationnelle.
        # ----------------------------------------------------

        if not include_archived:
            filters.append(
                or_(
                    Entreprise.statut.is_(None),
                    Entreprise.statut != "ARCHIVE",
                )
            )

        # ----------------------------------------------------
        # Filtre explicite de statut
        # ----------------------------------------------------

        if statut:
            filters.append(
                Entreprise.statut
                == statut.strip().upper()
            )

        # ----------------------------------------------------
        # Filtre géographique
        # ----------------------------------------------------

        if zone_siege_id is not None:
            filters.append(
                Entreprise.zone_siege_id.in_(
                    EntrepriseRepository.zone_scope_subquery(
                        zone_siege_id
                    )
                )
            )

        if secteur and secteur.strip():
            filters.append(
                func.upper(
                    func.coalesce(
                        Entreprise.activite_principale,
                        "",
                    )
                ) == secteur.strip().upper()
            )

        # ----------------------------------------------------
        # Recherche textuelle
        # ----------------------------------------------------

        if search and search.strip():

            pattern = (
                f"%{search.strip()}%"
            )

            filters.append(
                or_(
                    Entreprise.identifiant_national.ilike(
                        pattern
                    ),
                    Entreprise.raison_sociale.ilike(
                        pattern
                    ),
                    Entreprise.nom_commercial.ilike(
                        pattern
                    ),
                    Entreprise.rccm.ilike(
                        pattern
                    ),
                    Entreprise.nif.ilike(
                        pattern
                    ),
                    Entreprise.ifu.ilike(
                        pattern
                    ),
                )
            )

        # ----------------------------------------------------
        # Requête de données
        # ----------------------------------------------------

        query = (
            select(Entreprise)
            .where(*filters)
            .order_by(
                Entreprise.raison_sociale,
                Entreprise.nom_commercial,
                Entreprise.identifiant_national,
            )
            .limit(limit)
            .offset(offset)
        )

        result = await db.execute(query)

        entreprises = list(
            result.scalars().all()
        )

        # ----------------------------------------------------
        # COUNT séparé pour la pagination frontend.
        # ----------------------------------------------------

        count_query = (
            select(
                func.count(Entreprise.id)
            )
            .where(*filters)
        )

        total_result = await db.execute(
            count_query
        )

        total = int(
            total_result.scalar_one()
        )

        return entreprises, total

    # ========================================================
    # RCCM — UNICITÉ MÉTIER RM-11
    # ========================================================

    @staticmethod
    async def get_by_rccm(
        db: AsyncSession,
        rccm: str,
        *,
        exclude_id: UUID | None = None,
    ) -> Entreprise | None:
        normalized = rccm.strip().upper()

        filters = [
            func.upper(func.coalesce(Entreprise.rccm, ""))
            == normalized
        ]

        if exclude_id is not None:
            filters.append(Entreprise.id != exclude_id)

        result = await db.execute(
            select(Entreprise).where(*filters)
        )
        return result.scalar_one_or_none()


    # ========================================================
    # HIÉRARCHIE GÉOGRAPHIQUE
    # ========================================================

    @staticmethod
    def zone_scope_subquery(zone_id: UUID):
        """
        Retourne la zone demandée et tous ses descendants.

        Cela permet de filtrer par Région même lorsque `zone_siege_id`
        pointe sur une préfecture, une commune ou une localité.
        """
        scope = (
            select(ZoneAdministrative.id)
            .where(ZoneAdministrative.id == zone_id)
            .cte(name="entreprise_zone_scope", recursive=True)
        )

        scope = scope.union_all(
            select(ZoneAdministrative.id).where(
                ZoneAdministrative.parent_id == scope.c.id
            )
        )

        return select(scope.c.id)


    # ========================================================
    # FILTRES FRONTEND
    # ========================================================

    @staticmethod
    async def registry_filters(db: AsyncSession):
        zones_result = await db.execute(
            select(
                ZoneAdministrative.id,
                ZoneAdministrative.parent_id,
                ZoneAdministrative.code,
                ZoneAdministrative.nom,
                ZoneAdministrative.type_zone,
            )
            .where(
                ZoneAdministrative.nom.is_not(None),
                or_(
                    ZoneAdministrative.statut.is_(None),
                    func.upper(ZoneAdministrative.statut)
                    != "INACTIF",
                ),
            )
            .order_by(
                ZoneAdministrative.type_zone,
                ZoneAdministrative.nom,
            )
        )

        sectors_result = await db.execute(
            select(Entreprise.activite_principale)
            .where(
                Entreprise.activite_principale.is_not(None),
                func.trim(Entreprise.activite_principale) != "",
                or_(
                    Entreprise.statut.is_(None),
                    func.upper(Entreprise.statut) != "ARCHIVE",
                ),
            )
            .distinct()
            .order_by(Entreprise.activite_principale)
        )

        statuses_result = await db.execute(
            select(Entreprise.statut)
            .where(
                Entreprise.statut.is_not(None),
                func.trim(Entreprise.statut) != "",
                func.upper(Entreprise.statut) != "ARCHIVE",
            )
            .distinct()
            .order_by(Entreprise.statut)
        )

        return (
            list(zones_result.all()),
            [row[0] for row in sectors_result.all()],
            [row[0] for row in statuses_result.all()],
        )


    # ========================================================
    # REGISTRE ENRICHI
    # ========================================================

    @staticmethod
    def _registry_filters(
        *,
        search: str | None,
        statut: str | None,
        zone_id: UUID | None,
        secteur: str | None,
        include_archived: bool,
    ):
        filters = []

        if not include_archived:
            filters.append(
                or_(
                    Entreprise.statut.is_(None),
                    func.upper(Entreprise.statut) != "ARCHIVE",
                )
            )

        if statut:
            filters.append(
                func.upper(func.coalesce(Entreprise.statut, ""))
                == statut.strip().upper()
            )

        if zone_id:
            filters.append(
                Entreprise.zone_siege_id.in_(
                    EntrepriseRepository.zone_scope_subquery(zone_id)
                )
            )

        if secteur and secteur.strip():
            filters.append(
                func.upper(
                    func.coalesce(
                        Entreprise.activite_principale,
                        "",
                    )
                ) == secteur.strip().upper()
            )

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Entreprise.identifiant_national.ilike(pattern),
                    Entreprise.raison_sociale.ilike(pattern),
                    Entreprise.nom_commercial.ilike(pattern),
                    Entreprise.rccm.ilike(pattern),
                    Entreprise.nif.ilike(pattern),
                    Entreprise.ifu.ilike(pattern),
                )
            )

        return filters


    @staticmethod
    async def registry_rows(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        zone_id: UUID | None,
        secteur: str | None,
        include_archived: bool,
        sort: str,
        limit: int,
        offset: int,
    ):
        active_statuses = [
            "ACTIVE",
            "ACTIF",
            "VALIDE",
            "VALIDE_ACTIVE",
        ]

        cert_count = (
            select(
                Certification.entreprise_id.label("enterprise_id"),
                func.count(Certification.id).label("certifications_count"),
            )
            .group_by(Certification.entreprise_id)
            .subquery()
        )

        next_expiry = (
            select(
                Certification.entreprise_id.label("enterprise_id"),
                func.min(Certification.date_expiration).label("next_expiration"),
            )
            .where(
                Certification.date_expiration.is_not(None),
                Certification.date_expiration >= date.today(),
                func.upper(func.coalesce(Certification.statut, ""))
                .in_(active_statuses),
            )
            .group_by(Certification.entreprise_id)
            .subquery()
        )

        latest_score = (
            select(ClassificationEntreprise.score)
            .where(
                ClassificationEntreprise.entreprise_id
                == Entreprise.id
            )
            .order_by(
                ClassificationEntreprise.date_calcul.desc().nullslast(),
                ClassificationEntreprise.created_at.desc(),
            )
            .limit(1)
            .correlate(Entreprise)
            .scalar_subquery()
        )

        latest_class = (
            select(ClassificationEntreprise.classe)
            .where(
                ClassificationEntreprise.entreprise_id
                == Entreprise.id
            )
            .order_by(
                ClassificationEntreprise.date_calcul.desc().nullslast(),
                ClassificationEntreprise.created_at.desc(),
            )
            .limit(1)
            .correlate(Entreprise)
            .scalar_subquery()
        )

        filters = EntrepriseRepository._registry_filters(
            search=search,
            statut=statut,
            zone_id=zone_id,
            secteur=secteur,
            include_archived=include_archived,
        )

        columns = [
            Entreprise,
            ZoneAdministrative.nom.label("zone_nom"),
            ZoneAdministrative.type_zone.label("zone_type"),
            func.coalesce(
                cert_count.c.certifications_count,
                0,
            ).label("certifications_count"),
            next_expiry.c.next_expiration,
            latest_score.label("classification_score"),
            latest_class.label("classification_classe"),
        ]

        stmt = (
            select(*columns)
            .select_from(Entreprise)
            .outerjoin(
                ZoneAdministrative,
                ZoneAdministrative.id == Entreprise.zone_siege_id,
            )
            .outerjoin(
                cert_count,
                cert_count.c.enterprise_id == Entreprise.id,
            )
            .outerjoin(
                next_expiry,
                next_expiry.c.enterprise_id == Entreprise.id,
            )
            .where(*filters)
        )

        normalized_sort = (sort or "name").strip().lower()

        if normalized_sort == "recent":
            stmt = stmt.order_by(Entreprise.updated_at.desc())
        elif normalized_sort == "score":
            stmt = stmt.order_by(
                latest_score.desc().nullslast(),
                Entreprise.raison_sociale,
            )
        elif normalized_sort == "expiry":
            stmt = stmt.order_by(
                next_expiry.c.next_expiration.asc().nullslast(),
                Entreprise.raison_sociale,
            )
        else:
            stmt = stmt.order_by(
                Entreprise.raison_sociale.asc().nullslast(),
                Entreprise.nom_commercial.asc().nullslast(),
                Entreprise.identifiant_national.asc(),
            )

        result = await db.execute(
            stmt.limit(limit).offset(offset)
        )

        count_result = await db.execute(
            select(func.count(Entreprise.id)).where(*filters)
        )

        return list(result.all()), int(count_result.scalar_one())


    @staticmethod
    async def registry_summary(
        db: AsyncSession,
        *,
        search: str | None,
        zone_id: UUID | None,
        secteur: str | None,
        include_archived: bool,
    ) -> dict[str, int]:
        base_filters = EntrepriseRepository._registry_filters(
            search=search,
            statut=None,
            zone_id=zone_id,
            secteur=secteur,
            include_archived=include_archived,
        )

        total_result = await db.execute(
            select(func.count(distinct(Entreprise.id)))
            .where(*base_filters)
        )

        active_statuses = [
            "ACTIVE",
            "ACTIF",
            "VALIDE",
            "VALIDE_ACTIVE",
        ]

        active_result = await db.execute(
            select(func.count(distinct(Entreprise.id)))
            .select_from(Entreprise)
            .join(
                Certification,
                Certification.entreprise_id == Entreprise.id,
            )
            .where(
                *base_filters,
                func.upper(func.coalesce(Certification.statut, ""))
                .in_(active_statuses),
                or_(
                    Certification.date_expiration.is_(None),
                    Certification.date_expiration >= date.today(),
                ),
            )
        )

        risk_result = await db.execute(
            select(func.count(distinct(Entreprise.id)))
            .select_from(Entreprise)
            .join(
                Certification,
                Certification.entreprise_id == Entreprise.id,
            )
            .where(
                *base_filters,
                Certification.certification_strategique.is_(True),
                Certification.date_expiration.is_not(None),
                Certification.date_expiration >= date.today(),
                Certification.date_expiration
                <= date.today() + timedelta(days=90),
            )
        )

        non_compliant_result = await db.execute(
            select(func.count(distinct(Entreprise.id)))
            .where(
                *base_filters,
                func.upper(func.coalesce(Entreprise.statut, ""))
                == "NON_CONFORME",
            )
        )

        pending_result = await db.execute(
            select(func.count(distinct(Entreprise.id)))
            .where(
                *base_filters,
                func.upper(func.coalesce(Entreprise.statut, ""))
                == "EN_ATTENTE_REGULARISATION",
            )
        )

        return {
            "total": int(total_result.scalar_one()),
            "certified_active": int(active_result.scalar_one()),
            "at_risk": int(risk_result.scalar_one()),
            "non_compliant": int(non_compliant_result.scalar_one()),
            "pending_regularization": int(pending_result.scalar_one()),
        }


    # ========================================================
    # CONTRÔLES FUCCS D'UNE ENTREPRISE
    # ========================================================

    @staticmethod
    async def enterprise_controls(
        db: AsyncSession,
        entreprise_id: UUID,
    ):
        result = await db.execute(
            select(ControleFuccs)
            .select_from(ControleFuccs)
            .join(
                DossierVerification,
                DossierVerification.id
                == ControleFuccs.dossier_verification_id,
            )
            .join(
                FicheCollecte,
                FicheCollecte.id
                == DossierVerification.fiche_collecte_id,
            )
            .where(FicheCollecte.entreprise_id == entreprise_id)
            .order_by(
                ControleFuccs.date_fin.desc().nullslast(),
                ControleFuccs.created_at.desc(),
            )
        )
        return list(result.scalars().all())

