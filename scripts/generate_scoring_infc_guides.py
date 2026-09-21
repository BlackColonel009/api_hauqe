from pathlib import Path
from shutil import copy2

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf"
STATIC = ROOT / "app" / "static" / "docs"


def styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("guide-title", parent=base["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=colors.HexColor("#173d2f"), spaceAfter=7),
        "subtitle": ParagraphStyle("guide-subtitle", parent=base["BodyText"], fontSize=9, leading=13, textColor=colors.HexColor("#62756b"), spaceAfter=13),
        "head": ParagraphStyle("guide-head", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=colors.HexColor("#1f684d"), spaceBefore=8, spaceAfter=5),
        "body": ParagraphStyle("guide-body", parent=base["BodyText"], fontSize=9, leading=13, textColor=colors.HexColor("#2e4038"), alignment=TA_LEFT, spaceAfter=5),
        "note": ParagraphStyle("guide-note", parent=base["BodyText"], fontSize=8.5, leading=12, textColor=colors.HexColor("#465c52")),
    }


def bullet(text, style):
    return Paragraph(f"• {text}", style)


def build(path: Path, title: str, subtitle: str, sections: list[tuple[str, list[str]]]):
    st = styles()
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    flow = [Paragraph("HAUQE Certif - Guide de saisie", st["subtitle"]), Paragraph(title, st["title"]), Paragraph(subtitle, st["subtitle"])]
    for heading, items in sections:
        flow.append(Paragraph(heading, st["head"]))
        flow.extend(bullet(item, st["body"]) for item in items)
    flow.append(Spacer(1, 8))
    note = Table([[Paragraph("Les cartes visibles dans l'application affichent toujours les seuils, niveaux et la version réellement publiés. Ce guide explique la méthode ; il ne remplace pas la règle active.", st["note"])]], colWidths=[170 * mm])
    note.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef8f2")), ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#b9dec9")), ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    flow.append(note)
    doc.build(flow)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    STATIC.mkdir(parents=True, exist_ok=True)
    scoring = OUTPUT / "guide-scoring-hauqe.pdf"
    infc = OUTPUT / "guide-infc-hauqe.pdf"
    build(scoring, "Guide - Scoring entreprise", "Comment saisir et interpréter une classification à partir du modèle publié.", [
        ("1. Avant de commencer", ["Vérifiez que le bandeau indique un modèle publié et sa version.", "Lisez les cartes de classification : elles sont chargées depuis la règle active et peuvent changer après publication d'une nouvelle version."]),
        ("2. Saisir le score", ["Si le modèle est en saisie directe, entrez uniquement une valeur comprise dans la plage indiquée par le formulaire.", "N'utilisez pas un score FUCCS comme conversion automatique : la classification reste une décision calculée par son propre modèle."]),
        ("3. Contrôler avant validation", ["Utilisez Prévisualiser pour obtenir le résultat du backend sans enregistrer.", "Vérifiez le score, la classe proposée et la version du modèle, puis utilisez Calculer et valider."]),
    ])
    build(infc, "Guide - INFC", "Comprendre la notation des domaines et le calcul de l'indice national de fiabilité des certifications.", [
        ("1. Principe", ["L'INFC concerne une certification, et non l'entreprise entière.", "Le modèle affiché à l'écran décide du mode de calcul, des domaines obligatoires, des poids, des niveaux et de l'arrondi."]),
        ("2. Cas d'une moyenne pondérée sur 100", ["Chaque domaine est saisi sur une échelle de 0 à 100. Une note de 72 signifie 72 sur 100 pour ce domaine.", "Le poids indique l'influence relative du domaine dans le résultat. Ce n'est pas une note maximale.", "Le calcul est : somme des notes de domaines multipliées par leurs poids, divisée par la somme des poids."]),
        ("3. Saisie et validation", ["Renseignez tous les domaines obligatoires ; une valeur manquante bloque le calcul.", "L'aperçu de saisie donne une estimation. Prévisualiser et Calculer utilisent le backend et le modèle publié.", "La validation est distincte du calcul et exige des niveaux institutionnels publiés."]),
    ])
    copy2(scoring, STATIC / scoring.name)
    copy2(infc, STATIC / infc.name)


if __name__ == "__main__":
    main()
