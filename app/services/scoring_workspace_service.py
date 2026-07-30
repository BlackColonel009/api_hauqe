from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classification_entreprise import ClassificationEntreprise
from app.models.resultat_infc import ResultatInfc
from app.models.classement_sncc import ClassementSncc
from app.repositories.scoring_workspace_repository import ScoringWorkspaceRepository
from app.rules.sncc_reference import (
    SNCC_ADMIN_STATUSES,
    SNCC_CLASSES,
    SNCC_RISK_LEVELS,
)
from app.schemas.scoring_workspace import (
    CertificationInfcWorkspaceItem,
    CertificationInfcWorkspaceResponse,
    CertificationSnccWorkspaceItem,
    CertificationSnccWorkspaceResponse,
    ClassificationWorkspaceFilters,
    ClassificationWorkspaceItem,
    ClassificationWorkspaceResponse,
    ClassificationWorkspaceSummary,
    EnterpriseScoringWorkspaceItem,
    EnterpriseScoringWorkspaceResponse,
    InfcWorkspaceFilters,
    InfcWorkspaceItem,
    InfcWorkspaceResponse,
    InfcWorkspaceSummary,
    ScoringWorkspaceFilters,
    SnccWorkspaceFilters,
    SnccWorkspaceItem,
    SnccWorkspaceResponse,
    SnccWorkspaceSummary,
)


class ScoringWorkspaceService:
    @staticmethod
    def user_name(first_names, last_name, email):
        name = " ".join(
            part for part in (first_names, last_name) if part
        ).strip()
        return name or email

    @staticmethod
    def organization_name(name, acronym):
        if name and acronym:
            return f"{name} ({acronym})"
        return name or acronym

    @staticmethod
    def certification_common(row, certification):
        return {
            "certification_id": certification.id,
            "certification_identifier": certification.identifiant_national,
            "certificate_number": certification.numero_certificat,
            "certification_status": certification.statut,
            "expiry_date": certification.date_expiration,
            "enterprise_id": certification.entreprise_id,
            "enterprise_name": row.enterprise_name or row.enterprise_trade_name,
            "enterprise_identifier": row.enterprise_identifier,
            "organization_name": ScoringWorkspaceService.organization_name(
                row.organization_name,
                row.organization_acronym,
            ),
            "standard_code": row.standard_code,
            "standard_name": row.standard_name,
        }

    @staticmethod
    async def filters(db: AsyncSession) -> ScoringWorkspaceFilters:
        return ScoringWorkspaceFilters(
            classification_classes=(
                await ScoringWorkspaceRepository.distinct_values(
                    db, ClassificationEntreprise.classe
                )
            ),
            classification_statuses=(
                await ScoringWorkspaceRepository.distinct_values(
                    db, ClassificationEntreprise.statut
                )
            ),
            infc_statuses=(
                await ScoringWorkspaceRepository.distinct_values(
                    db, ResultatInfc.statut
                )
            ),
            sncc_classes=(
                await ScoringWorkspaceRepository.distinct_values(
                    db, ClassementSncc.classe
                )
            ),
            sncc_admin_statuses=(
                await ScoringWorkspaceRepository.distinct_values(
                    db, ClassementSncc.statut_administratif
                )
            ),
            sncc_risk_levels=(
                await ScoringWorkspaceRepository.distinct_values(
                    db, ClassementSncc.niveau_risque
                )
            ),
        )

    @staticmethod
    async def classification_filters(db: AsyncSession) -> ClassificationWorkspaceFilters:
        return ClassificationWorkspaceFilters(
            classes=await ScoringWorkspaceRepository.distinct_values(
                db, ClassificationEntreprise.classe
            ),
            statuses=await ScoringWorkspaceRepository.distinct_values(
                db, ClassificationEntreprise.statut
            ),
        )

    @staticmethod
    async def infc_filters(db: AsyncSession) -> InfcWorkspaceFilters:
        return InfcWorkspaceFilters(
            statuses=await ScoringWorkspaceRepository.distinct_values(
                db, ResultatInfc.statut
            )
        )

    @staticmethod
    async def sncc_filters(db: AsyncSession) -> SnccWorkspaceFilters:
        return SnccWorkspaceFilters(
            classes=list(SNCC_CLASSES),
            admin_statuses=list(SNCC_ADMIN_STATUSES),
            risk_levels=list(SNCC_RISK_LEVELS),
        )

    @staticmethod
    async def classifications(
        db: AsyncSession,
        *,
        search,
        classe,
        statut,
        sort,
        limit,
        offset,
    ) -> ClassificationWorkspaceResponse:
        rows, total, classified, classes = (
            await ScoringWorkspaceRepository.classification_registry(
                db,
                search=search,
                classe=classe,
                statut=statut,
                sort=sort,
                limit=limit,
                offset=offset,
            )
        )

        items = []
        for row in rows:
            item = row[0]
            items.append(
                ClassificationWorkspaceItem(
                    id=item.id,
                    enterprise_id=item.entreprise_id,
                    enterprise_name=row.enterprise_name or row.enterprise_trade_name,
                    enterprise_identifier=row.enterprise_identifier,
                    enterprise_status=row.enterprise_status,
                    score=item.score,
                    class_code=item.classe,
                    calculated_on=item.date_calcul,
                    validated_on=item.date_validation,
                    status=item.statut,
                    model_id=item.modele_scoring_id,
                    model_code=row.model_code,
                    model_version=row.model_version,
                    validator_id=item.valide_par_id,
                    validator_name=ScoringWorkspaceService.user_name(
                        row.validator_first_names,
                        row.validator_last_name,
                        row.validator_email,
                    ),
                )
            )

        return ClassificationWorkspaceResponse(
            total=total,
            limit=limit,
            offset=offset,
            summary=ClassificationWorkspaceSummary(
                total=total,
                enterprises_classified=classified,
                distinct_classes=classes,
            ),
            items=items,
        )

    @staticmethod
    async def enterprises(
        db: AsyncSession,
        *,
        search,
        limit,
    ) -> EnterpriseScoringWorkspaceResponse:
        rows, total = await ScoringWorkspaceRepository.enterprises(
            db,
            search=search,
            limit=limit,
        )

        return EnterpriseScoringWorkspaceResponse(
            total=total,
            items=[
                EnterpriseScoringWorkspaceItem(
                    enterprise_id=row[0].id,
                    enterprise_name=row[0].raison_sociale or row[0].nom_commercial,
                    enterprise_identifier=row[0].identifiant_national,
                    enterprise_status=row[0].statut,
                    activity=row[0].activite_principale,
                    latest_classification_id=row.latest_classification_id,
                    latest_score=row.latest_score,
                    latest_class=row.latest_class,
                    latest_classification_date=row.latest_classification_date,
                    latest_model_code=row.latest_model_code,
                    latest_model_version=row.latest_model_version,
                )
                for row in rows
            ],
        )

    @staticmethod
    async def infc_certifications(
        db: AsyncSession,
        *,
        search,
        limit,
    ) -> CertificationInfcWorkspaceResponse:
        rows, total = await ScoringWorkspaceRepository.infc_certifications(
            db,
            search=search,
            limit=limit,
        )
        items = []
        for row in rows:
            certification = row[0]
            common = ScoringWorkspaceService.certification_common(row, certification)
            items.append(
                CertificationInfcWorkspaceItem(
                    **common,
                    latest_infc_id=row.latest_infc_id,
                    latest_infc_score=row.latest_infc_score,
                    latest_infc_level=row.latest_infc_level,
                    latest_infc_status=row.latest_infc_status,
                    latest_infc_date=row.latest_infc_date,
                )
            )
        return CertificationInfcWorkspaceResponse(total=total, items=items)

    @staticmethod
    async def sncc_certifications(
        db: AsyncSession,
        *,
        search,
        limit,
    ) -> CertificationSnccWorkspaceResponse:
        rows, total = await ScoringWorkspaceRepository.sncc_certifications(
            db,
            search=search,
            limit=limit,
        )
        items = []
        for row in rows:
            certification = row[0]
            common = ScoringWorkspaceService.certification_common(row, certification)
            items.append(
                CertificationSnccWorkspaceItem(
                    **common,
                    eligible=(
                        str(row.latest_infc_status or "").upper() == "VALIDE"
                        and str(certification.statut or "").upper() != "ARCHIVE"
                    ),
                    eligibility_reasons=(
                        []
                        if (
                            str(row.latest_infc_status or "").upper() == "VALIDE"
                            and str(certification.statut or "").upper() != "ARCHIVE"
                        )
                        else [
                            *(
                                []
                                if str(certification.statut or "").upper() != "ARCHIVE"
                                else ["Certification archivée"]
                            ),
                            *(
                                []
                                if str(row.latest_infc_status or "").upper() == "VALIDE"
                                else ["Résultat INFC validé requis"]
                            ),
                        ]
                    ),
                    latest_infc_id=row.latest_infc_id,
                    latest_infc_score=row.latest_infc_score,
                    latest_infc_level=row.latest_infc_level,
                    latest_infc_status=row.latest_infc_status,
                    latest_infc_date=row.latest_infc_date,
                    current_sncc_id=row.current_sncc_id,
                    current_sncc_class=row.current_sncc_class,
                    current_admin_status=row.current_admin_status,
                    current_risk_level=row.current_risk_level,
                    current_effective_date=row.current_effective_date,
                )
            )
        return CertificationSnccWorkspaceResponse(total=total, items=items)

    @staticmethod
    async def infc_results(
        db: AsyncSession,
        *,
        search,
        statut,
        limit,
        offset,
    ) -> InfcWorkspaceResponse:
        rows, total, calculated, validated, certifications = (
            await ScoringWorkspaceRepository.infc_registry(
                db,
                search=search,
                statut=statut,
                limit=limit,
                offset=offset,
            )
        )

        items = []
        for row in rows:
            result = row[0]
            certification = row[1]
            common = ScoringWorkspaceService.certification_common(row, certification)
            items.append(
                InfcWorkspaceItem(
                    **common,
                    result_id=result.id,
                    model_id=result.modele_scoring_id,
                    model_code=row.model_code,
                    model_version=row.model_version,
                    score_global=result.score_global,
                    level=result.niveau,
                    calculated_on=result.date_calcul,
                    validated_on=result.date_validation,
                    status=result.statut,
                    domain_scores=result.scores_domaines,
                )
            )

        return InfcWorkspaceResponse(
            total=total,
            limit=limit,
            offset=offset,
            summary=InfcWorkspaceSummary(
                total=total,
                calculated=calculated,
                validated=validated,
                certifications_evaluated=certifications,
            ),
            items=items,
        )

    @staticmethod
    async def sncc_results(
        db: AsyncSession,
        *,
        search,
        classe,
        statut_administratif,
        niveau_risque,
        limit,
        offset,
    ) -> SnccWorkspaceResponse:
        rows, total, current, closed, certifications = (
            await ScoringWorkspaceRepository.sncc_registry(
                db,
                search=search,
                classe=classe,
                statut_administratif=statut_administratif,
                niveau_risque=niveau_risque,
                limit=limit,
                offset=offset,
            )
        )

        items = []
        for row in rows:
            item = row[0]
            certification = row[1]
            common = ScoringWorkspaceService.certification_common(row, certification)
            items.append(
                SnccWorkspaceItem(
                    **common,
                    sncc_id=item.id,
                    class_code=item.classe,
                    administrative_status=item.statut_administratif,
                    risk_level=item.niveau_risque,
                    justification=item.justification,
                    effective_on=item.date_effet,
                    ended_on=item.date_fin,
                    validated_by_id=item.valide_par_id,
                    validator_name=ScoringWorkspaceService.user_name(
                        row.validator_first_names,
                        row.validator_last_name,
                        row.validator_email,
                    ),
                    status=item.statut,
                )
            )

        return SnccWorkspaceResponse(
            total=total,
            limit=limit,
            offset=offset,
            summary=SnccWorkspaceSummary(
                total=total,
                current=current,
                closed=closed,
                certifications_ranked=certifications,
            ),
            items=items,
        )
