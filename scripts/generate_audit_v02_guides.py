from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
GREEN, PALE = HexColor("#287E5F"), HexColor("#EDF7F2")
INK, MUTED, LINE = HexColor("#18352B"), HexColor("#60756D"), HexColor("#DCE9E3")

GUIDES = [
    {
        "slug": "referentiels", "title": "Référentiels et nomenclatures", "subtitle": "Administrer les listes communes de la plateforme",
        "columns": ("Catégories", "Valeurs du référentiel", "Dépendances et export"),
        "steps": [("Initialiser", "Utilisez Référentiel type pour ajouter uniquement les listes HAUQE encore absentes."), ("Créer", "Le code proposé est unique et modifiable avant l'enregistrement."), ("Compléter", "Sélectionnez une catégorie puis créez, modifiez ou désactivez ses valeurs."), ("Contrôler", "Vérifiez les dépendances avant de changer un code déjà utilisé.")],
        "note": "L'initialisation ne remplace aucune donnée existante. Toutes les propositions restent modifiables et chaque action est auditée.",
    },
    {
        "slug": "verifications",
        "title": "Vérification documentaire",
        "subtitle": "De la fiche soumise à l'avis de vérification",
        "columns": ("Dossiers et filtres", "Fiche et affectation", "Contrôles et avis"),
        "steps": [
            ("Ouvrir", "Choisissez une fiche soumise. Une fiche ne peut avoir qu'un dossier ouvert."),
            ("Affecter", "Désignez le vérificateur et, si nécessaire, renseignez début, fin et échéance."),
            ("Contrôler", "Examinez les documents, points, anomalies et confirmations externes."),
            ("Décider", "Clôturez avec un avis et une synthèse. Le dossier devient admissible au FUCCS selon l'avis."),
        ],
        "note": "Les dates validées alimentent le calendrier et avertissent le vérificateur dans l'application et par email.",
    },
    {
        "slug": "controle-fuccs",
        "title": "Grille de contrôle FUCCS",
        "subtitle": "Noter, justifier et finaliser un contrôle",
        "columns": ("Dossiers admissibles", "Grille et critères", "Résultat historisé"),
        "steps": [
            ("Démarrer ou reprendre", "Le bouton ouvre le contrôle existant du dossier ; il ne crée pas de doublon."),
            ("Noter", "Renseignez chaque critère, les commentaires obligatoires et les preuves demandées."),
            ("Finaliser", "Vérifiez les critères manquants puis enregistrez la synthèse finale."),
            ("Réouvrir", "Indiquez le motif : le même contrôle repasse en brouillon et conserve son historique."),
        ],
        "note": "Création, reprise, notation, constat, finalisation et réouverture sont inscrites dans le journal d'audit.",
    },
    {
        "slug": "validations",
        "title": "Validation et corrections",
        "subtitle": "Revue N1, décision N2 et suivi des réserves",
        "columns": ("File sans doublon", "Décision N1", "Décision N2"),
        "steps": [
            ("Sélectionner", "Ouvrez un dossier dont le contrôle FUCCS est finalisé."),
            ("Valider N1", "Prononcez la première décision avec justification et réserves si nécessaire."),
            ("Valider N2", "Un autre agent prononce la décision définitive après une décision N1 favorable."),
            ("Corriger", "Une décision ajournée suit le circuit de correction avant une nouvelle décision."),
        ],
        "note": "Une décision favorable active par niveau est protégée contre les doublons.",
    },
    {
        "slug": "integration-bnec",
        "title": "Intégration BNEC",
        "subtitle": "Passage contrôlé vers la Base nationale",
        "columns": ("Validations N2", "Plan et codification", "Intégration tracée"),
        "steps": [
            ("Ouvrir", "Choisissez une validation N2 favorable dans la file d'entrée."),
            ("Contrôler", "Lisez le plan, les ressources et les codes institutionnels proposés."),
            ("Exécuter", "Confirmez l'intégration : les écritures sont réalisées dans une transaction contrôlée."),
            ("Suivre", "Consultez le statut, les erreurs éventuelles et la référence de sauvegarde."),
        ],
        "note": "Après intégration, les certifications validées alimentent automatiquement audits, renouvellements, échéances et alertes.",
    },
    {
        "slug": "scoring", "title": "Scoring entreprise", "subtitle": "Évaluer la situation globale d'une entreprise",
        "columns": ("Entreprises", "Modèle publié", "Résultat courant"),
        "steps": [("Choisir", "Sélectionnez l'entreprise à évaluer."), ("Renseigner", "Complétez les critères définis par le modèle actif."), ("Calculer", "Prévisualisez puis validez le score et la classe."), ("Historique", "Cliquez sur la ligne courante pour revoir les scores précédents.")],
        "note": "Une entreprise occupe une seule ligne dans le tableau ; toutes ses évaluations restent historisées.",
    },
    {
        "slug": "infc", "title": "INFC", "subtitle": "Mesurer la fiabilité d'une certification",
        "columns": ("Certification", "Calcul INFC", "Validation et historique"),
        "steps": [("Choisir", "Sélectionnez la certification concernée."), ("Calculer", "Renseignez les critères du modèle INFC publié."), ("Valider", "Validez séparément le résultat calculé."), ("Historique", "Cliquez sur la ligne pour consulter les recalculs précédents.")],
        "note": "L'INFC concerne une certification et reste indépendant du scoring entreprise et du SNCC.",
    },
    {
        "slug": "sncc", "title": "Classement SNCC", "subtitle": "Classer une certification dans le référentiel national",
        "columns": ("Certification admissible", "Classement motivé", "Classement courant"),
        "steps": [("Sélectionner", "Choisissez une certification admissible après INFC."), ("Classer", "Renseignez classe, statut, risque, date et justification."), ("Reclasser", "Motivez toute modification du classement courant."), ("Historique", "Cliquez sur la ligne pour revoir les classements précédents.")],
        "note": "Une certification occupe une ligne courante ; chaque période antérieure reste consultable.",
    },
    {
        "slug": "dossiers-veille", "title": "Dossiers de veille", "subtitle": "Organiser les rappels et relances de suivi",
        "columns": ("Dossier et responsable", "Prochaine action", "Relances"),
        "steps": [("Ouvrir", "Sélectionnez la certification, l'événement et le responsable."), ("Planifier", "La prochaine action alimente les alertes et le calendrier."), ("Relancer", "Programmez la date d'envoi et le délai de réponse."), ("Suivre", "Consignez la réponse ou clôturez le dossier avec un motif.")],
        "note": "Les courriels sont mis en file ; le service réel d'expédition sera configuré avec le système mail backend.",
    },
    {
        "slug": "decisions-actions", "title": "Décisions et actions", "subtitle": "Préparer et diffuser une décision institutionnelle",
        "columns": ("Brouillon", "Soumission", "Décision prononcée"),
        "steps": [("Créer", "Décrivez la ressource, le contexte, les risques et la recommandation."), ("Autorité", "Choisissez un utilisateur proposé ou saisissez une autorité librement."), ("Soumettre", "Faites relire le brouillon avant décision."), ("Notifier", "La création avertit tous les utilisateurs actifs dans leur interface.")],
        "note": "Les exemples proposés facilitent la saisie mais restent entièrement modifiables par l'agent.",
    },
]


def wrap(c, text, x, y, width, size=8.5, leading=11, color=MUTED):
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if stringWidth(trial, "Helvetica", size) <= width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def make(guide):
    output = ROOT / "output" / "pdf" / f"guide-{guide['slug']}-hauqe.pdf"
    static = ROOT / "app" / "static" / "docs" / output.name
    output.parent.mkdir(parents=True, exist_ok=True)
    static.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output), pagesize=A4)
    width, height = A4
    c.setTitle(f"Guide - {guide['title']}")
    c.setFillColor(GREEN)
    c.rect(0, height - 108, width, 108, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 20)
    c.drawString(42, height - 57, guide["title"])
    c.setFont("Helvetica", 10)
    c.drawString(42, height - 79, guide["subtitle"])

    y = height - 140
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(42, y, "Interface en un coup d'oeil")
    y -= 22
    gap, total = 10, width - 84
    cw = (total - 2 * gap) / 3
    for idx, label in enumerate(guide["columns"], 1):
        x = 42 + (idx - 1) * (cw + gap)
        c.setFillColor(PALE if idx == 2 else HexColor("#F8FBF9"))
        c.setStrokeColor(LINE)
        c.roundRect(x, y - 112, cw, 112, 9, fill=1, stroke=1)
        c.setFillColor(GREEN)
        c.circle(x + 21, y - 23, 11, fill=1, stroke=0)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(x + 21, y - 26, str(idx))
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 9)
        wrap(c, label, x + 12, y - 50, cw - 24, 9, 12, INK)
        wrap(c, ("Consulter et filtrer." if idx == 1 else "Renseigner et vérifier." if idx == 2 else "Décider et suivre."), x + 12, y - 82, cw - 24)

    y -= 145
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(42, y, "Utilisation")
    y -= 25
    for idx, (title, text) in enumerate(guide["steps"], 1):
        c.setFillColor(GREEN)
        c.circle(54, y, 11, fill=1, stroke=0)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(54, y - 3, str(idx))
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(76, y + 4, title)
        wrap(c, text, 76, y - 10, width - 120)
        y -= 58

    c.setFillColor(PALE)
    c.roundRect(42, 53, width - 84, 58, 9, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(56, 89, "À retenir")
    wrap(c, guide["note"], 56, 74, width - 112, 8, 10)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7)
    c.drawRightString(width - 42, 25, f"HAUQE - {guide['title']} - page 1/1")
    c.save()
    static.write_bytes(output.read_bytes())
    return output


for item in GUIDES:
    print(make(item))
