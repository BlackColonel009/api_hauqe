from __future__ import annotations

import math
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfgen import canvas


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from generate_mcd_pdf import (  # noqa: E402
    DARK_GREEN,
    FONT,
    FONT_BOLD,
    GOLD,
    GREEN,
    INK,
    LIGHT_GOLD,
    LIGHT_GREEN,
    LINE,
    MUTED,
    PAGES,
    PAPER,
    PAGE_H,
    PAGE_W,
    WHITE,
    DomainPage,
    Entity,
    Relation,
    fit_text,
)


OUTPUT = ROOT / "output" / "pdf" / "MCD_HAUQE_CERTIF_POWERDESIGNER.pdf"


def page_header(c: canvas.Canvas, title: str, subtitle: str, page_no: int, total: int, code: str) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.rect(0, PAGE_H - 76, PAGE_W, 76, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, PAGE_H - 80, PAGE_W, 4, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 20)
    c.drawString(34, PAGE_H - 34, title)
    c.setFont(FONT, 8.5)
    c.drawString(34, PAGE_H - 54, subtitle)
    c.setFillColor(LIGHT_GOLD)
    c.roundRect(PAGE_W - 142, PAGE_H - 56, 108, 28, 7, fill=1, stroke=0)
    c.setFillColor(DARK_GREEN)
    c.setFont(FONT_BOLD, 10)
    c.drawCentredString(PAGE_W - 88, PAGE_H - 47, code)
    c.setFillColor(MUTED)
    c.setFont(FONT, 7.2)
    c.drawString(34, 19, "HAUQE Certif - MCD détaillé - Notation Merise / PowerDesigner - Version 0.2")
    c.drawRightString(PAGE_W - 34, 19, f"Page {page_no} / {total}")


def entity_dimensions(entity: Entity, max_w: float, compact: bool) -> tuple[float, float]:
    attr_line = 8.2 if compact else 9
    header_h = 24
    h = header_h + 16 + len(entity.attrs) * attr_line
    h = max(67, min(h, 132 if compact else 150))
    return max_w, h


def layout_entities(entities: tuple[Entity, ...]) -> dict[str, tuple[float, float, float, float]]:
    count = len(entities)
    cols = 4 if count <= 8 else 5
    rows = math.ceil(count / cols)
    left = 34
    right = PAGE_W - 34
    top = PAGE_H - 100
    bottom = 98
    cell_w = (right - left) / cols
    cell_h = (top - bottom) / rows
    card_w = cell_w - 30
    compact = count > 10
    result: dict[str, tuple[float, float, float, float]] = {}
    for idx, entity in enumerate(entities):
        row = idx // cols
        col = idx % cols
        w, h = entity_dimensions(entity, card_w, compact)
        cx = left + col * cell_w + cell_w / 2
        cy = top - row * cell_h - cell_h / 2
        x = cx - w / 2
        y = cy - h / 2
        result[entity.name] = (x, y, w, h)
    return result


def closest_points(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
) -> tuple[tuple[float, float], tuple[float, float]]:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    acx, acy = ax + aw / 2, ay + ah / 2
    bcx, bcy = bx + bw / 2, by + bh / 2
    dx, dy = bcx - acx, bcy - acy
    if abs(dx) >= abs(dy):
        if dx >= 0:
            return (ax + aw, acy), (bx, bcy)
        return (ax, acy), (bx + bw, bcy)
    if dy >= 0:
        return (acx, ay + ah), (bcx, by)
    return (acx, ay), (bcx, by + bh)


def draw_association(
    c: canvas.Canvas,
    relation: Relation,
    left_box: tuple[float, float, float, float],
    right_box: tuple[float, float, float, float],
    offset: float,
) -> None:
    p1, p2 = closest_points(left_box, right_box)
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    length = max(math.hypot(dx, dy), 1)
    nx, ny = -dy / length, dx / length
    x1 += nx * offset
    y1 += ny * offset
    x2 += nx * offset
    y2 += ny * offset

    c.setStrokeColor(colors.HexColor("#799188"))
    c.setLineWidth(0.8)
    same_row = abs((left_box[1] + left_box[3] / 2) - (right_box[1] + right_box[3] / 2)) < 12
    if same_row:
        route_y = max(left_box[1] + left_box[3], right_box[1] + right_box[3]) + 13 + offset
        c.line(x1, y1, x1, route_y)
        c.line(x1, route_y, x2, route_y)
        c.line(x2, route_y, x2, y2)
        mx, my = (x1 + x2) / 2, route_y
        card_left = (x1, y1 + (route_y - y1) * 0.28)
        card_right = (x2, y2 + (route_y - y2) * 0.28)
    else:
        c.line(x1, y1, x2, y2)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        card_left = (x1 + dx * 0.13 + nx * 10, y1 + dy * 0.13 + ny * 10)
        card_right = (x2 - dx * 0.13 + nx * 10, y2 - dy * 0.13 + ny * 10)

    label = relation.verb.upper().replace("_", " ")
    label_w = max(48, min(118, 16 + len(label) * 4.5))
    label_h = 18
    c.setFillColor(LIGHT_GOLD)
    c.setStrokeColor(GOLD)
    c.roundRect(mx - label_w / 2, my - label_h / 2, label_w, label_h, 5, fill=1, stroke=1)
    c.setFillColor(DARK_GREEN)
    size = fit_text(c, label, label_w - 8, FONT_BOLD, 6.8, 5)
    c.setFont(FONT_BOLD, size)
    c.drawCentredString(mx, my - 2.2, label)

    def card(text: str, px: float, py: float) -> None:
        tw = 25
        c.setFillColor(WHITE)
        c.setStrokeColor(LINE)
        c.roundRect(px - tw / 2, py - 7, tw, 14, 4, fill=1, stroke=1)
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 5.8)
        c.drawCentredString(px, py - 2, text)

    card(relation.left_card, *card_left)
    card(relation.right_card, *card_right)


def draw_entity(c: canvas.Canvas, entity: Entity, box: tuple[float, float, float, float], compact: bool) -> None:
    x, y, w, h = box
    c.setFillColor(WHITE)
    c.setStrokeColor(GREEN)
    c.setLineWidth(1.1)
    c.rect(x, y, w, h, fill=1, stroke=1)
    c.setFillColor(GREEN)
    c.rect(x, y + h - 24, w, 24, fill=1, stroke=0)
    c.setFillColor(WHITE)
    name_size = fit_text(c, entity.name, w - 12, FONT_BOLD, 9.2 if not compact else 8)
    c.setFont(FONT_BOLD, name_size)
    c.drawCentredString(x + w / 2, y + h - 16, entity.name)

    line_h = 8.2 if compact else 9
    size = 6.1 if compact else 6.7
    yy = y + h - 36
    for idx, attr in enumerate(entity.attrs):
        if yy < y + 7:
            break
        is_identifier = attr.startswith("#")
        c.setFillColor(DARK_GREEN if is_identifier else INK)
        c.setFont(FONT_BOLD if is_identifier else FONT, size)
        prefix = "ID  " if is_identifier else "- "
        label = attr if len(attr) <= 43 else attr[:41] + "…"
        c.drawString(x + 7, yy, prefix + label)
        if is_identifier:
            width = c.stringWidth(label, FONT_BOLD, size)
            c.setStrokeColor(DARK_GREEN)
            c.setLineWidth(0.4)
            c.line(x + 23, yy - 1.2, x + 23 + width, yy - 1.2)
        yy -= line_h


def external_relations(page: DomainPage, entity_names: set[str]) -> list[Relation]:
    return [
        rel
        for rel in page.relations
        if rel.left not in entity_names or rel.right not in entity_names
    ]


def draw_external_band(c: canvas.Canvas, relations: list[Relation]) -> None:
    if not relations:
        return
    x, y, w, h = 34, 38, PAGE_W - 68, 45
    c.setFillColor(LIGHT_GREEN)
    c.setStrokeColor(GREEN)
    c.roundRect(x, y, w, h, 7, fill=1, stroke=1)
    c.setFillColor(DARK_GREEN)
    c.setFont(FONT_BOLD, 7.3)
    c.drawString(x + 9, y + h - 13, "Associations vers d'autres domaines")
    c.setFont(FONT, 5.7)
    col_w = (w - 18) / 2
    for idx, rel in enumerate(relations[:8]):
        col = idx % 2
        row = idx // 2
        tx = x + 9 + col * col_w
        ty = y + h - 25 - row * 8.2
        text = f"- {rel.left} {rel.left_card} - {rel.verb} - {rel.right_card} {rel.right}"
        size = fit_text(c, text, col_w - 7, FONT, 5.7, 4.8)
        c.setFont(FONT, size)
        c.drawString(tx, ty, text)


def draw_domain(c: canvas.Canvas, page: DomainPage, page_no: int, total: int) -> None:
    page_header(c, page.title, page.subtitle, page_no, total, page.code)
    boxes = layout_entities(page.entities)
    names = set(boxes)
    compact = len(page.entities) > 10
    for entity in page.entities:
        draw_entity(c, entity, boxes[entity.name], compact)

    local = [r for r in page.relations if r.left in names and r.right in names]
    pair_count: dict[tuple[str, str], int] = {}
    row_route_count: dict[int, int] = {}
    for relation in local:
        pair = tuple(sorted((relation.left, relation.right)))
        pair_count[pair] = pair_count.get(pair, 0) + 1
        occurrence = pair_count[pair]
        left_box = boxes[relation.left]
        right_box = boxes[relation.right]
        left_cy = left_box[1] + left_box[3] / 2
        right_cy = right_box[1] + right_box[3] / 2
        if abs(left_cy - right_cy) < 12:
            row_key = round((left_cy + right_cy) / 40)
            row_route_count[row_key] = row_route_count.get(row_key, 0) + 1
            offset = (row_route_count[row_key] - 1) * 16
        else:
            offset = (occurrence - 1) * 16
        draw_association(c, relation, boxes[relation.left], boxes[relation.right], offset)

    draw_external_band(c, external_relations(page, names))
    c.showPage()


def draw_cover(c: canvas.Canvas, total: int) -> None:
    c.setFillColor(PAPER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.rect(0, PAGE_H - 160, PAGE_W, 160, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(0, PAGE_H - 167, PAGE_W, 7, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 31)
    c.drawString(52, PAGE_H - 68, "MCD HAUQE Certif")
    c.setFont(FONT, 16)
    c.drawString(52, PAGE_H - 101, "Modèle conceptuel de données détaillé")
    c.setFont(FONT_BOLD, 11)
    c.drawString(52, PAGE_H - 132, "Notation Merise / PowerDesigner - Entités, associations, attributs et cardinalités")

    c.setFillColor(DARK_GREEN)
    c.setFont(FONT_BOLD, 16)
    c.drawString(52, PAGE_H - 220, "Objet du document")
    c.setFont(FONT, 10)
    text = (
        "Ce livrable présente le schéma conceptuel détaillé de la Base nationale des entreprises certifiées. "
        "Chaque planche affiche les entités du domaine, leurs attributs métier, les identifiants conceptuels, "
        "les associations nommées et les cardinalités portées par les liaisons."
    )
    words = text.split()
    line = ""
    yy = PAGE_H - 250
    for word in words:
        candidate = f"{line} {word}".strip()
        if c.stringWidth(candidate, FONT, 10) > PAGE_W - 104:
            c.drawString(52, yy, line)
            yy -= 16
            line = word
        else:
            line = candidate
    if line:
        c.drawString(52, yy, line)

    c.setFillColor(LIGHT_GREEN)
    c.setStrokeColor(GREEN)
    c.roundRect(52, 145, PAGE_W - 104, 330, 12, fill=1, stroke=1)
    c.setFillColor(DARK_GREEN)
    c.setFont(FONT_BOLD, 15)
    c.drawString(72, 425, "Légende PowerDesigner")

    legend = (
        ("ENTITÉ", "Rectangle vert : objet métier autonome."),
        ("ID", "Attribut identifiant conceptuel, affiché en gras et souligné."),
        ("ASSOCIATION", "Cartouche doré placé sur le trait reliant deux entités."),
        ("(0,1)", "Participation facultative, au maximum une occurrence."),
        ("(1,1)", "Participation obligatoire, exactement une occurrence."),
        ("(0,N)", "Participation facultative, plusieurs occurrences possibles."),
        ("(1,N)", "Participation obligatoire, une ou plusieurs occurrences."),
    )
    y = 405
    for key, description in legend:
        c.setFillColor(GOLD if key == "ASSOCIATION" else GREEN)
        c.roundRect(74, y - 6, 118, 24, 5, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 8)
        c.drawCentredString(133, y + 2, key)
        c.setFillColor(INK)
        c.setFont(FONT, 9)
        c.drawString(210, y + 1, description)
        y -= 38

    c.setFillColor(MUTED)
    c.setFont(FONT, 8.5)
    c.drawString(52, 106, "Version 0.2 - 23 juillet 2026 - Statut : brouillon de conception à soumettre à la revue HAUQE/GFA")
    c.drawString(52, 87, "Source détaillée : MCD_HAUQE_CERTIF.md - Étape suivante : dérivation du MLD puis du MPD PostgreSQL")
    c.drawRightString(PAGE_W - 52, 48, f"Page 1 / {total}")
    c.showPage()


def build_pdf() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    total = len(PAGES) + 1
    c = canvas.Canvas(str(OUTPUT), pagesize=landscape(A3), pageCompression=1)
    c.setTitle("MCD HAUQE Certif - Notation PowerDesigner")
    c.setAuthor("Projet HAUQE Certif")
    c.setSubject("Modèle conceptuel détaillé avec entités, associations et cardinalités")
    draw_cover(c, total)
    for page_no, page in enumerate(PAGES, start=2):
        draw_domain(c, page, page_no, total)
    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()
