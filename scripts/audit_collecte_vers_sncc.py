"""Recette transactionnelle Collecte → SNCC.

Le script crée un dossier fictif complet puis annule la transaction finale.
Il ne doit donc laisser aucune entreprise, collecte, audit, résultat ou code
BNEC dans PostgreSQL. Il vérifie les règles et modèles actuellement publiés,
ce qui en fait un audit de la configuration réellement active.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

# Autorise l'exécution directe depuis le dossier ``scripts`` sous Windows/Linux.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import HTTPException
from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.affectation_mission import AffectationMission
from app.models.campagne import Campagne
from app.models.certification_declaree import CertificationDeclaree
from app.models.document import Document
from app.models.entreprise import Entreprise
from app.models.mission_collecte import MissionCollecte
from app.models.norme import Norme
from app.models.organisme import Organisme
from app.models.utilisateur import Utilisateur
from app.models.zone_administrative import ZoneAdministrative
from app.repositories.fuccs_repository import FuccsRepository
from app.schemas.declarations_collecte import (
    CertificationDeclareeCreateRequest,
    OffreDeclareeCreateRequest,
)
from app.schemas.fiche_collecte import FicheCollecteCreateRequest
from app.schemas.fuccs import (
    FuccsControlCreateRequest,
    FuccsFinalizeRequest,
    FuccsNoteUpsertRequest,
)
from app.schemas.validation_bnec import (
    IntegrationOpenRequest,
    IntegrationStartRequest,
    ValidationDecisionRequest,
)
from app.schemas.verification import (
    VerificationAnomalyCreateRequest,
    VerificationAnomalyResolveRequest,
    VerificationCloseRequest,
    VerificationOpenRequest,
    VerificationPointCreateRequest,
)
from app.services.automatic_scoring_service import AutomaticScoringService
from app.services.fiche_collecte_service import FicheCollecteService
from app.services.fuccs_service import FuccsService
from app.services.validation_bnec_service import ValidationBnecService
from app.services.verification_service import VerificationService


ALL_AUDIT_PERMISSIONS = [
    "COLLECTE.CREER", "COLLECTE.MODIFIER", "COLLECTE.AFFECTER",
    "VERIFICATION.OUVRIR", "VERIFICATION.VERIFIER",
    "VERIFICATION.SIGNALER_ANOMALIE", "VERIFICATION.CLOTURER",
    "FUCCS.CONTROLER", "FUCCS.FINALISER",
    "VALIDATION.REVUE_N1", "VALIDATION.DECIDER_N2",
    "INTEGRATION.OUVRIR", "INTEGRATION.EXECUTER",
    "INTEGRATION.PRECONTROLER", "INTEGRATION.POSTCONTROLER",
    "INTEGRATION.CLOTURER", "SCORING.EVALUER", "INFC.CALCULER",
    "SNCC.CALCULER",
]


def actor(user: Utilisateur) -> SimpleNamespace:
    return SimpleNamespace(user=user, permissions=ALL_AUDIT_PERMISSIONS)


REQUEST = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))


async def _flush_only(db) -> None:
    """Remplace commit pendant la recette : la transaction reste annulable."""
    await db.flush()


async def _user(db, token: str, *, ordinal: int) -> Utilisateur:
    user = await db.scalar(
        select(Utilisateur)
        .where(Utilisateur.statut == "ACTIF")
        .limit(1)
    )
    if user is not None:
        return user
    user = Utilisateur(
        email=f"audit-{ordinal}-{token}@example.invalid",
        nom="Audit",
        prenoms=f"Recette {ordinal}",
        statut="ACTIF",
    )
    db.add(user)
    await db.flush()
    return user


async def _second_user(db, token: str, first: Utilisateur) -> Utilisateur:
    user = await db.scalar(
        select(Utilisateur)
        .where(
            Utilisateur.statut == "ACTIF",
            Utilisateur.id != first.id,
        )
        .limit(1)
    )
    if user is not None:
        return user
    user = Utilisateur(
        email=f"audit-n2-{token}@example.invalid",
        nom="Audit",
        prenoms="Validation N2",
        statut="ACTIF",
    )
    db.add(user)
    await db.flush()
    return user


async def run_audit() -> dict:
    token = uuid4().hex[:10].upper()
    stages: list[dict[str, str]] = []

    async with AsyncSessionLocal() as db:
        # Les services appellent commit après chaque étape. On conserve les
        # flush nécessaires à leur fonctionnement, sans publier la recette.
        db.commit = lambda: _flush_only(db)  # type: ignore[method-assign]
        try:
            user_n1 = await _user(db, token, ordinal=1)
            user_n2 = await _second_user(db, token, user_n1)
            admin = actor(user_n1)
            validator_n2 = actor(user_n2)

            zone = await db.scalar(select(ZoneAdministrative).limit(1))
            if zone is None:
                zone = ZoneAdministrative(
                    code=f"AUD-{token}", nom="Zone audit", statut="ACTIF"
                )
                db.add(zone)
                await db.flush()

            campaign = Campagne(
                code=f"AUDIT-{token}",
                nom="Campagne fictive de recette",
                objet="Audit transactionnel du parcours SNGSC",
                objectif="Vérifier le parcours complet sans persistance",
                date_debut=date.today(),
                date_fin=date.today() + timedelta(days=7),
                responsable_id=user_n1.id,
                statut="ACTIVE",
            )
            db.add(campaign)
            await db.flush()
            mission = MissionCollecte(
                campagne_id=campaign.id,
                code=f"MIS-{token}",
                objet="Mission fictive de recette",
                zone_id=zone.id,
                date_debut_prevue=date.today(),
                date_fin_prevue=date.today() + timedelta(days=2),
                priorite="NORMALE",
                progression=0,
                statut="PLANIFIEE",
            )
            db.add(mission)
            await db.flush()
            db.add(AffectationMission(
                mission_id=mission.id,
                utilisateur_id=user_n1.id,
                role_mission="AGENT_COLLECTEUR",
                date_debut=date.today(),
                attribue_par_id=user_n1.id,
                statut="ACTIF",
            ))
            enterprise = Entreprise(
                identifiant_national=f"TMP-AUD-{token}",
                raison_sociale="Entreprise fictive Audit SNGSC",
                forme_juridique="SARL",
                nationalite="TG",
                email_principal=f"audit-{token.lower()}@example.invalid",
                telephone_principal="+22890000000",
                adresse_siege="Lomé, Togo",
                zone_siege_id=zone.id,
                activite_principale="Transformation agroalimentaire",
                statut="EN_SAISIE",
                source_donnee="AUDIT_TRANSACTIONNEL",
            )
            organisme = Organisme(
                identifiant_national=f"AUD-ORG-{token}",
                nom_officiel="Organisme certificateur fictif Audit",
                sigle="OCA",
                type_organisme="CERTIFICATEUR",
                pays="TG",
                statut="ACTIF",
            )
            norm = Norme(
                code=f"ISO-AUD-{token}",
                nom="Norme fictive de recette",
                version="2026",
                statut="ACTIVE",
            )
            db.add_all([enterprise, organisme, norm])
            await db.flush()
            stages.append({"etape": "Préparation", "resultat": "OK"})

            fiche = await FicheCollecteService.create(
                db,
                mission_id=mission.id,
                payload=FicheCollecteCreateRequest(
                    entreprise_id=enterprise.id,
                    version_formulaire="AUDIT-RECETTE-V1",
                    consentement_obtenu=True,
                    nom_declarant="Déclarant fictif",
                    fonction_declarant="Responsable qualité",
                    telephone_declarant="+22891111111",
                    email_declarant="declarant.audit@example.invalid",
                    signature_declarant="Signature fictive",
                    observations="Données fictives, transaction annulée après audit.",
                ),
                actor=admin,
                request=REQUEST,
            )
            db.add(
                Document(
                    ressource_type="FICHE_COLLECTE",
                    ressource_id=fiche.id,
                    type_document="JUSTIFICATIF_COLLECTE",
                    nom_original="justificatif-audit-fictif.pdf",
                    nom_stockage=f"justificatif-audit-{token}.pdf",
                    chemin_stockage=f"audit/{token}/justificatif.pdf",
                    format="application/pdf",
                    taille_octets=1024,
                    source="AUDIT_TRANSACTIONNEL",
                    depose_par_id=user_n1.id,
                    date_document=date.today(),
                    statut="ACTIF",
                )
            )
            await db.flush()
            offer = await FicheCollecteService.create_offre(
                db,
                mission_id=mission.id,
                fiche_id=fiche.id,
                payload=OffreDeclareeCreateRequest(
                    type_offre="PRODUIT",
                    nom="Produit fictif de recette",
                    description="Produit créé uniquement pour vérifier le parcours.",
                    categorie="ALIMENTAIRE",
                    volume=Decimal("120"),
                    unite="kg",
                    capacite=Decimal("500"),
                    marches_vises="Togo, Région CEDEAO",
                ),
                actor=admin,
                request=REQUEST,
            )
            declared = await FicheCollecteService.create_certification(
                db,
                mission_id=mission.id,
                fiche_id=fiche.id,
                payload=CertificationDeclareeCreateRequest(
                    nom_certification="Certification fictive de recette",
                    numero=f"CERT-AUD-{token}",
                    organisme_declare=organisme.nom_officiel,
                    organisme_id=organisme.id,
                    norme_declaree=norm.code,
                    portee="Transformation et conditionnement",
                    date_obtention=date.today() - timedelta(days=30),
                    date_expiration=date.today() + timedelta(days=365),
                    copie_disponible=True,
                    situation_declaree="PRESENTE",
                ),
                actor=admin,
                request=REQUEST,
            )
            fiche = await FicheCollecteService.submit(
                db,
                mission_id=mission.id,
                fiche_id=fiche.id,
                commentaire="Soumission fictive de recette.",
                actor=admin,
                request=REQUEST,
            )
            assert fiche.statut == "SOUMISE"
            assert fiche.taux_completude == Decimal("100")
            stages.append({"etape": "Collecte et complétude", "resultat": "OK"})

            dossier = await VerificationService.open_from_fiche(
                db,
                fiche_id=fiche.id,
                payload=VerificationOpenRequest(priorite="NORMALE", niveau_risque="R2"),
                actor=admin,
                request=REQUEST,
            )
            point = await VerificationService.save_point(
                db,
                dossier_id=dossier.id,
                payload=VerificationPointCreateRequest(
                    libelle="Authenticité et dates contrôlées",
                    categorie="CERTIFICATION",
                    resultat="CONFORME",
                    observation="Document fictif cohérent.",
                ),
                actor=admin,
                request=REQUEST,
            )
            anomaly = await VerificationService.create_anomaly(
                db,
                dossier_id=dossier.id,
                payload=VerificationAnomalyCreateRequest(
                    point_verification_id=point.id,
                    categorie="FORME",
                    gravite="MINEURE",
                    description="Observation fictive à résoudre pour vérifier la clôture.",
                ),
                actor=admin,
                request=REQUEST,
            )
            anomaly = await VerificationService.resolve_anomaly(
                db,
                dossier_id=dossier.id,
                anomaly_id=anomaly.id,
                payload=VerificationAnomalyResolveRequest(
                    resolution="Observation fictive corrigée et contrôlée.",
                ),
                actor=admin,
                request=REQUEST,
            )
            assert anomaly.statut == "RESOLUE"
            dossier = await VerificationService.close(
                db,
                dossier_id=dossier.id,
                payload=VerificationCloseRequest(
                    avis="verified_compliant",
                    synthese="Vérification fictive favorable.",
                    niveau_risque="R2",
                ),
                actor=admin,
                request=REQUEST,
            )
            assert dossier.statut == "TERMINE"
            stages.append({"etape": "Vérification et anomalie", "resultat": "OK"})

            control = await FuccsService.create_control(
                db,
                dossier_id=dossier.id,
                payload=FuccsControlCreateRequest(),
                actor=admin,
                request=REQUEST,
            )
            proof = Document(
                type_document="PREUVE_AUDIT",
                nom_original="preuve-fictive.txt",
                nom_stockage=f"audit-{token}.txt",
                format="text/plain",
                taille_octets=1,
                ressource_type="FICHE_COLLECTE",
                ressource_id=fiche.id,
                confidentialite="INTERNE",
                source="AUDIT_TRANSACTIONNEL",
                depose_par_id=user_n1.id,
                date_document=date.today(),
                statut="ACTIF",
            )
            db.add(proof)
            await db.flush()
            criteria = await FuccsRepository.list_criteria_for_grid(
                db, control.grille_fuccs_id
            )
            assert criteria, "La grille FUCCS publiée ne contient aucun critère."
            for criterion in criteria:
                await FuccsService.upsert_note(
                    db,
                    control_id=control.id,
                    criterion_id=criterion.id,
                    payload=FuccsNoteUpsertRequest(
                        score=Decimal(str(criterion.score_maximal)),
                        commentaire="Note fictive de recette.",
                        preuve_document_id=proof.id if criterion.preuve_obligatoire else None,
                    ),
                    actor=admin,
                    request=REQUEST,
                )
            control = await FuccsService.finalize(
                db,
                control_id=control.id,
                payload=FuccsFinalizeRequest(synthese="FUCCS fictif finalisé."),
                actor=admin,
                request=REQUEST,
            )
            assert control.statut == "FINALISE"
            stages.append({"etape": "Contrôle FUCCS", "resultat": "OK"})

            validation_n1 = await ValidationBnecService.create_level_decision(
                db,
                fiche_id=fiche.id,
                level="NIVEAU_1",
                payload=ValidationDecisionRequest(
                    decision="VALIDE", justification="Revue N1 fictive favorable."
                ),
                actor=admin,
                request=REQUEST,
            )
            validation_n2 = await ValidationBnecService.create_level_decision(
                db,
                fiche_id=fiche.id,
                level="NIVEAU_2",
                payload=ValidationDecisionRequest(
                    decision="VALIDE", justification="Validation N2 fictive favorable."
                ),
                actor=validator_n2,
                request=REQUEST,
            )
            assert validation_n1.decision == validation_n2.decision == "VALIDE"
            stages.append({"etape": "Validations N1 et N2 distinctes", "resultat": "OK"})

            integration = await ValidationBnecService.open_integration(
                db,
                validation_id=validation_n2.id,
                payload=IntegrationOpenRequest(resume="Intégration fictive de recette."),
                actor=admin,
                request=REQUEST,
            )
            integration = await ValidationBnecService.start(
                db,
                integration_id=integration.id,
                payload=IntegrationStartRequest(resume="Exécution fictive intégrale."),
                actor=admin,
                request=REQUEST,
            )
            assert integration.statut == "INTEGREE"
            declared_orm = await db.get(CertificationDeclaree, declared.id)
            assert declared_orm is not None
            assert declared_orm.certification_officielle_id is not None
            stages.append({"etape": "Intégration BNEC et codification", "resultat": "OK"})

            scoring = await AutomaticScoringService.evaluate_enterprise(
                db, enterprise_id=enterprise.id, actor=admin, request=REQUEST
            )
            infc = await AutomaticScoringService.calculate_infc(
                db,
                certification_id=declared_orm.certification_officielle_id,
                actor=admin,
                request=REQUEST,
            )
            sncc = await AutomaticScoringService.classify_sncc(
                db,
                certification_id=declared_orm.certification_officielle_id,
                actor=admin,
                request=REQUEST,
            )
            assert scoring.execute and infc.execute and sncc.execute
            stages.append({"etape": "Scoring, INFC et SNCC automatiques", "resultat": "OK"})

            return {"statut": "SUCCES", "token": token, "etapes": stages}
        except HTTPException as exc:
            return {
                "statut": "ECHEC_METIER",
                "token": token,
                "etapes": stages,
                "detail": str(exc.detail),
            }
        except Exception as exc:
            return {
                "statut": "ECHEC_TECHNIQUE",
                "token": token,
                "etapes": stages,
                "detail": str(exc),
            }
        finally:
            await db.rollback()


def main() -> None:
    if sys.platform == "win32":
        result = asyncio.run(
            run_audit(),
            loop_factory=asyncio.SelectorEventLoop,
        )
    else:
        result = asyncio.run(run_audit())
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if result["statut"] != "SUCCES":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
