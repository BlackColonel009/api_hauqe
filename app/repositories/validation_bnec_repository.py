"""
Repository PostgreSQL — Validation / Corrections / Intégration BNEC.

Le repository assure :
- recherche du contrôle FUCCS finalisé d'une fiche ;
- historique des deux niveaux de validation ;
- corrections liées à une décision ;
- file et journal des intégrations BNEC ;
- éléments d'intégration.

Les règles de décision restent dans le service.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.certification import Certification
from app.models.certification_declaree import CertificationDeclaree
from app.models.controle_fuccs import ControleFuccs
from app.models.correction import Correction
from app.models.dossier_verification import DossierVerification
from app.models.element_integration import ElementIntegration
from app.models.entreprise import Entreprise
from app.models.fiche_collecte import FicheCollecte
from app.models.integration_bnec import IntegrationBnec
from app.models.norme import Norme
from app.models.offre_declaree import OffreDeclaree
from app.models.offre_entreprise import OffreEntreprise
from app.models.organisme import Organisme
from app.models.regle_metier import RegleMetier
from app.models.zone_administrative import ZoneAdministrative
from app.models.validation import Validation


class ValidationBnecRepository:

    @staticmethod
    async def get_fiche_for_update(
        db: AsyncSession,
        fiche_id: UUID,
    ) -> FicheCollecte | None:
        result = await db.execute(
            select(FicheCollecte)
            .where(FicheCollecte.id == fiche_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    async def get_fiche(db: AsyncSession, fiche_id: UUID) -> FicheCollecte | None:
        result = await db.execute(
            select(FicheCollecte).where(FicheCollecte.id == fiche_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def latest_finalized_control_for_fiche(
        db: AsyncSession,
        fiche_id: UUID,
    ) -> ControleFuccs | None:
        result = await db.execute(
            select(ControleFuccs)
            .join(
                DossierVerification,
                DossierVerification.id == ControleFuccs.dossier_verification_id,
            )
            .where(
                DossierVerification.fiche_collecte_id == fiche_id,
                ControleFuccs.statut == "FINALISE",
                ControleFuccs.date_fin.is_not(None),
            )
            .order_by(
                ControleFuccs.date_fin.desc(),
                ControleFuccs.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_validation(
        db: AsyncSession,
        validation_id: UUID,
    ) -> Validation | None:
        result = await db.execute(
            select(Validation).where(Validation.id == validation_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def latest_validation_for_level(
        db: AsyncSession,
        *,
        fiche_id: UUID,
        level: str,
    ) -> Validation | None:
        result = await db.execute(
            select(Validation)
            .where(
                Validation.fiche_collecte_id == fiche_id,
                Validation.niveau_validation == level,
            )
            .order_by(
                Validation.date_validation.desc().nullslast(),
                Validation.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_validations(
        db: AsyncSession,
        *,
        fiche_id: UUID | None,
        niveau: str | None,
        decision: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Validation], int]:
        filters = []

        if fiche_id:
            filters.append(Validation.fiche_collecte_id == fiche_id)
        if niveau:
            filters.append(Validation.niveau_validation == niveau)
        if decision:
            filters.append(Validation.decision == decision)

        result = await db.execute(
            select(Validation)
            .where(*filters)
            .order_by(
                Validation.date_validation.desc().nullslast(),
                Validation.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(Validation.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def validation_queue_rows(db: AsyncSession):
        """
        Retourne les contrôles FUCCS finalisés avec leur fiche.

        Le service complète ensuite les décisions N1/N2 afin de garder
        la logique hiérarchique dans la couche métier.
        """
        result = await db.execute(
            select(ControleFuccs, DossierVerification)
            .join(
                DossierVerification,
                DossierVerification.id == ControleFuccs.dossier_verification_id,
            )
            .where(
                ControleFuccs.statut == "FINALISE",
                ControleFuccs.date_fin.is_not(None),
            )
            .order_by(
                ControleFuccs.date_fin.desc(),
                ControleFuccs.created_at.desc(),
            )
        )
        return list(result.all())

    # ========================================================
    # CORRECTIONS
    # ========================================================

    @staticmethod
    async def list_corrections(
        db: AsyncSession,
        validation_id: UUID,
    ) -> list[Correction]:
        result = await db.execute(
            select(Correction)
            .where(Correction.validation_id == validation_id)
            .order_by(Correction.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_correction(
        db: AsyncSession,
        *,
        validation_id: UUID,
        correction_id: UUID,
    ) -> Correction | None:
        result = await db.execute(
            select(Correction).where(
                Correction.id == correction_id,
                Correction.validation_id == validation_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def has_pending_correction(
        db: AsyncSession,
        validation_id: UUID,
    ) -> bool:
        result = await db.execute(
            select(Correction.id)
            .where(
                Correction.validation_id == validation_id,
                Correction.statut.in_(["DEMANDEE", "EN_COURS"]),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None


    # ========================================================
    # CODIFICATION INSTITUTIONNELLE
    # ========================================================

    @staticmethod
    async def active_codification_rule(
        db: AsyncSession,
        logical_code: str,
    ) -> RegleMetier | None:
        today = __import__("datetime").date.today()
        result = await db.execute(
            select(RegleMetier)
            .where(
                RegleMetier.statut == "PUBLIE",
                RegleMetier.parametres["_logical_code"].astext
                == logical_code.strip().upper(),
                or_(
                    RegleMetier.date_debut_effet.is_(None),
                    RegleMetier.date_debut_effet <= today,
                ),
                or_(
                    RegleMetier.date_fin_effet.is_(None),
                    RegleMetier.date_fin_effet >= today,
                ),
            )
            .order_by(
                RegleMetier.date_debut_effet.desc().nullslast(),
                RegleMetier.created_at.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_zone(
        db: AsyncSession,
        zone_id: UUID | None,
    ) -> ZoneAdministrative | None:
        if zone_id is None:
            return None
        result = await db.execute(
            select(ZoneAdministrative).where(ZoneAdministrative.id == zone_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def lock_codification_scope(
        db: AsyncSession,
        lock_key: str,
    ) -> None:
        # Verrou transactionnel PostgreSQL : deux intégrations concurrentes ne
        # peuvent pas réserver la même séquence pour un même modèle/périmètre.
        await db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": lock_key},
        )

    @staticmethod
    async def max_codification_sequence(
        db: AsyncSession,
        *,
        rule_id: UUID,
        scope_key: str,
    ) -> int:
        result = await db.execute(
            select(func.max(ElementIntegration.codification_sequence)).where(
                ElementIntegration.codification_regle_id == rule_id,
                ElementIntegration.codification_scope_key == scope_key,
            )
        )
        return int(result.scalar_one_or_none() or 0)

    @staticmethod
    async def generated_code_exists(
        db: AsyncSession,
        *,
        object_type: str,
        code: str,
        exclude_element_id: UUID | None = None,
    ) -> bool:
        object_type = object_type.strip().upper()
        if object_type == "ENTREPRISE":
            query = select(Entreprise.id).where(Entreprise.identifiant_national == code)
        elif object_type == "CERTIFICATION":
            query = select(Certification.id).where(
                Certification.identifiant_national == code
            )
        else:
            query = select(ElementIntegration.id).where(
                ElementIntegration.type_objet == object_type,
                ElementIntegration.code_genere == code,
            )
        result = await db.execute(query.limit(1))
        if result.scalar_one_or_none() is not None:
            return True

        filters = [ElementIntegration.code_genere == code]
        if exclude_element_id is not None:
            filters.append(ElementIntegration.id != exclude_element_id)
        result = await db.execute(
            select(ElementIntegration.id).where(*filters).limit(1)
        )
        return result.scalar_one_or_none() is not None

    # ========================================================
    # INTEGRATION
    # ========================================================

    @staticmethod
    async def get_integration(
        db: AsyncSession,
        integration_id: UUID,
    ) -> IntegrationBnec | None:
        result = await db.execute(
            select(IntegrationBnec).where(IntegrationBnec.id == integration_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def latest_integration_for_validation(
        db: AsyncSession,
        validation_id: UUID,
    ) -> IntegrationBnec | None:
        result = await db.execute(
            select(IntegrationBnec)
            .where(IntegrationBnec.validation_id == validation_id)
            .order_by(IntegrationBnec.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def active_integration_for_validation(
        db: AsyncSession,
        validation_id: UUID,
    ) -> IntegrationBnec | None:
        result = await db.execute(
            select(IntegrationBnec)
            .where(
                IntegrationBnec.validation_id == validation_id,
                IntegrationBnec.date_fin.is_(None),
                IntegrationBnec.statut != "INTEGREE",
            )
            .order_by(IntegrationBnec.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_integrations(
        db: AsyncSession,
        *,
        statut: str | None,
        validation_id: UUID | None,
        administrateur_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[IntegrationBnec], int]:
        filters = []
        if statut:
            filters.append(IntegrationBnec.statut == statut)
        if validation_id:
            filters.append(IntegrationBnec.validation_id == validation_id)
        if administrateur_id:
            filters.append(IntegrationBnec.administrateur_id == administrateur_id)

        result = await db.execute(
            select(IntegrationBnec)
            .where(*filters)
            .order_by(IntegrationBnec.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count = await db.execute(
            select(func.count(IntegrationBnec.id)).where(*filters)
        )
        return list(result.scalars().all()), int(count.scalar_one())

    @staticmethod
    async def favorable_level2_validations(db: AsyncSession) -> list[Validation]:
        result = await db.execute(
            select(Validation)
            .where(
                Validation.niveau_validation == "NIVEAU_2",
                Validation.decision.in_(["VALIDE", "VALIDE_SOUS_RESERVE"]),
                Validation.statut == "TERMINE",
            )
            .order_by(
                Validation.date_validation.desc().nullslast(),
                Validation.created_at.desc(),
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_elements(
        db: AsyncSession,
        integration_id: UUID,
    ) -> list[ElementIntegration]:
        result = await db.execute(
            select(ElementIntegration)
            .where(ElementIntegration.integration_bnec_id == integration_id)
            .order_by(ElementIntegration.created_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_element(
        db: AsyncSession,
        *,
        integration_id: UUID,
        element_id: UUID,
    ) -> ElementIntegration | None:
        result = await db.execute(
            select(ElementIntegration).where(
                ElementIntegration.id == element_id,
                ElementIntegration.integration_bnec_id == integration_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def integration_source_context(
        db: AsyncSession,
        integration_id: UUID,
    ):
        """Retourne la tentative, sa validation, la fiche et l'entreprise."""
        result = await db.execute(
            select(IntegrationBnec, Validation, FicheCollecte, Entreprise)
            .join(Validation, Validation.id == IntegrationBnec.validation_id)
            .join(FicheCollecte, FicheCollecte.id == Validation.fiche_collecte_id)
            .outerjoin(Entreprise, Entreprise.id == FicheCollecte.entreprise_id)
            .where(IntegrationBnec.id == integration_id)
        )
        return result.one_or_none()

    @staticmethod
    async def list_declared_offers(
        db: AsyncSession,
        fiche_id: UUID,
    ) -> list[OffreDeclaree]:
        result = await db.execute(
            select(OffreDeclaree)
            .where(OffreDeclaree.fiche_collecte_id == fiche_id)
            .order_by(OffreDeclaree.created_at, OffreDeclaree.id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_declared_certifications(
        db: AsyncSession,
        fiche_id: UUID,
    ) -> list[CertificationDeclaree]:
        result = await db.execute(
            select(CertificationDeclaree)
            .where(CertificationDeclaree.fiche_collecte_id == fiche_id)
            .order_by(CertificationDeclaree.created_at, CertificationDeclaree.id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_enterprise(
        db: AsyncSession,
        enterprise_id: UUID,
    ) -> Entreprise | None:
        result = await db.execute(
            select(Entreprise).where(Entreprise.id == enterprise_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_declared_offer(
        db: AsyncSession,
        source_id: UUID,
    ) -> OffreDeclaree | None:
        result = await db.execute(
            select(OffreDeclaree).where(OffreDeclaree.id == source_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_official_offer(
        db: AsyncSession,
        target_id: UUID,
    ) -> OffreEntreprise | None:
        result = await db.execute(
            select(OffreEntreprise).where(OffreEntreprise.id == target_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_official_offer(
        db: AsyncSession,
        *,
        enterprise_id: UUID,
        name: str,
        offer_type: str | None = None,
        category: str | None = None,
    ) -> OffreEntreprise | None:
        filters = [
            OffreEntreprise.entreprise_id == enterprise_id,
            func.lower(func.trim(OffreEntreprise.nom)) == name.strip().lower(),
        ]
        if offer_type:
            filters.append(
                func.lower(func.trim(OffreEntreprise.type_offre))
                == offer_type.strip().lower()
            )
        if category:
            filters.append(
                func.lower(func.trim(OffreEntreprise.categorie))
                == category.strip().lower()
            )
        result = await db.execute(
            select(OffreEntreprise)
            .where(*filters)
            .order_by(OffreEntreprise.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_declared_certification(
        db: AsyncSession,
        source_id: UUID,
    ) -> CertificationDeclaree | None:
        result = await db.execute(
            select(CertificationDeclaree).where(
                CertificationDeclaree.id == source_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_official_certification(
        db: AsyncSession,
        target_id: UUID,
    ) -> Certification | None:
        result = await db.execute(
            select(Certification).where(Certification.id == target_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_certification_by_number(
        db: AsyncSession,
        *,
        enterprise_id: UUID,
        number: str,
    ) -> Certification | None:
        result = await db.execute(
            select(Certification)
            .where(
                Certification.entreprise_id == enterprise_id,
                func.lower(func.trim(Certification.numero_certificat))
                == number.strip().lower(),
            )
            .order_by(Certification.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_certification_candidate(
        db: AsyncSession,
        *,
        enterprise_id: UUID,
        organisme_id: UUID,
        norme_id: UUID,
        scope: str | None,
    ) -> Certification | None:
        filters = [
            Certification.entreprise_id == enterprise_id,
            Certification.organisme_id == organisme_id,
            Certification.norme_id == norme_id,
        ]
        if scope:
            filters.append(
                func.lower(func.trim(Certification.portee))
                == scope.strip().lower()
            )
        result = await db.execute(
            select(Certification)
            .where(*filters)
            .order_by(Certification.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_organism_by_label(
        db: AsyncSession,
        label: str,
    ) -> Organisme | None:
        normalized = label.strip().lower()
        result = await db.execute(
            select(Organisme)
            .where(
                or_(
                    func.lower(func.trim(Organisme.nom_officiel)) == normalized,
                    func.lower(func.trim(Organisme.sigle)) == normalized,
                )
            )
            .order_by(Organisme.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_norm_by_label(
        db: AsyncSession,
        label: str,
    ) -> Norme | None:
        normalized = label.strip().lower()
        result = await db.execute(
            select(Norme)
            .where(
                or_(
                    func.lower(func.trim(Norme.code)) == normalized,
                    func.lower(func.trim(Norme.nom)) == normalized,
                )
            )
            .order_by(Norme.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_norms_for_matching(
        db: AsyncSession,
    ) -> list[Norme]:
        """Retourne le référentiel nécessaire au rapprochement normalisé.

        Le volume du référentiel des normes reste borné et nettement inférieur
        à celui des entreprises/certifications. Le classement place les normes
        actives et les plus récemment mises à jour en tête, mais l'arbitrage
        final est réalisé de façon déterministe dans le service métier.
        """

        result = await db.execute(
            select(Norme).order_by(
                Norme.statut.desc().nullslast(),
                Norme.updated_at.desc(),
                Norme.code,
                Norme.version,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_organism(
        db: AsyncSession,
        organisme_id: UUID,
    ) -> Organisme | None:
        result = await db.execute(
            select(Organisme).where(Organisme.id == organisme_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_norm(
        db: AsyncSession,
        norme_id: UUID,
    ) -> Norme | None:
        result = await db.execute(select(Norme).where(Norme.id == norme_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def count_active_certifications(
        db: AsyncSession,
        enterprise_id: UUID,
    ) -> int:
        result = await db.execute(
            select(func.count(Certification.id)).where(
                Certification.entreprise_id == enterprise_id,
                Certification.statut.in_([
                    "ACTIF",
                    "ACTIVE",
                    "VALIDE",
                    "VALIDE_ACTIVE",
                ]),
            )
        )
        return int(result.scalar_one())

    @staticmethod
    async def integration_counts(
        db: AsyncSession,
        integration_id: UUID,
    ) -> tuple[int, int, int]:
        total = await db.execute(
            select(func.count(ElementIntegration.id)).where(
                ElementIntegration.integration_bnec_id == integration_id
            )
        )
        success = await db.execute(
            select(func.count(ElementIntegration.id)).where(
                ElementIntegration.integration_bnec_id == integration_id,
                ElementIntegration.statut == "INTEGRE",
            )
        )
        error = await db.execute(
            select(func.count(ElementIntegration.id)).where(
                ElementIntegration.integration_bnec_id == integration_id,
                ElementIntegration.statut == "ECHEC",
            )
        )
        return (
            int(total.scalar_one()),
            int(success.scalar_one()),
            int(error.scalar_one()),
        )
