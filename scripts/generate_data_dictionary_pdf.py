from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    LongTable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "DICTIONNAIRE_DONNEES_66_TABLES.md"
OUTPUT = ROOT / "output" / "pdf" / "DICTIONNAIRE_DONNEES_HAUQE_CERTIF.pdf"

GREEN = colors.HexColor("#0B6B4B")
DARK_GREEN = colors.HexColor("#064C38")
LIGHT_GREEN = colors.HexColor("#E7F3EE")
GOLD = colors.HexColor("#D3A229")
LIGHT_GOLD = colors.HexColor("#FFF4D6")
INK = colors.HexColor("#1E2925")
MUTED = colors.HexColor("#64706B")
GRID = colors.HexColor("#B9CAC3")
WHITE = colors.white


def register_fonts() -> tuple[str, str]:
    candidates = [
        (
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ),
        (
            Path("C:/Windows/Fonts/calibri.ttf"),
            Path("C:/Windows/Fonts/calibrib.ttf"),
        ),
    ]
    for regular, bold in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont("DocRegular", str(regular)))
            pdfmetrics.registerFont(TTFont("DocBold", str(bold)))
            return "DocRegular", "DocBold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()


def parse_markdown():
    text = SOURCE.read_text(encoding="utf-8")
    summary = {}
    for label in ("Nombre de tables", "Nombre de clés étrangères"):
        match = re.search(rf"\*\*{re.escape(label)} :\*\*\s*(\d+)", text)
        if match:
            summary[label] = int(match.group(1))

    tables = []
    current = None
    for line in text.splitlines():
        heading = re.match(r"^##\s+(\d+)\.\s+`([^`]+)`", line)
        if heading:
            current = {
                "number": int(heading.group(1)),
                "name": heading.group(2),
                "rows": [],
            }
            tables.append(current)
            continue
        row = re.match(
            r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*(.*?)\s*\|$",
            line,
        )
        if row and current:
            current["rows"].append(row.groups())
    return summary, tables


def p(text: str, style: ParagraphStyle) -> Paragraph:
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("`", "")
    )
    return Paragraph(safe, style)


def page_decor(canvas, doc):
    canvas.saveState()
    width, height = landscape(A4)
    canvas.setFillColor(GREEN)
    canvas.rect(0, height - 13 * mm, width, 13 * mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, height - 14 * mm, width, 1 * mm, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont(FONT_BOLD, 8)
    canvas.drawString(14 * mm, height - 8.5 * mm, "HAUQE Certif - Dictionnaire de données")
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT, 7)
    canvas.drawString(14 * mm, 8 * mm, "Base nationale des entreprises certifiées - Version 0.3")
    canvas.drawRightString(width - 14 * mm, 8 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build():
    summary, tables = parse_markdown()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=landscape(A4),
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=20 * mm,
        bottomMargin=14 * mm,
        title="Dictionnaire de données HAUQE Certif",
        author="Projet HAUQE Certif",
        subject="Dictionnaire des 66 tables PostgreSQL",
        pageCompression=1,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "CoverTitle", parent=styles["Title"], fontName=FONT_BOLD,
        fontSize=26, leading=31, textColor=GREEN, alignment=TA_CENTER,
        spaceAfter=8 * mm,
    )
    subtitle = ParagraphStyle(
        "CoverSubtitle", parent=styles["Normal"], fontName=FONT,
        fontSize=13, leading=18, textColor=DARK_GREEN, alignment=TA_CENTER,
        spaceAfter=14 * mm,
    )
    heading = ParagraphStyle(
        "TableHeading", parent=styles["Heading2"], fontName=FONT_BOLD,
        fontSize=13, leading=16, textColor=GREEN, spaceBefore=4 * mm,
        spaceAfter=2.5 * mm, keepWithNext=True,
    )
    body = ParagraphStyle(
        "Body", parent=styles["BodyText"], fontName=FONT,
        fontSize=8.2, leading=10.2, textColor=INK,
    )
    body_bold = ParagraphStyle(
        "BodyBold", parent=body, fontName=FONT_BOLD, textColor=DARK_GREEN,
    )
    header_text = ParagraphStyle(
        "HeaderText", parent=body, fontName=FONT_BOLD, fontSize=8,
        leading=9.5, textColor=WHITE, alignment=TA_CENTER,
    )
    note = ParagraphStyle(
        "Note", parent=body, fontSize=9.5, leading=13, textColor=MUTED,
        alignment=TA_LEFT,
    )

    story = [
        Spacer(1, 37 * mm),
        p("DICTIONNAIRE DE DONNÉES", title),
        p("HAUQE Certif - Base nationale des entreprises certifiées", subtitle),
    ]
    metrics = [
        [p("66", ParagraphStyle("Metric", parent=title, fontSize=22, leading=24, textColor=WHITE)),
         p("843", ParagraphStyle("Metric2", parent=title, fontSize=22, leading=24, textColor=WHITE)),
         p("107", ParagraphStyle("Metric3", parent=title, fontSize=22, leading=24, textColor=WHITE))],
        [p("tables", header_text), p("colonnes", header_text), p("clés étrangères", header_text)],
    ]
    metric_table = Table(metrics, colWidths=[78 * mm, 78 * mm, 78 * mm], rowHeights=[18 * mm, 10 * mm])
    metric_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GREEN),
        ("BOX", (0, 0), (-1, -1), 0.8, DARK_GREEN),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, LIGHT_GREEN),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.extend([
        metric_table,
        Spacer(1, 14 * mm),
        p(
            "Ce document décrit les tables, colonnes, types PostgreSQL, clés et relations "
            "du modèle rationalisé HAUQE Certif. PK = clé primaire, FK = clé étrangère, "
            "UQ = valeur unique et NN = valeur obligatoire.",
            note,
        ),
        Spacer(1, 10 * mm),
        p("Version 0.3 - Document de travail à valider par la HAUQE/GFA", note),
        PageBreak(),
    ])

    for table in tables:
        story.append(p(f"{table['number']}. {table['name']}", heading))
        data = [[
            p("Colonne", header_text),
            p("Type PostgreSQL", header_text),
            p("Contraintes / relation", header_text),
        ]]
        for column, data_type, constraint in table["rows"]:
            data.append([
                p(column, body_bold),
                p(data_type, body),
                p(constraint, body),
            ])
        long_table = LongTable(
            data,
            colWidths=[70 * mm, 52 * mm, 147 * mm],
            repeatRows=1,
            splitByRow=1,
            hAlign="LEFT",
        )
        long_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("GRID", (0, 0), (-1, -1), 0.35, GRID),
            ("BACKGROUND", (0, 1), (-1, -1), WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GREEN]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.extend([long_table, Spacer(1, 3.5 * mm)])

    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    print(OUTPUT)


if __name__ == "__main__":
    build()
