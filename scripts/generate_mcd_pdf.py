from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "MCD_HAUQE_CERTIF_DETAILLE.pdf"
PAGE_W, PAGE_H = landscape(A3)

GREEN = colors.HexColor("#0A6546")
DARK_GREEN = colors.HexColor("#064734")
LIGHT_GREEN = colors.HexColor("#E7F4EF")
GOLD = colors.HexColor("#C89B2C")
LIGHT_GOLD = colors.HexColor("#F8F0D9")
INK = colors.HexColor("#17211D")
MUTED = colors.HexColor("#5E6B66")
LINE = colors.HexColor("#A8BBB3")
PAPER = colors.HexColor("#FCFDFB")
WHITE = colors.white
RED = colors.HexColor("#B5473C")


def register_fonts() -> tuple[str, str]:
    candidates = [
        (
            Path(r"C:\Windows\Fonts\arial.ttf"),
            Path(r"C:\Windows\Fonts\arialbd.ttf"),
        ),
        (
            Path(r"C:\Windows\Fonts\segoeui.ttf"),
            Path(r"C:\Windows\Fonts\segoeuib.ttf"),
        ),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("HAUQE-Regular", str(regular)))
            pdfmetrics.registerFont(TTFont("HAUQE-Bold", str(bold)))
            return "HAUQE-Regular", "HAUQE-Bold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()


@dataclass(frozen=True)
class Entity:
    name: str
    attrs: tuple[str, ...]
    note: str = ""


@dataclass(frozen=True)
class Relation:
    left: str
    left_card: str
    verb: str
    right_card: str
    right: str

    def text(self) -> str:
        return f"{self.left} {self.left_card} - {self.verb} - {self.right_card} {self.right}"


@dataclass(frozen=True)
class DomainPage:
    code: str
    title: str
    subtitle: str
    entities: tuple[Entity, ...]
    relations: tuple[Relation, ...]


PAGES = (
    DomainPage(
        "D01-D02",
        "Identités, habilitations et référentiels",
        "Sécurité applicative, gouvernance des accès et nomenclatures partagées",
        (
            Entity("UTILISATEUR", ("#utilisateur", "email professionnel", "prénom, nom", "fonction, téléphone", "statut", "région d'affectation", "MFA, dernière connexion")),
            Entity("RÔLE", ("#rôle", "code", "libellé", "description", "état")),
            Entity("PERMISSION", ("#permission", "code", "domaine", "action", "description")),
            Entity("ATTRIBUTION_RÔLE", ("#attribution", "début", "fin éventuelle", "auteur", "état")),
            Entity("SESSION_UTILISATEUR", ("#session", "début", "dernière activité", "expiration", "verrouillage", "révocation")),
            Entity("ÉVÉNEMENT_SÉCURITÉ", ("#événement", "type", "date", "résultat", "gravité", "contexte, IP éventuelle")),
            Entity("RÉGION", ("#région", "code", "libellé", "état")),
            Entity("PRÉFECTURE", ("#préfecture", "code", "libellé", "état")),
            Entity("COMMUNE", ("#commune", "code", "libellé", "état")),
            Entity("LOCALITÉ", ("#localité", "code éventuel", "libellé", "état")),
            Entity("CATÉGORIE_RÉFÉRENTIEL", ("#catégorie", "code", "libellé", "description")),
            Entity("VALEUR_RÉFÉRENTIEL", ("#valeur", "code", "libellé", "parent éventuel", "ordre", "validité", "état")),
            Entity("NORME", ("#norme", "code", "nom", "version", "autorité émettrice", "période d'application", "expiration requise", "état")),
        ),
        (
            Relation("UTILISATEUR", "(0,N)", "reçoit", "(1,1)", "ATTRIBUTION_RÔLE"),
            Relation("RÔLE", "(1,1)", "est concerné par", "(0,N)", "ATTRIBUTION_RÔLE"),
            Relation("RÔLE", "(0,N)", "autorise", "(0,N)", "PERMISSION"),
            Relation("UTILISATEUR", "(1,1)", "ouvre", "(0,N)", "SESSION_UTILISATEUR"),
            Relation("UTILISATEUR", "(0,1)", "est concerné par", "(0,N)", "ÉVÉNEMENT_SÉCURITÉ"),
            Relation("RÉGION", "(1,1)", "contient", "(1,N)", "PRÉFECTURE"),
            Relation("PRÉFECTURE", "(1,1)", "contient", "(1,N)", "COMMUNE"),
            Relation("COMMUNE", "(1,1)", "contient", "(0,N)", "LOCALITÉ"),
            Relation("CATÉGORIE_RÉFÉRENTIEL", "(1,1)", "contient", "(0,N)", "VALEUR_RÉFÉRENTIEL"),
        ),
    ),
    DomainPage(
        "D03",
        "Entreprises et qualité d'identité",
        "Dossier national, implantations, activités économiques et détection des doublons",
        (
            Entity("ENTREPRISE", ("#entreprise", "identifiant national", "raison sociale", "nom commercial", "RCCM éventuel", "NIF/IFU éventuel", "forme juridique", "coordonnées", "statut, risque", "archivage")),
            Entity("VERSION_ENTREPRISE", ("#version", "numéro", "date d'effet", "motif", "valeurs figées", "auteur", "état")),
            Entity("CONTACT_ENTREPRISE", ("#contact", "nom complet", "fonction", "téléphone", "courriel", "contact principal")),
            Entity("SITE_ENTREPRISE", ("#site", "nom", "type", "adresse", "région, localité", "latitude, longitude", "état")),
            Entity("ACTIVITÉ_ENTREPRISE", ("#activité entreprise", "activité référencée", "caractère principal", "date de début", "état")),
            Entity("PRODUIT_ENTREPRISE", ("#produit entreprise", "produit référencé", "désignation déclarée", "volume annuel", "unité", "capacité", "état")),
            Entity("MARCHÉ_ENTREPRISE", ("#marché entreprise", "type de marché", "destination", "détail")),
            Entity("CANDIDAT_DOUBLON", ("#candidat", "ressource A", "ressource B", "critères concordants", "similarité", "état d'examen", "décision, motif")),
        ),
        (
            Relation("ENTREPRISE", "(1,1)", "possède", "(0,N)", "VERSION_ENTREPRISE"),
            Relation("ENTREPRISE", "(1,1)", "dispose de", "(1,N)", "CONTACT_ENTREPRISE"),
            Relation("ENTREPRISE", "(1,1)", "exploite", "(0,N)", "SITE_ENTREPRISE"),
            Relation("ENTREPRISE", "(1,1)", "exerce", "(1,N)", "ACTIVITÉ_ENTREPRISE"),
            Relation("ENTREPRISE", "(1,1)", "propose", "(0,N)", "PRODUIT_ENTREPRISE"),
            Relation("ENTREPRISE", "(1,1)", "dessert", "(0,N)", "MARCHÉ_ENTREPRISE"),
            Relation("ENTREPRISE", "(0,N)", "est rapprochée dans", "(2,2)", "CANDIDAT_DOUBLON"),
            Relation("ENTREPRISE", "(0,N)", "est localisée dans", "(1,1)", "LOCALITÉ"),
        ),
    ),
    DomainPage(
        "D04-D06",
        "Organismes, accréditations, certifications et documents",
        "Coeur du registre BNEC et conservation des preuves officielles",
        (
            Entity("ORGANISME", ("#organisme", "identifiant national", "nom officiel, sigle", "type, pays", "enregistrement", "représentation Togo", "coordonnées", "statut", "dernière vérification")),
            Entity("VERSION_ORGANISME", ("#version", "numéro", "date d'effet", "motif", "valeurs figées", "auteur")),
            Entity("ACCRÉDITATION", ("#accréditation", "numéro", "accréditeur", "domaine technique", "périmètre", "délivrance", "expiration", "statut", "référence")),
            Entity("HISTORIQUE_ACCRÉDITATION", ("#événement", "ancien statut", "nouveau statut", "date", "motif", "source", "décision HAUQE")),
            Entity("CERTIFICATION", ("#certification", "identifiant national", "numéro original", "portée", "obtention", "effet", "expiration éventuelle", "statut", "vérification", "authenticité", "stratégique")),
            Entity("VERSION_CERTIFICATION", ("#version", "numéro", "date d'effet", "motif", "valeurs figées", "auteur")),
            Entity("COUVERTURE_PRODUIT", ("#couverture produit", "produit entreprise", "détail de couverture")),
            Entity("COUVERTURE_SITE", ("#couverture site", "site entreprise", "détail de couverture")),
            Entity("AUDIT_CERTIFICATION", ("#audit", "type", "date prévue", "date réalisée", "résultat", "prochain audit", "observations")),
            Entity("ÉVÉNEMENT_CERTIFICATION", ("#événement", "type", "ancien statut", "nouveau statut", "date", "motif", "source")),
            Entity("PROCÉDURE_RENOUVELLEMENT", ("#procédure", "ouverture", "état", "date attendue", "décision", "résultat", "justification")),
            Entity("PREUVE_RENOUVELLEMENT", ("#preuve", "type", "référence", "date", "statut de vérification")),
            Entity("DOCUMENT", ("#document", "nom original", "type", "source", "auteur déclaré", "date", "confidentialité", "checksum", "statut", "archivage")),
            Entity("VERSION_DOCUMENT", ("#version", "numéro", "fichier logique", "format", "taille", "date de dépôt", "auteur", "vérification")),
            Entity("LIEN_DOCUMENTAIRE", ("#lien", "ressource métier", "rôle du document", "date d'association", "état")),
        ),
        (
            Relation("ORGANISME", "(1,1)", "possède", "(0,N)", "VERSION_ORGANISME"),
            Relation("ORGANISME", "(1,1)", "détient", "(0,N)", "ACCRÉDITATION"),
            Relation("ACCRÉDITATION", "(1,1)", "concerne", "(1,1)", "NORME"),
            Relation("ACCRÉDITATION", "(1,1)", "possède", "(1,N)", "HISTORIQUE_ACCRÉDITATION"),
            Relation("ENTREPRISE", "(1,1)", "détient", "(0,N)", "CERTIFICATION"),
            Relation("ORGANISME", "(1,1)", "délivre", "(0,N)", "CERTIFICATION"),
            Relation("CERTIFICATION", "(1,1)", "applique", "(1,1)", "NORME"),
            Relation("CERTIFICATION", "(1,1)", "possède", "(1,N)", "VERSION_CERTIFICATION"),
            Relation("CERTIFICATION", "(1,1)", "connaît", "(0,N)", "AUDIT_CERTIFICATION"),
            Relation("CERTIFICATION", "(1,1)", "engage", "(0,N)", "PROCÉDURE_RENOUVELLEMENT"),
            Relation("PROCÉDURE_RENOUVELLEMENT", "(1,1)", "comporte", "(1,N)", "PREUVE_RENOUVELLEMENT"),
            Relation("DOCUMENT", "(1,1)", "possède", "(1,N)", "VERSION_DOCUMENT"),
            Relation("DOCUMENT", "(1,1)", "est associé via", "(1,N)", "LIEN_DOCUMENTAIRE"),
        ),
    ),
    DomainPage(
        "D07",
        "Campagnes, missions et collecte",
        "Données déclarées, révisions de fiches et traçabilité de la collecte",
        (
            Entity("CAMPAGNE", ("#campagne", "code", "nom", "objet", "début, fin", "objectif", "statut")),
            Entity("MISSION_COLLECTE", ("#mission", "code", "objet", "date prévue", "début, fin", "priorité", "statut", "progression")),
            Entity("AFFECTATION_AGENT", ("#affectation", "agent", "début", "fin", "auteur", "motif", "statut")),
            Entity("FICHE_COLLECTE", ("#fiche", "version formulaire", "révision", "courante", "statut", "complétude", "consentement", "déclarant", "signature", "observations", "soumission")),
            Entity("PRODUIT_DÉCLARÉ", ("#produit déclaré", "nom", "volume", "unité", "capacité", "marchés visés")),
            Entity("CERTIFICATION_DÉCLARÉE", ("#certification déclarée", "norme", "numéro", "organisme", "portée", "dates", "statut", "copie disponible", "rapprochement officiel")),
            Entity("HISTORIQUE_COLLECTE", ("#événement", "ancien statut", "nouveau statut", "date", "acteur", "commentaire")),
        ),
        (
            Relation("CAMPAGNE", "(0,1)", "organise", "(0,N)", "MISSION_COLLECTE"),
            Relation("ENTREPRISE", "(1,1)", "est concernée par", "(0,N)", "MISSION_COLLECTE"),
            Relation("MISSION_COLLECTE", "(1,1)", "reçoit", "(1,N)", "AFFECTATION_AGENT"),
            Relation("UTILISATEUR", "(1,1)", "est désigné par", "(0,N)", "AFFECTATION_AGENT"),
            Relation("MISSION_COLLECTE", "(1,1)", "produit", "(1,N)", "FICHE_COLLECTE"),
            Relation("FICHE_COLLECTE", "(1,1)", "déclare", "(0,N)", "PRODUIT_DÉCLARÉ"),
            Relation("FICHE_COLLECTE", "(1,1)", "déclare", "(0,N)", "CERTIFICATION_DÉCLARÉE"),
            Relation("MISSION_COLLECTE", "(1,1)", "possède", "(1,N)", "HISTORIQUE_COLLECTE"),
            Relation("CERTIFICATION_DÉCLARÉE", "(0,N)", "est rapprochée de", "(0,1)", "CERTIFICATION"),
        ),
    ),
    DomainPage(
        "D08",
        "Vérification documentaire et échanges",
        "Contrôles de complétude, anomalies et confirmations externes",
        (
            Entity("DOSSIER_VÉRIFICATION", ("#dossier", "fiche source", "début", "fin", "statut", "avis", "synthèse")),
            Entity("AFFECTATION_VÉRIFICATION", ("#affectation", "vérificateur", "début", "fin", "échéance", "motif", "état")),
            Entity("POINT_VÉRIFICATION", ("#point", "code", "libellé figé", "résultat", "observation", "date", "preuve")),
            Entity("ANOMALIE_VÉRIFICATION", ("#anomalie", "catégorie", "gravité", "description", "statut", "résolution", "escalade")),
            Entity("DEMANDE_CONFIRMATION", ("#demande", "canal", "destinataire", "objet", "envoi", "réponse attendue", "statut", "pièces")),
            Entity("RÉPONSE_CONFIRMATION", ("#réponse", "date", "contenu synthétique", "document", "résultat d'exploitation")),
        ),
        (
            Relation("FICHE_COLLECTE", "(1,1)", "ouvre", "(0,N)", "DOSSIER_VÉRIFICATION"),
            Relation("DOSSIER_VÉRIFICATION", "(1,1)", "reçoit", "(1,N)", "AFFECTATION_VÉRIFICATION"),
            Relation("UTILISATEUR", "(1,1)", "est désigné par", "(0,N)", "AFFECTATION_VÉRIFICATION"),
            Relation("DOSSIER_VÉRIFICATION", "(1,1)", "comporte", "(1,N)", "POINT_VÉRIFICATION"),
            Relation("DOSSIER_VÉRIFICATION", "(1,1)", "révèle", "(0,N)", "ANOMALIE_VÉRIFICATION"),
            Relation("DOSSIER_VÉRIFICATION", "(1,1)", "génère", "(0,N)", "DEMANDE_CONFIRMATION"),
            Relation("DEMANDE_CONFIRMATION", "(1,1)", "reçoit", "(0,N)", "RÉPONSE_CONFIRMATION"),
            Relation("DEMANDE_CONFIRMATION", "(0,N)", "s'adresse à", "(0,1)", "ORGANISME"),
            Relation("DEMANDE_CONFIRMATION", "(0,N)", "s'adresse à", "(0,1)", "ENTREPRISE"),
        ),
    ),
    DomainPage(
        "D09-D10",
        "Contrôle FUCCS, validation et intégration BNEC",
        "Séparation des avis techniques, décisions hiérarchiques et opérations d'intégration",
        (
            Entity("VERSION_GRILLE_FUCCS", ("#version grille", "libellé", "période d'effet", "état de publication", "référence d'approbation")),
            Entity("RUBRIQUE_FUCCS", ("#rubrique", "code", "libellé", "ordre")),
            Entity("CRITÈRE_FUCCS", ("#critère", "code", "libellé", "description", "score maximal", "ordre", "commentaire obligatoire")),
            Entity("CONTRÔLE_FUCCS", ("#contrôle", "code", "dossier source", "contrôleur", "début, fin", "statut", "score brut", "score max", "taux", "synthèse")),
            Entity("NOTE_CRITÈRE", ("#note", "critère", "score 0-2", "commentaire", "preuve", "date", "auteur")),
            Entity("CONSTAT", ("#constat", "type", "gravité", "titre", "description", "statut")),
            Entity("VALIDATION", ("#validation", "fiche", "niveau", "validateur", "décision", "date", "réserves", "justification", "statut")),
            Entity("DEMANDE_CORRECTION", ("#correction", "motif", "instruction", "demande", "échéance", "resoumission", "statut")),
            Entity("INTÉGRATION_BNEC", ("#intégration", "validation source", "administrateur", "début, fin", "statut", "précontrôle", "post-contrôle", "sauvegarde")),
            Entity("ÉLÉMENT_INTÉGRATION", ("#élément", "type objet", "révision source", "cible officielle", "action", "code généré", "statut", "erreur")),
        ),
        (
            Relation("VERSION_GRILLE_FUCCS", "(1,1)", "contient", "(4,4)", "RUBRIQUE_FUCCS"),
            Relation("RUBRIQUE_FUCCS", "(1,1)", "regroupe", "(1,N)", "CRITÈRE_FUCCS"),
            Relation("VERSION_GRILLE_FUCCS", "(1,1)", "définit", "(28,28)", "CRITÈRE_FUCCS"),
            Relation("DOSSIER_VÉRIFICATION", "(1,1)", "autorise", "(0,N)", "CONTRÔLE_FUCCS"),
            Relation("CONTRÔLE_FUCCS", "(1,1)", "possède", "(1,N)", "NOTE_CRITÈRE"),
            Relation("CRITÈRE_FUCCS", "(1,1)", "est évalué par", "(0,N)", "NOTE_CRITÈRE"),
            Relation("CONTRÔLE_FUCCS", "(1,1)", "produit", "(0,N)", "CONSTAT"),
            Relation("FICHE_COLLECTE", "(1,1)", "reçoit", "(0,N)", "VALIDATION"),
            Relation("VALIDATION", "(1,1)", "émet", "(0,N)", "DEMANDE_CORRECTION"),
            Relation("VALIDATION", "(1,1)", "autorise", "(0,1)", "INTÉGRATION_BNEC"),
            Relation("INTÉGRATION_BNEC", "(1,1)", "traite", "(1,N)", "ÉLÉMENT_INTÉGRATION"),
        ),
    ),
    DomainPage(
        "D11",
        "Classification entreprise, INFC et SNCC",
        "Quatre mécanismes indépendants : FUCCS, classification, INFC et classement national",
        (
            Entity("MODÈLE_SCORING", ("#modèle", "code", "objet évalué", "description")),
            Entity("VERSION_MODÈLE_SCORING", ("#version", "libellé", "période d'effet", "état", "approbation", "règle de calcul figée")),
            Entity("PONDÉRATION", ("#pondération", "domaine", "valeur", "période", "état")),
            Entity("CLASSIFICATION_ENTREPRISE", ("#classification", "entreprise", "score", "classe", "date", "validation", "sources figées", "modèle/version")),
            Entity("RÉSULTAT_INFC", ("#résultat", "certification", "score /100", "niveau", "date", "validation", "sources figées", "formule/version")),
            Entity("SCORE_DOMAINE_INFC", ("#score domaine", "domaine", "valeur brute", "valeur pondérée", "complétude", "preuve synthétique")),
            Entity("CLASSEMENT_SNCC", ("#classement", "certification", "classe A+ à D", "statut administratif", "risque R1-R5", "justification", "effet", "état")),
            Entity("HISTORIQUE_CLASSEMENT", ("#événement", "anciennes valeurs", "nouvelles valeurs", "date", "auteur", "motif")),
        ),
        (
            Relation("MODÈLE_SCORING", "(1,1)", "possède", "(1,N)", "VERSION_MODÈLE_SCORING"),
            Relation("VERSION_MODÈLE_SCORING", "(1,1)", "définit", "(1,N)", "PONDÉRATION"),
            Relation("ENTREPRISE", "(1,1)", "reçoit", "(0,N)", "CLASSIFICATION_ENTREPRISE"),
            Relation("CLASSIFICATION_ENTREPRISE", "(0,N)", "utilise", "(1,1)", "VERSION_MODÈLE_SCORING"),
            Relation("CERTIFICATION", "(1,1)", "reçoit", "(0,N)", "RÉSULTAT_INFC"),
            Relation("RÉSULTAT_INFC", "(1,1)", "contient", "(6,6)", "SCORE_DOMAINE_INFC"),
            Relation("RÉSULTAT_INFC", "(0,N)", "utilise", "(1,1)", "VERSION_MODÈLE_SCORING"),
            Relation("CERTIFICATION", "(1,1)", "reçoit", "(0,N)", "CLASSEMENT_SNCC"),
            Relation("CLASSEMENT_SNCC", "(0,N)", "s'appuie sur", "(0,1)", "RÉSULTAT_INFC"),
            Relation("CLASSEMENT_SNCC", "(1,1)", "possède", "(1,N)", "HISTORIQUE_CLASSEMENT"),
        ),
    ),
    DomainPage(
        "D12",
        "Échéances, alertes, notifications et veille",
        "Moteur 180/90/30 jours/expiration et activités de la Cellule de Veille",
        (
            Entity("ÉCHÉANCE", ("#échéance", "code", "ressource", "type", "titre", "description", "date", "responsable", "priorité", "statut")),
            Entity("ALERTE", ("#alerte", "code", "type", "niveau", "titre", "message", "ressource", "détection", "prise en compte", "résolution", "statut")),
            Entity("AFFECTATION_ALERTE", ("#affectation", "responsable", "date", "échéance", "instruction", "auteur", "état")),
            Entity("HISTORIQUE_ALERTE", ("#événement", "action", "avant", "après", "commentaire", "acteur", "date")),
            Entity("RÈGLE_NOTIFICATION", ("#règle", "type alerte", "activation", "premier délai", "répétition", "expéditeur", "réponse", "version règle")),
            Entity("DESTINATAIRE_NOTIFICATION", ("#destinataire", "utilisateur éventuel", "adresse externe éventuelle", "type", "état")),
            Entity("LIVRAISON_NOTIFICATION", ("#livraison", "alerte", "canal", "destinataire", "objet", "file", "envoi", "résultat", "erreur", "tentatives")),
            Entity("DOSSIER_VEILLE", ("#dossier", "certification", "événement", "priorité", "ouverture", "responsable", "prochaine action", "statut", "clôture")),
            Entity("RELANCE", ("#relance", "dossier veille", "destinataire", "canal", "objet", "envoi", "échéance", "réponse", "résultat")),
            Entity("RAPPORT_VEILLE", ("#rapport", "type mensuel/trimestriel", "période", "statut", "préparateur", "validateur", "document")),
            Entity("INDICATEUR_VEILLE", ("#instantané", "période", "certificats suivis", "alertes à temps", "renouvellements suivis", "délai moyen", "fiabilité")),
        ),
        (
            Relation("CERTIFICATION", "(1,1)", "génère", "(0,N)", "ÉCHÉANCE"),
            Relation("ÉCHÉANCE", "(1,1)", "déclenche", "(0,N)", "ALERTE"),
            Relation("ALERTE", "(1,1)", "reçoit", "(0,N)", "AFFECTATION_ALERTE"),
            Relation("ALERTE", "(1,1)", "possède", "(1,N)", "HISTORIQUE_ALERTE"),
            Relation("RÈGLE_NOTIFICATION", "(1,1)", "désigne", "(1,N)", "DESTINATAIRE_NOTIFICATION"),
            Relation("ALERTE", "(1,1)", "produit", "(0,N)", "LIVRAISON_NOTIFICATION"),
            Relation("CERTIFICATION", "(1,1)", "ouvre", "(0,N)", "DOSSIER_VEILLE"),
            Relation("DOSSIER_VEILLE", "(1,1)", "reçoit", "(0,N)", "RELANCE"),
            Relation("UTILISATEUR", "(1,1)", "prépare", "(0,N)", "RAPPORT_VEILLE"),
        ),
    ),
    DomainPage(
        "D13",
        "Règles, qualité, décisions, publications et rapports",
        "Administration fonctionnelle, amélioration continue et diffusion contrôlée",
        (
            Entity("VERSION_RÈGLE_MÉTIER", ("#version", "libellé", "période d'effet", "état", "approbation", "motif")),
            Entity("RÈGLE_MÉTIER", ("#règle", "code RM", "famille", "libellé", "description")),
            Entity("PARAMÈTRE_RÈGLE", ("#paramètre", "clé", "valeur", "type", "date d'effet", "état")),
            Entity("REVUE_QUALITÉ", ("#revue", "période", "périmètre", "début, fin", "statut", "résultat global")),
            Entity("CONSTAT_QUALITÉ", ("#constat", "dimension", "gravité", "description", "preuve", "statut")),
            Entity("PLAN_ACTION", ("#plan", "titre", "objectif", "responsable", "échéance", "priorité", "indicateur", "cible", "progression", "statut")),
            Entity("NOTE_DÉCISION", ("#note", "période", "contexte", "constats", "risques", "options", "recommandation", "statut")),
            Entity("DÉCISION_INSTITUTIONNELLE", ("#décision", "code", "titre", "texte", "autorité", "date", "priorité", "statut")),
            Entity("DEMANDE_PUBLICATION", ("#publication", "objet", "périmètre", "confidentialité", "statut", "soumission", "retrait éventuel")),
            Entity("APPROBATION_PUBLICATION", ("#approbation", "autorité", "décision", "date", "réserve")),
            Entity("MODÈLE_RAPPORT", ("#modèle", "code", "nom", "catégorie", "formats", "configuration", "état")),
            Entity("DEMANDE_RAPPORT", ("#demande", "modèle", "demandeur", "filtres", "sections", "format", "statut", "début, fin", "résultat")),
        ),
        (
            Relation("VERSION_RÈGLE_MÉTIER", "(1,1)", "contient", "(1,N)", "RÈGLE_MÉTIER"),
            Relation("RÈGLE_MÉTIER", "(1,1)", "définit", "(0,N)", "PARAMÈTRE_RÈGLE"),
            Relation("REVUE_QUALITÉ", "(1,1)", "produit", "(0,N)", "CONSTAT_QUALITÉ"),
            Relation("CONSTAT_QUALITÉ", "(1,1)", "déclenche", "(0,N)", "PLAN_ACTION"),
            Relation("NOTE_DÉCISION", "(1,1)", "conduit à", "(0,N)", "DÉCISION_INSTITUTIONNELLE"),
            Relation("DÉCISION_INSTITUTIONNELLE", "(1,1)", "ordonne", "(0,N)", "PLAN_ACTION"),
            Relation("DEMANDE_PUBLICATION", "(1,1)", "reçoit", "(0,N)", "APPROBATION_PUBLICATION"),
            Relation("MODÈLE_RAPPORT", "(1,1)", "génère", "(0,N)", "DEMANDE_RAPPORT"),
            Relation("UTILISATEUR", "(1,1)", "initie", "(0,N)", "DEMANDE_RAPPORT"),
        ),
    ),
    DomainPage(
        "D14",
        "Audit, archivage, sauvegardes et incidents",
        "Traçabilité, conservation sur dix ans et continuité de service",
        (
            Entity("ÉVÉNEMENT_AUDIT", ("#événement", "date", "acteur éventuel", "action", "catégorie", "ressource", "résultat", "contexte, IP", "avant", "après", "empreinte")),
            Entity("ARCHIVE", ("#archive", "ressource", "date", "motif", "auteur", "durée de conservation", "état")),
            Entity("POLITIQUE_CONSERVATION", ("#politique", "catégorie de données", "durée", "base", "date d'effet", "état")),
            Entity("POLITIQUE_SAUVEGARDE", ("#politique", "fréquence", "rétention", "périmètre", "stockage logique", "état")),
            Entity("EXÉCUTION_SAUVEGARDE", ("#exécution", "politique", "début, fin", "taille", "emplacement logique", "résultat", "intégrité", "erreur")),
            Entity("TEST_RESTAURATION", ("#test", "date", "périmètre", "sauvegarde testée", "résultat", "durée", "preuve", "auteur")),
            Entity("INCIDENT", ("#incident", "code", "catégorie", "gravité", "déclaration", "description", "responsable", "statut", "résolution", "clôture")),
            Entity("ÉVÉNEMENT_INCIDENT", ("#événement", "incident", "type", "date", "acteur", "description", "preuve")),
        ),
        (
            Relation("UTILISATEUR", "(0,1)", "produit", "(0,N)", "ÉVÉNEMENT_AUDIT"),
            Relation("ARCHIVE", "(0,N)", "applique", "(1,1)", "POLITIQUE_CONSERVATION"),
            Relation("POLITIQUE_SAUVEGARDE", "(1,1)", "génère", "(0,N)", "EXÉCUTION_SAUVEGARDE"),
            Relation("EXÉCUTION_SAUVEGARDE", "(1,1)", "est évaluée par", "(0,N)", "TEST_RESTAURATION"),
            Relation("INCIDENT", "(1,1)", "possède", "(1,N)", "ÉVÉNEMENT_INCIDENT"),
            Relation("INCIDENT", "(0,N)", "peut concerner", "(0,N)", "ÉVÉNEMENT_SÉCURITÉ"),
        ),
    ),
)


SUMMARY_ENTITIES = (
    "ENTREPRISE", "SITE", "PRODUIT", "CERTIFICATION", "ORGANISME",
    "ACCRÉDITATION", "NORME", "MISSION", "FICHE COLLECTE", "VÉRIFICATION",
    "CONTRÔLE FUCCS", "VALIDATION", "INTÉGRATION BNEC",
    "CLASSIFICATION ENTREPRISE", "RÉSULTAT INFC", "CLASSEMENT SNCC",
    "ÉCHÉANCE", "ALERTE", "DOCUMENT", "UTILISATEUR",
)


def fit_text(c: canvas.Canvas, text: str, max_width: float, font: str, size: float, minimum: float = 5.4) -> float:
    while size > minimum and pdfmetrics.stringWidth(text, font, size) > max_width:
        size -= 0.2
    return size


def header(c: canvas.Canvas, title: str, subtitle: str, page_no: int, code: str = "") -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.rect(0, PAGE_H - 82, PAGE_W, 82, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, PAGE_H - 86, PAGE_W, 4, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 21)
    c.drawString(36, PAGE_H - 38, title)
    c.setFont(FONT, 9)
    c.drawString(36, PAGE_H - 59, subtitle)
    if code:
        c.setFillColor(LIGHT_GOLD)
        c.roundRect(PAGE_W - 142, PAGE_H - 60, 105, 28, 8, fill=1, stroke=0)
        c.setFillColor(DARK_GREEN)
        c.setFont(FONT_BOLD, 11)
        c.drawCentredString(PAGE_W - 89, PAGE_H - 50, code)
    c.setFillColor(MUTED)
    c.setFont(FONT, 7.5)
    c.drawString(36, 22, "HAUQE Certif - Modèle conceptuel de données - Version 0.1")
    c.drawRightString(PAGE_W - 36, 22, f"Page {page_no} / {len(PAGES) + 1}")


def draw_entity_card(
    c: canvas.Canvas,
    entity: Entity,
    x: float,
    y: float,
    width: float,
    height: float,
    compact: bool = False,
) -> None:
    c.setFillColor(WHITE)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.roundRect(x, y, width, height, 7, fill=1, stroke=1)
    header_h = 23 if compact else 27
    c.setFillColor(GREEN)
    c.roundRect(x, y + height - header_h, width, header_h, 7, fill=1, stroke=0)
    c.rect(x, y + height - header_h, width, 7, fill=1, stroke=0)
    c.setFillColor(WHITE)
    name_size = fit_text(c, entity.name, width - 14, FONT_BOLD, 9 if compact else 10)
    c.setFont(FONT_BOLD, name_size)
    c.drawCentredString(x + width / 2, y + height - header_h + 8, entity.name)

    body_top = y + height - header_h - 10
    available = height - header_h - 16
    attr_size = 6.4 if compact else 7.1
    line_h = 9 if compact else 10
    max_lines = max(1, int(available // line_h))
    attrs = entity.attrs[:max_lines]
    c.setFont(FONT, attr_size)
    for idx, attr in enumerate(attrs):
        yy = body_top - idx * line_h
        is_id = attr.startswith("#")
        c.setFillColor(DARK_GREEN if is_id else INK)
        if is_id:
            c.setFont(FONT_BOLD, attr_size)
        else:
            c.setFont(FONT, attr_size)
        label = attr if len(attr) <= 40 else attr[:38] + "…"
        c.drawString(x + 9, yy, ("ID  " if is_id else "- ") + label)


def grid_positions(count: int, top: float, bottom: float) -> tuple[int, int, float, float]:
    if count <= 8:
        cols = 4
    elif count <= 12:
        cols = 4
    else:
        cols = 5
    rows = (count + cols - 1) // cols
    usable_w = PAGE_W - 72
    gap_x = 14
    gap_y = 14
    card_w = (usable_w - gap_x * (cols - 1)) / cols
    card_h = (top - bottom - gap_y * (rows - 1)) / rows
    return cols, rows, card_w, card_h


def draw_relations_panel(c: canvas.Canvas, relations: Iterable[Relation], x: float, y: float, w: float, h: float) -> None:
    c.setFillColor(LIGHT_GOLD)
    c.setStrokeColor(GOLD)
    c.roundRect(x, y, w, h, 8, fill=1, stroke=1)
    c.setFillColor(DARK_GREEN)
    c.setFont(FONT_BOLD, 9)
    c.drawString(x + 12, y + h - 16, "Cardinalités et associations principales")
    rels = list(relations)
    cols = 2 if len(rels) > 7 else 1
    col_w = (w - 24) / cols
    per_col = (len(rels) + cols - 1) // cols
    c.setFont(FONT, 6.7)
    for idx, rel in enumerate(rels):
        col = idx // per_col
        row = idx % per_col
        tx = x + 12 + col * col_w
        ty = y + h - 31 - row * 11
        c.setFillColor(INK)
        text = rel.text()
        size = fit_text(c, text, col_w - 10, FONT, 6.7, 5.2)
        c.setFont(FONT, size)
        c.drawString(tx, ty, "- " + text)


def draw_domain_page(c: canvas.Canvas, page: DomainPage, page_no: int) -> None:
    header(c, page.title, page.subtitle, page_no, page.code)
    rel_h = 108 if len(page.relations) > 9 else 92
    rel_y = 44
    cards_bottom = rel_y + rel_h + 18
    cards_top = PAGE_H - 105
    cols, rows, card_w, card_h = grid_positions(len(page.entities), cards_top, cards_bottom)
    gap_x = 14
    gap_y = 14
    compact = len(page.entities) > 10 or card_h < 145

    for idx, entity in enumerate(page.entities):
        row = idx // cols
        col = idx % cols
        x = 36 + col * (card_w + gap_x)
        y = cards_top - (row + 1) * card_h - row * gap_y
        draw_entity_card(c, entity, x, y, card_w, card_h, compact)

    draw_relations_panel(c, page.relations, 36, rel_y, PAGE_W - 72, rel_h)
    c.showPage()


def draw_summary(c: canvas.Canvas) -> None:
    header(
        c,
        "MCD HAUQE Certif - Schéma contracté",
        "Vue synthétique des entités structurantes - le détail figure dans les planches suivantes",
        1,
        "SYNTHÈSE",
    )
    c.setFillColor(DARK_GREEN)
    c.setFont(FONT_BOLD, 12)
    c.drawString(36, PAGE_H - 116, "Cycle métier de référence")

    flow = (
        "Collecte", "Vérification", "Contrôle FUCCS", "Validation",
        "Intégration BNEC", "Classification / INFC", "SNCC", "Veille",
    )
    gap = 10
    box_w = (PAGE_W - 72 - gap * (len(flow) - 1)) / len(flow)
    y = PAGE_H - 170
    for idx, label in enumerate(flow):
        x = 36 + idx * (box_w + gap)
        c.setFillColor(GREEN if idx < 5 else GOLD)
        c.roundRect(x, y, box_w, 38, 8, fill=1, stroke=0)
        c.setFillColor(WHITE if idx < 5 else DARK_GREEN)
        size = fit_text(c, label, box_w - 10, FONT_BOLD, 8.5)
        c.setFont(FONT_BOLD, size)
        c.drawCentredString(x + box_w / 2, y + 15, label)
        if idx < len(flow) - 1:
            c.setStrokeColor(MUTED)
            c.setFillColor(MUTED)
            c.line(x + box_w, y + 19, x + box_w + gap - 2, y + 19)

    c.setFillColor(DARK_GREEN)
    c.setFont(FONT_BOLD, 12)
    c.drawString(36, PAGE_H - 205, "20 entités structurantes")

    cols = 5
    rows = 4
    gap_x = 14
    gap_y = 14
    top = PAGE_H - 225
    bottom = 145
    box_w = (PAGE_W - 72 - gap_x * (cols - 1)) / cols
    box_h = (top - bottom - gap_y * (rows - 1)) / rows
    for idx, name in enumerate(SUMMARY_ENTITIES):
        row = idx // cols
        col = idx % cols
        x = 36 + col * (box_w + gap_x)
        yy = top - (row + 1) * box_h - row * gap_y
        c.setFillColor(WHITE)
        c.setStrokeColor(LINE)
        c.roundRect(x, yy, box_w, box_h, 8, fill=1, stroke=1)
        c.setFillColor(GREEN if idx < 13 else GOLD)
        c.rect(x, yy + box_h - 7, box_w, 7, fill=1, stroke=0)
        c.setFillColor(INK)
        size = fit_text(c, name, box_w - 14, FONT_BOLD, 9.5)
        c.setFont(FONT_BOLD, size)
        c.drawCentredString(x + box_w / 2, yy + box_h / 2 - 3, name)

    c.setFillColor(LIGHT_GREEN)
    c.setStrokeColor(GREEN)
    c.roundRect(36, 48, PAGE_W - 72, 72, 10, fill=1, stroke=1)
    c.setFillColor(DARK_GREEN)
    c.setFont(FONT_BOLD, 10)
    c.drawString(50, 98, "Lecture du livrable")
    c.setFont(FONT, 8)
    lines = (
        "Cette page constitue le MCD contracté. Les dix planches suivantes détaillent les entités, attributs métier et cardinalités par domaine.",
        "Le MLD transformera ensuite les associations en relations et clés. Le MPD précisera les types PostgreSQL, contraintes et index.",
        "Les données déclarées, les données officielles BNEC, FUCCS, la classification entreprise, l'INFC et le SNCC restent séparés.",
    )
    for idx, line in enumerate(lines):
        c.drawString(50, 81 - idx * 15, "- " + line)
    c.showPage()


def build_pdf() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=landscape(A3), pageCompression=1)
    c.setTitle("MCD HAUQE Certif - Contracté et détaillé")
    c.setAuthor("Projet HAUQE Certif")
    c.setSubject("Schéma conceptuel de conception de la base nationale des entreprises certifiées")
    draw_summary(c)
    for page_no, page in enumerate(PAGES, start=2):
        draw_domain_page(c, page, page_no)
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()
