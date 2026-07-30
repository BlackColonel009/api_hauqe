from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "guide-alertes-hauqe.pdf"
STATIC = ROOT / "app" / "static" / "docs" / "guide-alertes-hauqe.pdf"

GREEN = HexColor("#287E5F")
PALE = HexColor("#EDF7F2")
INK = HexColor("#18352B")
MUTED = HexColor("#60756D")
LINE = HexColor("#DCE9E3")


def wrapped(c, text, x, y, width, size=9, leading=13, color=INK):
    words = text.split()
    lines, current = [], ""
    for word in words:
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


def build(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    c.setTitle("Guide d'utilisation - Alertes HAUQE")

    c.setFillColor(GREEN)
    c.rect(0, height - 105, width, 105, fill=1, stroke=0)
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont("Helvetica-Bold", 21)
    c.drawString(42, height - 57, "Guide rapide - Alertes")
    c.setFont("Helvetica", 10)
    c.drawString(42, height - 78, "Consulter, comprendre et traiter une alerte HAUQE")

    y = height - 135
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(42, y, "Interface en un coup d'oeil")
    y -= 18

    # Schéma unique de l'interface.
    box_y, box_h = y - 235, 225
    c.setFillColor(HexColor("#F8FBF9"))
    c.setStrokeColor(LINE)
    c.roundRect(42, box_y, width - 84, box_h, 12, fill=1, stroke=1)
    c.setFillColor(PALE)
    c.roundRect(56, box_y + 168, width - 112, 38, 8, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(68, box_y + 190, "1  FILTRES")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(68, box_y + 177, "Rechercher puis filtrer par niveau, type ou statut.")

    c.setFillColor(HexColor("#FFFFFF"))
    c.setStrokeColor(LINE)
    c.roundRect(56, box_y + 20, 225, 135, 8, fill=1, stroke=1)
    c.roundRect(294, box_y + 20, width - 350, 135, 8, fill=1, stroke=1)
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(68, box_y + 137, "2  FILE DES ALERTES")
    c.drawString(306, box_y + 137, "3  DETAIL ET ACTIONS")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(68, box_y + 119, "Cliquez sur « Voir le détail ».")
    c.drawString(306, box_y + 119, "Lire le message et la traçabilité.")
    for idx, label in enumerate(("Alerte critique", "Audit à surveiller", "Document attendu")):
        row_y = box_y + 91 - idx * 27
        c.setFillColor(PALE if idx == 0 else HexColor("#F7F9F8"))
        c.roundRect(68, row_y, 195, 20, 5, fill=1, stroke=0)
        c.setFillColor(INK)
        c.drawString(78, row_y + 7, label)
    c.setFillColor(PALE)
    c.roundRect(306, box_y + 67, width - 374, 38, 5, fill=1, stroke=0)
    c.setFillColor(INK)
    c.drawString(316, box_y + 90, "Affecter - Notifier - Résoudre")
    c.setFillColor(MUTED)
    c.drawString(316, box_y + 76, "selon vos permissions")

    y = box_y - 28
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(42, y, "Comment traiter une alerte")
    y -= 22
    steps = [
        ("1", "Filtrer", "Utilisez la recherche ou les listes Niveau, Type et Statut."),
        ("2", "Ouvrir", "Cliquez sur une ligne : le détail s'affiche à droite."),
        ("3", "Vérifier", "Lisez le message, la ressource liée et la traçabilité."),
        ("4", "Agir", "Affectez, notifiez ou résolvez. Un motif est demandé lorsque nécessaire."),
    ]
    for number, title, text in steps:
        c.setFillColor(GREEN)
        c.circle(54, y - 2, 11, fill=1, stroke=0)
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(54, y - 5, number)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(76, y + 2, title)
        wrapped(c, text, 76, y - 11, width - 120, 8.5, 11, MUTED)
        y -= 46

    c.setFillColor(PALE)
    c.roundRect(42, 42, width - 84, 45, 8, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(56, 69, "Bon à savoir")
    wrapped(c, "Une ligne ouvre son détail ; « Ouvrir la ressource » mène au dossier d'origine lorsqu'un lien est disponible.", 56, 56, width - 112, 8, 10, MUTED)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7)
    c.drawRightString(width - 42, 22, "HAUQE - Guide Alertes - page 1/1")
    c.save()


build(OUTPUT)
STATIC.parent.mkdir(parents=True, exist_ok=True)
STATIC.write_bytes(OUTPUT.read_bytes())
print(OUTPUT)
