from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PDM = ROOT / "output" / "Livrable v01" / "MPD_HAUQE_CERTIF_V01.pdm"
OUTPUT = ROOT / "MATRICE_PASSAGE_MPD_VERS_MCD.md"


CLASSIFICATION = {
    "utilisateurs": ("ENTITÉ", "Utilisateur", "Conserver les attributs métier, masquer les champs d’audit."),
    "roles": ("ENTITÉ", "Rôle", "Conserver."),
    "permissions": ("ENTITÉ", "Permission", "Conserver dans le MCD détaillé."),
    "utilisateur_role": ("ASSOCIATION", "Attribuer un rôle", "Transformer la table de liaison en association porteuse de dates et motif."),
    "role_permission": ("ASSOCIATION", "Autoriser", "Transformer en association Rôle–Permission."),
    "sessions_utilisateur": ("TECHNIQUE", "—", "Masquer du MCD ; conserver uniquement dans le MPD."),
    "zones_administratives": ("ENTITÉ", "Zone administrative", "Conserver la hiérarchie récursive."),
    "referentiels": ("ENTITÉ", "Référentiel", "Conserver dans le MCD détaillé."),
    "valeurs_referentiel": ("ENTITÉ", "Valeur de référentiel", "Conserver et relier au référentiel."),
    "normes": ("ENTITÉ", "Norme", "Conserver."),
    "entreprises": ("ENTITÉ", "Entreprise", "Entité centrale."),
    "contacts_entreprise": ("ENTITÉ", "Contact d’entreprise", "Conserver, cardinalité multiple."),
    "sites_entreprise": ("ENTITÉ", "Site d’entreprise", "Conserver, cardinalité multiple."),
    "offres_entreprise": ("ENTITÉ", "Offre d’entreprise", "Produit ou service proposé."),
    "candidats_doublon": ("FUSION", "Contrôle de doublon", "Présenter comme résultat de contrôle, pas comme entité centrale."),
    "organismes": ("ENTITÉ", "Organisme", "Conserver."),
    "accreditations": ("ENTITÉ", "Accréditation", "Conserver."),
    "certifications": ("ENTITÉ", "Certification", "Entité centrale."),
    "couvertures_certification": ("ASSOCIATION", "Couvrir", "Association porteuse entre Certification et Offre/Site."),
    "audits_certification": ("ENTITÉ", "Audit de certification", "Conserver."),
    "evenements_certification": ("HISTORIQUE", "Historique de certification", "Masquer du contracté ; conserver comme historique dans le détaillé."),
    "renouvellements_certification": ("ENTITÉ", "Renouvellement", "Conserver."),
    "documents": ("ENTITÉ", "Document", "Conserver comme preuve documentaire transverse."),
    "campagnes": ("ENTITÉ", "Campagne", "Conserver."),
    "missions_collecte": ("ENTITÉ", "Mission de collecte", "Conserver."),
    "affectations_mission": ("ASSOCIATION", "Affecter à une mission", "Association Utilisateur–Mission avec dates et rôle."),
    "fiches_collecte": ("ENTITÉ", "Fiche de collecte", "Conserver."),
    "offres_declarees": ("ENTITÉ", "Offre déclarée", "Séparer des données officielles."),
    "certifications_declarees": ("ENTITÉ", "Certification déclarée", "Séparer des certifications officielles."),
    "evenements_collecte": ("HISTORIQUE", "Historique de collecte", "Masquer du contracté ; conserver dans le détaillé."),
    "dossiers_verification": ("ENTITÉ", "Dossier de vérification", "Conserver."),
    "affectations_verification": ("ASSOCIATION", "Affecter à la vérification", "Association Utilisateur–Dossier."),
    "points_verification": ("ENTITÉ", "Point de vérification", "Conserver."),
    "anomalies_verification": ("ENTITÉ", "Anomalie de vérification", "Conserver."),
    "confirmations_externes": ("ENTITÉ", "Confirmation externe", "Conserver."),
    "grilles_fuccs": ("ENTITÉ", "Grille FUCCS", "Conserver."),
    "rubriques_fuccs": ("ENTITÉ", "Rubrique FUCCS", "Conserver."),
    "criteres_fuccs": ("ENTITÉ", "Critère FUCCS", "Conserver."),
    "controles_fuccs": ("ENTITÉ", "Contrôle FUCCS", "Conserver."),
    "notes_criteres": ("ASSOCIATION", "Évaluer un critère", "Association Contrôle–Critère porteuse du score et de la preuve."),
    "constats_controle": ("ENTITÉ", "Constat de contrôle", "Conserver."),
    "validations": ("ENTITÉ", "Validation", "Conserver."),
    "corrections": ("ENTITÉ", "Correction", "Conserver."),
    "integrations_bnec": ("ENTITÉ", "Intégration BNEC", "Conserver."),
    "elements_integration": ("FUSION", "Élément intégré", "Présenter comme détail de l’intégration, pas dans le contracté."),
    "modeles_scoring": ("ENTITÉ", "Modèle de scoring", "Conserver."),
    "ponderations_scoring": ("ASSOCIATION", "Pondérer un domaine", "Association porteuse rattachée au modèle de scoring."),
    "classifications_entreprise": ("ENTITÉ", "Classification d’entreprise", "Conserver."),
    "resultats_infc": ("ENTITÉ", "Résultat INFC", "Conserver."),
    "classements_sncc": ("ENTITÉ", "Classement SNCC", "Conserver."),
    "echeances": ("ENTITÉ", "Échéance", "Conserver dans le détaillé."),
    "alertes": ("ENTITÉ", "Alerte", "Conserver."),
    "notifications": ("ENTITÉ", "Notification", "Conserver dans le détaillé."),
    "dossiers_veille": ("ENTITÉ", "Dossier de veille", "Conserver."),
    "relances_veille": ("ENTITÉ", "Relance de veille", "Conserver."),
    "rapports_veille": ("ENTITÉ", "Rapport de veille", "Conserver."),
    "regles_metier": ("ENTITÉ", "Règle métier", "Conserver dans le détaillé."),
    "revues_qualite": ("ENTITÉ", "Revue qualité", "Conserver."),
    "plans_action": ("ENTITÉ", "Plan d’action", "Conserver."),
    "decisions_institutionnelles": ("ENTITÉ", "Décision institutionnelle", "Conserver."),
    "publications": ("ENTITÉ", "Publication", "Conserver dans le détaillé."),
    "rapports_generes": ("FUSION", "Rapport généré", "Présenter comme document produit, fusion conceptuelle avec Document."),
    "evenements_audit": ("TECHNIQUE", "—", "Masquer du MCD ; documenter dans les règles d’audit."),
    "archives": ("TECHNIQUE", "—", "Masquer du contracté ; conserver dans le MPD et l’architecture technique."),
    "sauvegardes": ("TECHNIQUE", "—", "Masquer du MCD métier ; conserver dans le MPD."),
    "incidents": ("ENTITÉ", "Incident", "Conserver dans le MCD détaillé."),
}


def parse_tables() -> list[tuple[str, int]]:
    text = PDM.read_text(encoding="utf-8")
    starts = list(re.finditer(r'<o:Table Id="[^"]+">', text))
    result = []
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[match.start():end]
        name_match = re.search(r"<a:Name>([^<]+)</a:Name>", block)
        if not name_match:
            continue
        result.append((name_match.group(1), len(re.findall(r'<o:Column Id="', block))))
    return result


def build() -> None:
    tables = parse_tables()
    missing = [name for name, _ in tables if name not in CLASSIFICATION]
    if missing:
        raise ValueError(f"Tables non classées : {missing}")

    counts: dict[str, int] = {}
    lines = [
        "# Matrice de passage du MPD vers le MCD — HAUQE Certif",
        "",
        f"**Source contrôlée :** `{PDM.relative_to(ROOT)}`  ",
        f"**Tables MPD :** {len(tables)}  ",
        "**Objectif :** transformer le modèle physique en modèle conceptuel lisible pour le livrable contractuel.",
        "",
        "| N° | Table du MPD | Colonnes | Traitement MCD | Objet conceptuel cible | Décision |",
        "|---:|---|---:|---|---|---|",
    ]
    for number, (name, columns) in enumerate(tables, start=1):
        treatment, target, decision = CLASSIFICATION[name]
        counts[treatment] = counts.get(treatment, 0) + 1
        lines.append(f"| {number} | `{name}` | {columns} | {treatment} | {target} | {decision} |")

    lines.extend([
        "",
        "## Synthèse",
        "",
        f"- Entités conceptuelles conservées : **{counts.get('ENTITÉ', 0)}**",
        f"- Tables transformées en associations : **{counts.get('ASSOCIATION', 0)}**",
        f"- Historiques conservés seulement dans le MCD détaillé : **{counts.get('HISTORIQUE', 0)}**",
        f"- Objets fusionnés ou absorbés : **{counts.get('FUSION', 0)}**",
        f"- Objets purement techniques masqués : **{counts.get('TECHNIQUE', 0)}**",
        "",
        "## Règles de nettoyage du CDM",
        "",
        "1. retirer `created_at`, `updated_at`, UUID, index, triggers et noms de contraintes ;",
        "2. ne pas afficher les clés étrangères lorsqu’une association les représente ;",
        "3. conserver les identifiants métier et les attributs compréhensibles par la HAUQE/GFA ;",
        "4. remplacer les noms techniques par des noms métier au singulier ;",
        "5. nommer chaque association avec un verbe ;",
        "6. vérifier toutes les cardinalités minimales et maximales ;",
        "7. produire un diagramme contracté et des diagrammes détaillés par domaine.",
        "",
    ])
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"tables={len(tables)} counts={counts}")
    print(OUTPUT)


if __name__ == "__main__":
    build()
