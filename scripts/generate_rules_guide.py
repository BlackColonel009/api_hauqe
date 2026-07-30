from pathlib import Path
from shutil import copyfile

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table,
    TableStyle, PageBreak, KeepTogether,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "guide-regles-codification-hauqe-v2.pdf"
STATIC = ROOT / "app" / "static" / "docs" / "guide-regles-codification-hauqe.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

GREEN = colors.HexColor("#176B4D")
GREEN_SOFT = colors.HexColor("#EAF6F0")
INK = colors.HexColor("#263B32")
MUTED = colors.HexColor("#667970")
LINE = colors.HexColor("#DCE7E1")
ORANGE = colors.HexColor("#A86620")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=26, leading=31, textColor=colors.white, alignment=TA_CENTER, spaceAfter=10))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontSize=11, leading=17,
    textColor=colors.HexColor("#D7EEE4"), alignment=TA_CENTER))
styles.add(ParagraphStyle(name="H1x", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=19, leading=23, textColor=GREEN, spaceAfter=10))
styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=12, leading=15, textColor=INK, spaceBefore=9, spaceAfter=5))
styles.add(ParagraphStyle(name="Bodyx", parent=styles["BodyText"], fontSize=9.2, leading=13.5,
    textColor=INK, spaceAfter=6))
styles.add(ParagraphStyle(name="Smallx", parent=styles["BodyText"], fontSize=7.8, leading=11,
    textColor=MUTED))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontSize=8.8, leading=13,
    textColor=INK, leftIndent=8, rightIndent=8, spaceBefore=4, spaceAfter=8))
styles.add(ParagraphStyle(name="CodeX", parent=styles["Code"], fontName="Courier", fontSize=7.2,
    leading=10, textColor=INK, leftIndent=8, rightIndent=8, spaceBefore=5, spaceAfter=8))


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 282 * mm, 192 * mm, 282 * mm)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(GREEN)
    canvas.drawString(18 * mm, 286 * mm, "HAUQE CERTIF - GUIDE REGLES & CODIFICATION")
    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(192 * mm, 286 * mm, "Version 2.0 - 30 juillet 2026")
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.drawString(18 * mm, 9 * mm, "Document operationnel simplifie")
    canvas.drawRightString(192 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


doc = BaseDocTemplate(str(OUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm,
    topMargin=28 * mm, bottomMargin=18 * mm, title="Guide Regles et codification HAUQE Certif v2")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
doc.addPageTemplates(PageTemplate(id="guide", frames=[frame], onPage=header_footer))
story = []


def p(text, style="Bodyx"):
    story.append(Paragraph(text, styles[style]))


def h1(text):
    story.append(Paragraph(text, styles["H1x"]))


def h2(text):
    story.append(Paragraph(text, styles["H2x"]))


def bullets(items):
    for item in items:
        p(f"• {item}")


def callout(title, text, tone=GREEN_SOFT):
    block = Table([[Paragraph(f"<b>{title}</b><br/>{text}", styles["Callout"])]],
        colWidths=[doc.width])
    block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), tone),
        ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.extend([block, Spacer(1, 4)])


def table(headers, rows, widths=None):
    data = [[Paragraph(f"<b>{x}</b>", styles["Smallx"]) for x in headers]]
    data += [[Paragraph(str(x), styles["Smallx"]) for x in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FBF9")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([t, Spacer(1, 8)])


# Cover
cover = Table([[
    Paragraph("HAUQE CERTIF<br/><font size='11'>Administration fonctionnelle</font>", styles["CoverTitle"])
], [
    Paragraph("Guide simple des règles, de la codification BNEC, du scoring et des grilles FUCCS",
              styles["CoverSub"])
]], colWidths=[doc.width], rowHeights=[78 * mm, 35 * mm])
cover.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), GREEN),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("BOX", (0, 0), (-1, -1), 0, GREEN),
]))
story.extend([Spacer(1, 34 * mm), cover, Spacer(1, 12 * mm)])
p("<b>Version 2.0</b> - alignée sur la page Règles, codification, grilles FUCCS & scoring.", "Bodyx")
p("Public : administrateurs fonctionnels et agents habilités. Une configuration ne devient exécutable qu'après publication avec une référence d'approbation et une date d'effet.", "Bodyx")
story.append(PageBreak())

h1("1. Comprendre la page")
p("La page contient cinq onglets. Chacun répond à un besoin précis. Ne placez pas une formule de scoring dans une règle générique et ne confondez pas la codification BNEC avec les codes FUCCS.")
table(["Onglet", "Utilité"], [
    ("COLLECTE_COMPLETUDE", "Définit ce qui doit être présent avant la soumission d'une fiche."),
    ("Codification BNEC", "Construit les identifiants officiels des entreprises et certifications."),
    ("Règles métier", "Versionne des paramètres JSON consommés par un moteur connu."),
    ("Modèles de scoring", "Définit formules, classes, niveaux et pondérations."),
    ("Grilles FUCCS", "Organise la grille, ses rubriques, critères, preuves et scores."),
], [48 * mm, 126 * mm])
h2("Cycle de vie commun")
table(["Statut", "Comportement"], [
    ("BROUILLON", "Modifiable, testable, sans effet opérationnel."),
    ("PUBLIE", "Immuable et utilisable à partir de sa date d'effet."),
    ("RETIRE", "Conservé dans l'historique, non utilisé pour de nouveaux traitements."),
], [35 * mm, 139 * mm])
callout("Règle essentielle", "Pour corriger une version publiée, clonez-la, modifiez le nouveau brouillon, testez-le puis publiez la nouvelle version.")
h2("Publication")
bullets([
    "Renseigner une référence d'approbation retrouvable.",
    "Choisir une date d'effet cohérente.",
    "Tester la prévisualisation avant publication.",
    "Vérifier les cartes de préparation affichées en haut de la page.",
])
story.append(PageBreak())

h1("2. COLLECTE_COMPLETUDE")
p("Cette règle autorise les brouillons incomplets mais contrôle la fiche au moment de sa soumission.")
h2("Construction dans l'interface")
bullets([
    "Créer une nouvelle version et conserver la famille COLLECTE.",
    "Ajouter une exigence de champs : ALL exige tous les champs, ANY au moins un.",
    "Ajouter une exigence de quantité pour les documents, offres ou certifications déclarées.",
    "Fixer le taux minimum de soumission, généralement 100 après décision.",
    "Valider, enregistrer le brouillon, tester puis publier.",
])
table(["Type", "Exemple", "Effet"], [
    ("FIELD / ALL", "entreprise_id + version_formulaire", "Tous les champs doivent être présents."),
    ("FIELD / ANY", "téléphone ou courriel", "Une des valeurs suffit."),
    ("COUNT", "DOCUMENTS, minimum 1", "Au moins une ressource liée est requise."),
], [34 * mm, 63 * mm, 77 * mm])
callout("Attention", "Le catalogue affiché dans la page est la source de vérité. N'ajoutez pas manuellement un nom de champ ou de ressource absent du catalogue.", colors.HexColor("#FFF7E9"))
h2("Exemple minimal")
p("""{
  "requirements": [
    {"type":"FIELD","label":"Entreprise liée",
     "fields":["entreprise_id"],"match":"ALL"}
  ],
  "minimum_submission_rate": 100
}""", "CodeX")
story.append(PageBreak())

h1("3. Codification BNEC")
p("BNEC signifie Base nationale des entreprises certifiées. Cet onglet définit séparément les codes officiels des entreprises et ceux des certifications.")
h2("Méthode")
bullets([
    "Choisir l'objet : ENTREPRISE ou CERTIFICATION.",
    "Saisir code logique, version, libellé et description.",
    "Construire le format avec les jetons proposés par la page.",
    "Définir le séparateur, la longueur de séquence, sa portée et sa remise à zéro.",
    "Renseigner uniquement les constantes nécessaires.",
    "Contrôler l'aperçu et les diagnostics avant d'enregistrer.",
    "Publier avec référence et date d'effet.",
])
table(["Élément", "Rôle"], [
    ("Jeton", "Segment calculé depuis le contexte de l'entreprise ou de la certification."),
    ("Constante", "Valeur stable telle que HAUQE, BNEC, pays ou préfixe certification."),
    ("Séquence", "Numéro unique réservé par le backend selon la portée configurée."),
    ("Aperçu", "Exemple visuel ; il ne réserve aucun numéro réel."),
], [42 * mm, 132 * mm])
callout("Séparation obligatoire", "Un modèle ENTREPRISE ne doit pas être réutilisé pour CERTIFICATION. Les deux objets ont leur propre format et leur propre séquence.")
story.append(PageBreak())

h1("4. Règles métier génériques")
p("Une règle générique contient un JSON versionné. Elle n'a d'effet que si un moteur de l'application connaît son code logique.")
h2("Exemple réellement consommé : VEILLE_SEUILS_EXPIRATION")
p("""{
  "thresholds": [
    {"days":180,"niveau":1,"code":"INFO_180","label":"Information"},
    {"days":90,"niveau":2,"code":"SURVEILLANCE_90","label":"Surveillance"},
    {"days":30,"niveau":3,"code":"URGENCE_30","label":"Urgence"},
    {"days":0,"niveau":4,"code":"CRITIQUE_EXPIRATION","label":"Critique"}
  ]
}""", "CodeX")
callout("Ne pas supposer", "Publier un nouveau code logique ne crée pas automatiquement une fonctionnalité. Le backend doit être programmé pour le lire.")
h2("Contrôles JSON")
bullets([
    "Guillemets doubles autour des clés et textes.",
    "true et false en minuscules.",
    "Aucune virgule après le dernier élément.",
    "Les nombres restent des nombres et non des textes.",
])
story.append(PageBreak())

h1("5. Modèles de scoring et INFC")
p("Classification entreprise, INFC, FUCCS et SNCC sont quatre résultats distincts. Aucun passage automatique de l'un à l'autre n'est appliqué.")
h2("Modes disponibles")
table(["Mode", "Utilisation"], [
    ("DIRECT_SCORE", "Le formulaire reçoit directement un score puis applique classes ou niveaux."),
    ("WEIGHTED_AVERAGE_100", "Chaque domaine est noté sur 100 ; moyenne selon les poids."),
    ("SUM_DOMAIN_POINTS", "Chaque domaine reçoit des points jusqu'à son maximum."),
], [54 * mm, 120 * mm])
h2("INFC - configuration actuelle")
p("INFC signifie Indice national de fiabilité des certifications. Le modèle documenté utilise six domaines et un total de pondération de 100.")
table(["Domaine", "Poids"], [
    ("AUTHENTICITE", "20"), ("VALIDITE", "20"), ("MAINTIEN", "20"),
    ("MAITRISE_DOCUMENTAIRE", "15"),
    ("TRACABILITE_MAITRISE_OPERATIONNELLE", "15"),
    ("SUIVI_RENOUVELLEMENT", "10"),
], [135 * mm, 39 * mm])
story.append(PageBreak())

h1("6. Niveaux INFC et validation")
p("Un résultat INFC peut être calculé sans niveau, mais il ne peut pas être validé tant que la version publiée ne contient pas une liste levels couvrant tout le score de 0 à 100.")
table(["Niveau", "Lecture", "Intervalle"], [
    ("1", "Excellence", "95 à 100"),
    ("2", "Très satisfaisant", "90 à 94,99"),
    ("3", "Satisfaisant", "75 à 89,99"),
    ("4", "Acceptable", "60 à 74,99"),
    ("5", "Faible", "40 à 59,99"),
    ("6", "Critique", "0 à 39,99"),
], [28 * mm, 82 * mm, 64 * mm])
h2("JSON à placer dans Classes / niveaux")
p("""[
  {"niveau":1,"min":95,"max":100},
  {"niveau":2,"min":90,"max":94.99},
  {"niveau":3,"min":75,"max":89.99},
  {"niveau":4,"min":60,"max":74.99},
  {"niveau":5,"min":40,"max":59.99},
  {"niveau":6,"min":0,"max":39.99}
]""", "CodeX")
callout("Après une nouvelle version", "Publiez la version complète, puis recalculez les certifications dont l'ancien résultat ne possède pas de niveau. Le nouveau résultat sera CALCULE puis pourra passer à VALIDE.")
story.append(PageBreak())

h1("7. Grilles FUCCS")
p("Une grille FUCCS est composée de rubriques et de critères. La version appartient à la grille ; les codes des rubriques et critères restent stables lorsque leur sens ne change pas.")
h2("Ordre de construction")
bullets([
    "Créer ou cloner une grille BROUILLON.",
    "Ajouter les rubriques avec code, ordre, libellé et description.",
    "Ajouter les critères avec score maximal, obligations de commentaire et de preuve.",
    "Contrôler le score maximal total.",
    "Tester un contrôle complet.",
    "Publier avec référence et date d'effet.",
])
h2("Préremplissage historique de recette")
p("Le bouton de préremplissage ajoute 6 rubriques, 24 critères et 48 points dans une grille BROUILLON vide. Ce modèle sert à la recette et n'est jamais publié automatiquement.")
table(["Condition", "Valeur"], [
    ("Permission", "FUCCS.ADMINISTRER_GRILLE"),
    ("Grille", "BROUILLON et vide"),
    ("Résultat", "6 rubriques, 24 critères, score maximal 48"),
    ("Transaction", "Tout est créé ou rien n'est conservé"),
], [45 * mm, 129 * mm])
callout("Publication FUCCS", "Relisez chaque critère et adaptez les obligations avant publication. Le backend ne force ni 24 critères, ni 28 critères, ni un total de 100.")
story.append(PageBreak())

h1("8. Checklist et dépannage")
table(["Avant publication", "Question"], [
    ("Code et objet", "Le code logique et l'objet correspondent-ils au moteur concerné ?"),
    ("Version", "La version est-elle nouvelle ?"),
    ("Structure", "JSON, segments, rubriques ou critères sont-ils complets ?"),
    ("Couverture", "Toutes les bornes de score sont-elles couvertes ?"),
    ("Test", "La prévisualisation et les cas limites ont-ils été essayés ?"),
    ("Approbation", "Référence et date d'effet sont-elles officielles ?"),
], [48 * mm, 126 * mm])
h2("Messages fréquents")
table(["Message", "Action"], [
    ("Aucune version publiée active", "Publier une version applicable ou vérifier sa date d'effet."),
    ("Version déjà existante", "Cloner ou choisir une nouvelle version."),
    ("Score hors niveau", "Corriger les intervalles levels afin de couvrir 0 à 100."),
    ("Domaine manquant", "Renseigner tous les domaines si missing_policy vaut REJECT."),
    ("Grille immuable", "Cloner la grille publiée au lieu de la modifier."),
    ("Permission insuffisante", "Faire vérifier les permissions du rôle."),
], [58 * mm, 116 * mm])
callout("Retour arrière", "Ne supprimez pas l'historique. Publiez une version corrigée puis retirez la version erronée avec une date et un motif.")
p("<b>Fin du guide.</b> Après publication, actualisez la page et vérifiez les cartes de préparation avant de reprendre Collecte, Codification BNEC, Scoring ou FUCCS.")

doc.build(story)
copyfile(OUT, STATIC)
print(OUT)
print(STATIC)
