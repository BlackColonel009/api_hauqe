"""Génère le guide pratique du classement SNCC, servi par l'application."""

from pathlib import Path
from shutil import copyfile

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "guide-sncc-hauqe.pdf"
STATIC = ROOT / "app" / "static" / "docs" / "guide-sncc-hauqe.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

GREEN = colors.HexColor("#176B4D")
GREEN_SOFT = colors.HexColor("#EAF6F0")
INK = colors.HexColor("#263B32")
MUTED = colors.HexColor("#667970")
LINE = colors.HexColor("#DCE7E1")
ORANGE = colors.HexColor("#A86620")
RED = colors.HexColor("#A34A45")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=25, leading=30, textColor=colors.white, alignment=TA_CENTER, spaceAfter=9))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontSize=10.5, leading=15, textColor=colors.HexColor("#D7EEE4"), alignment=TA_CENTER))
styles.add(ParagraphStyle(name="H1x", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=GREEN, spaceAfter=9))
styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=14, textColor=INK, spaceBefore=9, spaceAfter=5))
styles.add(ParagraphStyle(name="Bodyx", parent=styles["BodyText"], fontSize=9, leading=13, textColor=INK, spaceAfter=6))
styles.add(ParagraphStyle(name="Smallx", parent=styles["BodyText"], fontSize=7.6, leading=10.3, textColor=MUTED))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontSize=8.7, leading=12.5, textColor=INK, leftIndent=8, rightIndent=8, spaceBefore=5, spaceAfter=8))
styles.add(ParagraphStyle(name="TableHead", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=7.5, leading=9.5, textColor=colors.white))
styles.add(ParagraphStyle(name="TableCell", parent=styles["BodyText"], fontSize=7.5, leading=10, textColor=INK))


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(18 * mm, 282 * mm, 192 * mm, 282 * mm)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(GREEN)
    canvas.drawString(18 * mm, 286 * mm, "HAUQE CERTIF - GUIDE CLASSEMENT SNCC")
    canvas.setFont("Helvetica", 7.2)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(192 * mm, 286 * mm, "Version 2.0 - 21 septembre 2026")
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.drawString(18 * mm, 9 * mm, "Guide opérationnel simplifié")
    canvas.drawRightString(192 * mm, 9 * mm, f"Page {doc.page}")
    canvas.restoreState()


doc = BaseDocTemplate(str(OUT), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=28 * mm, bottomMargin=18 * mm, title="Guide Classement SNCC HAUQE Certif")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
doc.addPageTemplates(PageTemplate(id="guide", frames=[frame], onPage=header_footer))
story = []


def p(text, style="Bodyx"):
    story.append(Paragraph(text, styles[style]))


def h1(text):
    story.append(Paragraph(text, styles["H1x"]))


def h2(text):
    story.append(Paragraph(text, styles["H2x"]))


def callout(title, text, tone=GREEN_SOFT):
    table = Table([[Paragraph(f"<b>{title}</b><br/>{text}", styles["Callout"])]], colWidths=[174 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), tone),
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(table)
    story.append(Spacer(1, 5))


def reference_table(headers, rows, widths):
    data = [[Paragraph(cell, styles["TableHead"]) for cell in headers]]
    data += [[Paragraph(cell, styles["TableCell"]) for cell in row] for row in rows]
    table = Table(data, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FBF9")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    story.append(Spacer(1, 8))


# Couverture
cover = Table([[Paragraph("CLASSEMENT SNCC", styles["CoverTitle"])], [Paragraph("Guide pratique de lecture, de décision et de traçabilité", styles["CoverSub"])]], colWidths=[174 * mm], rowHeights=[28 * mm, 19 * mm])
cover.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), GREEN), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 16), ("RIGHTPADDING", (0, 0), (-1, -1), 16)]))
story += [Spacer(1, 18 * mm), cover, Spacer(1, 13 * mm)]
h1("Ce que le SNCC permet de décider")
p("Le Système national de classement des certifications (SNCC) enregistre une décision administrative motivée pour une certification. Il ne transforme pas automatiquement un score FUCCS ou un indice INFC en classement.")
callout("Les trois dimensions sont distinctes", "La <b>classe</b> exprime le niveau global de conformité observé. Le <b>statut administratif</b> indique la situation de la certification. Le <b>risque</b> aide à organiser le niveau de suivi. Les trois valeurs doivent être sélectionnées et justifiées.")
h2("Parcours en quatre étapes")
reference_table(["Étape", "Action attendue"], [
    ("1. Sélectionner", "Choisir une certification admissible après les contrôles et validations requis."),
    ("2. Examiner", "Relire les documents, constats, anomalies, décisions et éléments de suivi."),
    ("3. Classer", "Renseigner classe, statut administratif, risque, date d'effet et justification."),
    ("4. Suivre", "Reclasser ou clôturer lorsque la situation évolue. L'ancienne période reste dans l'historique."),
], [37 * mm, 137 * mm])
callout("Règle de traçabilité", "Une justification claire doit expliquer la décision : faits contrôlés, anomalies éventuelles, documents ou confirmation externe utilisée, et action de suivi attendue.", colors.HexColor("#FFF7E8"))

story.append(PageBreak())
h1("Définitions des classements")
p("Les définitions ci-dessous servent à lire et renseigner les valeurs dans HAUQE Certif. Elles sont des repères opérationnels : toute décision reste fondée sur le dossier, les règles publiées et la justification saisie.")
h2("Classe de conformité")
reference_table(["Classe", "Lecture pratique"], [
    ("A+", "Situation très favorable : éléments de conformité complets et cohérents ; aucun point significatif non traité dans le périmètre examiné."),
    ("A", "Situation favorable : conformité globalement établie ; écarts mineurs éventuels documentés et sans effet majeur sur la décision."),
    ("B", "Situation satisfaisante avec améliorations à suivre : certains écarts ou preuves incomplètes nécessitent une action ou une vérification planifiée."),
    ("C", "Situation fragilisée : écarts significatifs, incohérences ou preuves insuffisantes ; suivi renforcé et correction attendue."),
    ("D", "Situation critique : non-conformité majeure, information non fiable ou risque élevé ; escalade et décision administrative requises."),
], [22 * mm, 152 * mm])
h2("Statut administratif")
reference_table(["Code", "Signification opérationnelle"], [
    ("VA", "Valide : certification reconnue comme active dans son périmètre et sa période d'effet."),
    ("RE", "Sous réserve : certification conservée avec conditions, corrections ou vérifications complémentaires à suivre."),
    ("SU", "Suspendue : effet de la certification interrompu temporairement dans l'attente d'une décision ou d'une régularisation."),
    ("RT", "Retirée : reconnaissance retirée par décision compétente ; l'historique est conservé."),
    ("EX", "Expirée : période de validité échue sans renouvellement applicable enregistré."),
    ("VE", "Sous veille : certification suivie de manière renforcée ; une échéance, une confirmation ou une action de contrôle est attendue."),
], [22 * mm, 152 * mm])
callout("Attention", "Le statut administratif ne remplace pas la classe. Par exemple, une certification peut être classée B et placée sous veille (VE) si un contrôle complémentaire est nécessaire.", colors.HexColor("#F2F7FC"))

story.append(PageBreak())
h1("Risque, anomalies et décision")
h2("Niveau de risque")
reference_table(["Niveau", "Lecture pratique"], [
    ("R1", "Risque faible : suivi courant suffisant."),
    ("R2", "Risque limité : point de vigilance identifié, sans urgence."),
    ("R3", "Risque modéré : action ou contrôle complémentaire à planifier."),
    ("R4", "Risque élevé : suivi rapproché, responsable et échéance nécessaires."),
    ("R5", "Risque critique : traitement prioritaire, escalade et traçabilité renforcée."),
], [22 * mm, 152 * mm])
h2("Qu'est-ce qu'une anomalie ?")
p("Une anomalie est un fait constaté qui mérite d'être enregistré, expliqué et suivi. Elle ne signifie pas automatiquement que la certification est invalide ; son effet dépend de sa gravité, des preuves disponibles et de la décision instruite.")
reference_table(["Type", "Exemple de constat", "Réponse attendue"], [
    ("Documentaire", "Certificat, pièce ou date de validité manquante.", "Demander ou compléter la preuve."),
    ("Cohérence", "Numéro, norme, portée ou entreprise incohérents entre deux sources.", "Comparer les sources et corriger la donnée justifiée."),
    ("Authenticité", "Doute sur l'émetteur, le numéro ou la validité d'un certificat.", "Déclencher une confirmation auprès de l'organisme compétent."),
    ("Conformité", "Écart entre la portée déclarée et les éléments vérifiés.", "Instruire l'écart, exiger une correction ou adapter le suivi."),
    ("Critique", "Indice sérieux de fraude, de falsification ou de non-conformité majeure.", "Escalader sans délai et consigner la décision."),
], [28 * mm, 74 * mm, 72 * mm])
callout("Bon réflexe de rédaction", "Écrire des faits vérifiables : <i>« La date de fin indiquée sur le certificat est dépassée depuis le 12/09/2026 ; confirmation demandée à l'organisme X »</i>. Éviter les formulations vagues comme <i>« document suspect »</i>.", colors.HexColor("#FFF3F1"))
h2("Avant d'enregistrer")
p("Vérifier que la certification concernée est la bonne, que les trois valeurs SNCC sont renseignées, que la date d'effet est cohérente, et que la justification permet à un autre utilisateur de comprendre la décision. En cas de reclassement, préciser ce qui a changé depuis le classement précédent.")

doc.build(story)
copyfile(OUT, STATIC)
print(OUT)
print(STATIC)
