from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.certification import Certification
from app.models.classement_sncc import ClassementSncc
from app.models.classification_entreprise import ClassificationEntreprise
from app.models.entreprise import Entreprise
from app.models.modele_scoring import ModeleScoring
from app.models.norme import Norme
from app.models.organisme import Organisme
from app.models.resultat_infc import ResultatInfc
from app.models.utilisateur import Utilisateur


class ScoringWorkspaceRepository:
    @staticmethod
    async def distinct_values(db: AsyncSession, column) -> list[str]:
        result = await db.execute(
            select(column)
            .where(
                column.is_not(None),
                func.trim(column) != "",
            )
            .distinct()
            .order_by(column)
        )
        return [
            str(value).strip()
            for value in result.scalars().all()
            if value
        ]

    @staticmethod
    def latest_classification_id():
        return (
            select(ClassificationEntreprise.id)
            .where(
                ClassificationEntreprise.entreprise_id
                == Entreprise.id
            )
            .order_by(
                ClassificationEntreprise.date_validation.desc().nullslast(),
                ClassificationEntreprise.created_at.desc(),
            )
            .limit(1)
            .correlate(Entreprise)
            .scalar_subquery()
        )

    @staticmethod
    async def classification_registry(
        db: AsyncSession,
        *,
        search: str | None,
        classe: str | None,
        statut: str | None,
        sort: str,
        limit: int,
        offset: int,
    ):
        validator = aliased(Utilisateur)
        filters = []

        if classe:
            filters.append(
                func.upper(ClassificationEntreprise.classe)
                == classe.strip().upper()
            )
        if statut:
            filters.append(
                func.upper(ClassificationEntreprise.statut)
                == statut.strip().upper()
            )
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Entreprise.identifiant_national.ilike(pattern),
                    Entreprise.raison_sociale.ilike(pattern),
                    Entreprise.nom_commercial.ilike(pattern),
                    ModeleScoring.code.ilike(pattern),
                    ModeleScoring.libelle.ilike(pattern),
                )
            )

        order_by = {
            "oldest": ClassificationEntreprise.created_at.asc(),
            "company": Entreprise.raison_sociale.asc().nullslast(),
            "score": ClassificationEntreprise.score.desc().nullslast(),
            "class": ClassificationEntreprise.classe.asc().nullslast(),
        }.get(sort, ClassificationEntreprise.created_at.desc())

        base = (
            select(
                ClassificationEntreprise,
                Entreprise.identifiant_national.label("enterprise_identifier"),
                Entreprise.raison_sociale.label("enterprise_name"),
                Entreprise.nom_commercial.label("enterprise_trade_name"),
                Entreprise.statut.label("enterprise_status"),
                ModeleScoring.code.label("model_code"),
                ModeleScoring.version.label("model_version"),
                validator.prenoms.label("validator_first_names"),
                validator.nom.label("validator_last_name"),
                validator.email.label("validator_email"),
            )
            .select_from(ClassificationEntreprise)
            .join(
                Entreprise,
                Entreprise.id == ClassificationEntreprise.entreprise_id,
            )
            .join(
                ModeleScoring,
                ModeleScoring.id == ClassificationEntreprise.modele_scoring_id,
            )
            .join(
                validator,
                validator.id == ClassificationEntreprise.valide_par_id,
            )
            .where(*filters)
        )

        result = await db.execute(
            base.order_by(order_by, ClassificationEntreprise.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        count_result = await db.execute(
            select(func.count(ClassificationEntreprise.id))
            .select_from(ClassificationEntreprise)
            .join(
                Entreprise,
                Entreprise.id == ClassificationEntreprise.entreprise_id,
            )
            .join(
                ModeleScoring,
                ModeleScoring.id == ClassificationEntreprise.modele_scoring_id,
            )
            .where(*filters)
        )

        classified_result = await db.execute(
            select(
                func.count(
                    func.distinct(ClassificationEntreprise.entreprise_id)
                )
            )
            .select_from(ClassificationEntreprise)
            .join(
                Entreprise,
                Entreprise.id == ClassificationEntreprise.entreprise_id,
            )
            .join(
                ModeleScoring,
                ModeleScoring.id == ClassificationEntreprise.modele_scoring_id,
            )
            .where(*filters)
        )

        class_result = await db.execute(
            select(
                func.count(func.distinct(ClassificationEntreprise.classe))
            )
            .select_from(ClassificationEntreprise)
            .join(
                Entreprise,
                Entreprise.id == ClassificationEntreprise.entreprise_id,
            )
            .join(
                ModeleScoring,
                ModeleScoring.id == ClassificationEntreprise.modele_scoring_id,
            )
            .where(
                *filters,
                ClassificationEntreprise.classe.is_not(None),
            )
        )

        return (
            result.all(),
            int(count_result.scalar_one() or 0),
            int(classified_result.scalar_one() or 0),
            int(class_result.scalar_one() or 0),
        )

    @staticmethod
    async def enterprises(
        db: AsyncSession,
        *,
        search: str | None,
        limit: int,
    ):
        latest = aliased(ClassificationEntreprise)
        model = aliased(ModeleScoring)

        filters = []
        if search and search.strip():
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Entreprise.identifiant_national.ilike(pattern),
                    Entreprise.raison_sociale.ilike(pattern),
                    Entreprise.nom_commercial.ilike(pattern),
                    Entreprise.activite_principale.ilike(pattern),
                )
            )

        result = await db.execute(
            select(
                Entreprise,
                latest.id.label("latest_classification_id"),
                latest.score.label("latest_score"),
                latest.classe.label("latest_class"),
                latest.date_validation.label("latest_classification_date"),
                model.code.label("latest_model_code"),
                model.version.label("latest_model_version"),
            )
            .select_from(Entreprise)
            .outerjoin(
                latest,
                latest.id == ScoringWorkspaceRepository.latest_classification_id(),
            )
            .outerjoin(model, model.id == latest.modele_scoring_id)
            .where(*filters)
            .order_by(
                Entreprise.raison_sociale.asc().nullslast(),
                Entreprise.identifiant_national.asc(),
            )
            .limit(limit)
        )

        count_result = await db.execute(
            select(func.count(Entreprise.id)).where(*filters)
        )

        return result.all(), int(count_result.scalar_one() or 0)

    @staticmethod
    def certification_base():
        return (
            select(
                Certification,
                Entreprise.raison_sociale.label("enterprise_name"),
                Entreprise.nom_commercial.label("enterprise_trade_name"),
                Entreprise.identifiant_national.label("enterprise_identifier"),
                Organisme.nom_officiel.label("organization_name"),
                Organisme.sigle.label("organization_acronym"),
                Norme.code.label("standard_code"),
                Norme.nom.label("standard_name"),
            )
            .select_from(Certification)
            .join(Entreprise, Entreprise.id == Certification.entreprise_id)
            .join(Organisme, Organisme.id == Certification.organisme_id)
            .join(Norme, Norme.id == Certification.norme_id)
        )

    @staticmethod
    def certification_search(search: str | None):
        if not search or not search.strip():
            return None

        pattern = f"%{search.strip()}%"
        return or_(
            Certification.identifiant_national.ilike(pattern),
            Certification.numero_certificat.ilike(pattern),
            Entreprise.identifiant_national.ilike(pattern),
            Entreprise.raison_sociale.ilike(pattern),
            Entreprise.nom_commercial.ilike(pattern),
            Organisme.nom_officiel.ilike(pattern),
            Organisme.sigle.ilike(pattern),
            Norme.code.ilike(pattern),
            Norme.nom.ilike(pattern),
        )

    @staticmethod
    def latest_infc_id():
        return (
            select(ResultatInfc.id)
            .where(ResultatInfc.certification_id == Certification.id)
            .order_by(
                ResultatInfc.date_calcul.desc().nullslast(),
                ResultatInfc.created_at.desc(),
            )
            .limit(1)
            .correlate(Certification)
            .scalar_subquery()
        )

    @staticmethod
    def current_sncc_id():
        return (
            select(ClassementSncc.id)
            .where(
                ClassementSncc.certification_id == Certification.id,
                ClassementSncc.date_fin.is_(None),
            )
            .order_by(
                ClassementSncc.date_effet.desc().nullslast(),
                ClassementSncc.created_at.desc(),
            )
            .limit(1)
            .correlate(Certification)
            .scalar_subquery()
        )

    @staticmethod
    async def infc_certifications(
        db: AsyncSession,
        *,
        search: str | None,
        limit: int,
    ):
        latest = aliased(ResultatInfc)
        condition = ScoringWorkspaceRepository.certification_search(search)
        filters = [condition] if condition is not None else []

        result = await db.execute(
            ScoringWorkspaceRepository.certification_base()
            .add_columns(
                latest.id.label("latest_infc_id"),
                latest.score_global.label("latest_infc_score"),
                latest.niveau.label("latest_infc_level"),
                latest.statut.label("latest_infc_status"),
                latest.date_calcul.label("latest_infc_date"),
            )
            .outerjoin(
                latest,
                latest.id == ScoringWorkspaceRepository.latest_infc_id(),
            )
            .where(*filters)
            .order_by(
                Entreprise.raison_sociale.asc().nullslast(),
                Certification.identifiant_national.asc(),
            )
            .limit(limit)
        )

        count_result = await db.execute(
            select(func.count(Certification.id))
            .select_from(Certification)
            .join(Entreprise, Entreprise.id == Certification.entreprise_id)
            .join(Organisme, Organisme.id == Certification.organisme_id)
            .join(Norme, Norme.id == Certification.norme_id)
            .where(*filters)
        )

        return result.all(), int(count_result.scalar_one() or 0)

    @staticmethod
    async def sncc_certifications(
        db: AsyncSession,
        *,
        search: str | None,
        limit: int,
    ):
        current = aliased(ClassementSncc)
        latest_infc = aliased(ResultatInfc)
        condition = ScoringWorkspaceRepository.certification_search(search)
        filters = [condition] if condition is not None else []

        result = await db.execute(
            ScoringWorkspaceRepository.certification_base()
            .add_columns(
                current.id.label("current_sncc_id"),
                current.classe.label("current_sncc_class"),
                current.statut_administratif.label("current_admin_status"),
                current.niveau_risque.label("current_risk_level"),
                current.date_effet.label("current_effective_date"),
                latest_infc.id.label("latest_infc_id"),
                latest_infc.score_global.label("latest_infc_score"),
                latest_infc.niveau.label("latest_infc_level"),
                latest_infc.statut.label("latest_infc_status"),
                latest_infc.date_calcul.label("latest_infc_date"),
            )
            .outerjoin(
                current,
                current.id == ScoringWorkspaceRepository.current_sncc_id(),
            )
            .outerjoin(
                latest_infc,
                latest_infc.id == ScoringWorkspaceRepository.latest_infc_id(),
            )
            .where(*filters)
            .order_by(
                Entreprise.raison_sociale.asc().nullslast(),
                Certification.identifiant_national.asc(),
            )
            .limit(limit)
        )

        count_result = await db.execute(
            select(func.count(Certification.id))
            .select_from(Certification)
            .join(Entreprise, Entreprise.id == Certification.entreprise_id)
            .join(Organisme, Organisme.id == Certification.organisme_id)
            .join(Norme, Norme.id == Certification.norme_id)
            .where(*filters)
        )

        return result.all(), int(count_result.scalar_one() or 0)

    @staticmethod
    async def infc_registry(
        db: AsyncSession,
        *,
        search: str | None,
        statut: str | None,
        limit: int,
        offset: int,
    ):
        filters = []
        if statut:
            filters.append(
                func.upper(ResultatInfc.statut) == statut.strip().upper()
            )
        condition = ScoringWorkspaceRepository.certification_search(search)
        if condition is not None:
            filters.append(condition)

        base = (
            select(
                ResultatInfc,
                Certification,
                Entreprise.raison_sociale.label("enterprise_name"),
                Entreprise.nom_commercial.label("enterprise_trade_name"),
                Entreprise.identifiant_national.label("enterprise_identifier"),
                Organisme.nom_officiel.label("organization_name"),
                Organisme.sigle.label("organization_acronym"),
                Norme.code.label("standard_code"),
                Norme.nom.label("standard_name"),
                ModeleScoring.code.label("model_code"),
                ModeleScoring.version.label("model_version"),
            )
            .select_from(ResultatInfc)
            .join(Certification, Certification.id == ResultatInfc.certification_id)
            .join(Entreprise, Entreprise.id == Certification.entreprise_id)
            .join(Organisme, Organisme.id == Certification.organisme_id)
            .join(Norme, Norme.id == Certification.norme_id)
            .join(ModeleScoring, ModeleScoring.id == ResultatInfc.modele_scoring_id)
            .where(*filters)
        )

        result = await db.execute(
            base.order_by(
                ResultatInfc.date_calcul.desc().nullslast(),
                ResultatInfc.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        count_base = (
            select(func.count(ResultatInfc.id))
            .select_from(ResultatInfc)
            .join(Certification, Certification.id == ResultatInfc.certification_id)
            .join(Entreprise, Entreprise.id == Certification.entreprise_id)
            .join(Organisme, Organisme.id == Certification.organisme_id)
            .join(Norme, Norme.id == Certification.norme_id)
        )
        count_result = await db.execute(count_base.where(*filters))
        calculated_result = await db.execute(
            count_base.where(*filters, func.upper(ResultatInfc.statut) == "CALCULE")
        )
        validated_result = await db.execute(
            count_base.where(*filters, func.upper(ResultatInfc.statut) == "VALIDE")
        )
        certs_result = await db.execute(
            select(func.count(func.distinct(ResultatInfc.certification_id)))
            .select_from(ResultatInfc)
            .join(Certification, Certification.id == ResultatInfc.certification_id)
            .join(Entreprise, Entreprise.id == Certification.entreprise_id)
            .join(Organisme, Organisme.id == Certification.organisme_id)
            .join(Norme, Norme.id == Certification.norme_id)
            .where(*filters)
        )

        return (
            result.all(),
            int(count_result.scalar_one() or 0),
            int(calculated_result.scalar_one() or 0),
            int(validated_result.scalar_one() or 0),
            int(certs_result.scalar_one() or 0),
        )

    @staticmethod
    async def sncc_registry(
        db: AsyncSession,
        *,
        search: str | None,
        classe: str | None,
        statut_administratif: str | None,
        niveau_risque: str | None,
        limit: int,
        offset: int,
    ):
        validator = aliased(Utilisateur)
        filters = []

        if classe:
            filters.append(
                func.upper(ClassementSncc.classe) == classe.strip().upper()
            )
        if statut_administratif:
            filters.append(
                func.upper(ClassementSncc.statut_administratif)
                == statut_administratif.strip().upper()
            )
        if niveau_risque:
            filters.append(
                func.upper(ClassementSncc.niveau_risque)
                == niveau_risque.strip().upper()
            )
        condition = ScoringWorkspaceRepository.certification_search(search)
        if condition is not None:
            filters.append(condition)

        base = (
            select(
                ClassementSncc,
                Certification,
                Entreprise.raison_sociale.label("enterprise_name"),
                Entreprise.nom_commercial.label("enterprise_trade_name"),
                Entreprise.identifiant_national.label("enterprise_identifier"),
                Organisme.nom_officiel.label("organization_name"),
                Organisme.sigle.label("organization_acronym"),
                Norme.code.label("standard_code"),
                Norme.nom.label("standard_name"),
                validator.prenoms.label("validator_first_names"),
                validator.nom.label("validator_last_name"),
                validator.email.label("validator_email"),
            )
            .select_from(ClassementSncc)
            .join(Certification, Certification.id == ClassementSncc.certification_id)
            .join(Entreprise, Entreprise.id == Certification.entreprise_id)
            .join(Organisme, Organisme.id == Certification.organisme_id)
            .join(Norme, Norme.id == Certification.norme_id)
            .join(validator, validator.id == ClassementSncc.valide_par_id)
            .where(*filters)
        )

        result = await db.execute(
            base.order_by(
                ClassementSncc.date_effet.desc().nullslast(),
                ClassementSncc.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        count_base = (
            select(func.count(ClassementSncc.id))
            .select_from(ClassementSncc)
            .join(Certification, Certification.id == ClassementSncc.certification_id)
            .join(Entreprise, Entreprise.id == Certification.entreprise_id)
            .join(Organisme, Organisme.id == Certification.organisme_id)
            .join(Norme, Norme.id == Certification.norme_id)
        )
        count_result = await db.execute(count_base.where(*filters))
        current_result = await db.execute(
            count_base.where(*filters, ClassementSncc.date_fin.is_(None))
        )
        certs_result = await db.execute(
            select(func.count(func.distinct(ClassementSncc.certification_id)))
            .select_from(ClassementSncc)
            .join(Certification, Certification.id == ClassementSncc.certification_id)
            .join(Entreprise, Entreprise.id == Certification.entreprise_id)
            .join(Organisme, Organisme.id == Certification.organisme_id)
            .join(Norme, Norme.id == Certification.norme_id)
            .where(*filters)
        )

        total = int(count_result.scalar_one() or 0)
        current = int(current_result.scalar_one() or 0)

        return (
            result.all(),
            total,
            current,
            max(total - current, 0),
            int(certs_result.scalar_one() or 0),
        )
