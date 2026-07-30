from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, PageBreak, PageTemplate, Paragraph as RLParagraph,
    Spacer, Table, TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Line

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "guide-tableau-de-bord-hauqe.pdf"
STATIC = ROOT / "app" / "static" / "docs" / "guide-tableau-de-bord-hauqe.pdf"
TMP = ROOT / "tmp" / "pdfs"
TMP.mkdir(parents=True, exist_ok=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
STATIC.parent.mkdir(parents=True, exist_ok=True)

GREEN = colors.HexColor("#087658")
DARK = colors.HexColor("#073D32")
PALE = colors.HexColor("#EAF7F3")
INK = colors.HexColor("#17211D")
MUTED = colors.HexColor("#60706A")
LINE = colors.HexColor("#DDE7E3")
ORANGE = colors.HexColor("#E49B36")
RED = colors.HexColor("#C6504B")
BLUE = colors.HexColor("#4B82D3")


def fr_text(text):
    replacements = {
        "A quoi": "À quoi", "metier": "métier", "reperer": "repérer",
        "expiration": "expiration", "competente": "compétente",
        "vise": "visé", "autorises": "autorisés", "a consulter": "à consulter",
        "operationnel": "opérationnel", "Periode": "Période",
        "periode": "période", "Echeances": "Échéances", "echeances": "échéances",
        "certificats": "certificats", "a 90": "à 90", "Selectionnez": "Sélectionnez",
        "region": "région", "perimetre": "périmètre", "Reinitialisez": "Réinitialisez",
        "detaille": "détaillé", "Consultez d'abord": "Consultez d’abord",
        "priorites": "priorités", "telecharge": "télécharge", "calcule": "calculé",
        "Elements": "Éléments", "Element": "Élément", "Moyenne": "Moyenne",
        "etre": "être", "deja": "déjà", "Activite": "Activité",
        "interpretation": "interprétation", "controle": "contrôle",
        "verifiez": "vérifiez", "conformite": "conformité", "recentes": "récentes",
        "Regle": "Règle", "anormal": "anormal", "associe": "associé",
        "synchronisation": "synchronisation", "securite": "sécurité",
        "depend": "dépend", "necessitent": "nécessitent", "peut donc etre": "peut donc être",
        "renouvellements": "renouvellements", "eventuellement": "éventuellement",
        "priorite": "priorité", "affectation": "affectation", "generation": "génération",
        "Conservez": "Conservez", "reflexe": "réflexe", "decision": "décision",
        "confirmee": "confirmée", "approuvee": "approuvée",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


def Paragraph(text, *args, **kwargs):
    return RLParagraph(fr_text(text), *args, **kwargs)


def dashboard_diagram():
    d = Drawing(1100, 620)
    d.add(Rect(0, 0, 1100, 620, fillColor=colors.HexColor("#F3F6F5"), strokeColor=None))
    d.add(Rect(0, 0, 205, 620, fillColor=DARK, strokeColor=None))
    d.add(String(32, 575, "HQ  HAUQE", fontName="Helvetica-Bold", fontSize=21, fillColor=colors.white))
    for i, name in enumerate(["Pilotage", "Tableau de bord", "Alertes", "Echeances", "Registre national", "Analyse"]):
        d.add(String(28 if i in (0, 4, 5) else 42, 525-i*42, name, fontName="Helvetica-Bold" if i in (0, 4, 5) else "Helvetica", fontSize=11, fillColor=colors.HexColor("#BFD8D1") if i in (0, 4, 5) else colors.white))
    d.add(String(245, 574, "TABLEAU DE BORD - VUE NATIONALE", fontName="Helvetica-Bold", fontSize=20, fillColor=INK))
    d.add(String(245, 548, "Filtres, indicateurs, echeances et actions prioritaires", fontName="Helvetica", fontSize=11, fillColor=MUTED))
    d.add(Rect(245, 492, 815, 42, rx=9, fillColor=colors.white, strokeColor=LINE))
    for i, name in enumerate(["Periode", "Region", "Secteur", "Norme", "Organisme"]):
        x = 260+i*150
        d.add(String(x, 516, name, fontName="Helvetica-Bold", fontSize=9, fillColor=MUTED))
        d.add(Rect(x, 498, 130, 14, rx=3, fillColor=PALE, strokeColor=None))
    for i, (label, value, color) in enumerate([("Entreprises", "247", GREEN), ("Certifications", "189", BLUE), ("A echeance", "28", ORANGE), ("Alertes", "9", RED)]):
        x = 245+i*204
        d.add(Rect(x, 405, 188, 70, rx=10, fillColor=colors.white, strokeColor=LINE))
        d.add(Circle(x+25, 440, 12, fillColor=color, strokeColor=None))
        d.add(String(x+47, 447, label, fontName="Helvetica", fontSize=9, fillColor=MUTED))
        d.add(String(x+47, 420, value, fontName="Helvetica-Bold", fontSize=21, fillColor=INK))
    d.add(Rect(245, 205, 500, 180, rx=10, fillColor=colors.white, strokeColor=LINE))
    d.add(String(265, 360, "Etat des certifications", fontName="Helvetica-Bold", fontSize=13, fillColor=INK))
    d.add(Circle(370, 285, 65, fillColor=None, strokeColor=GREEN, strokeWidth=24))
    for i, (c, t) in enumerate([(GREEN, "Actives"), (ORANGE, "A renouveler"), (RED, "Expirees")]):
        d.add(Circle(485, 325-i*38, 6, fillColor=c, strokeColor=None))
        d.add(String(500, 320-i*38, t, fontName="Helvetica", fontSize=10, fillColor=INK))
    d.add(Rect(762, 205, 298, 180, rx=10, fillColor=colors.white, strokeColor=LINE))
    d.add(String(782, 360, "Echeances a surveiller", fontName="Helvetica-Bold", fontSize=13, fillColor=INK))
    for i, (name, c) in enumerate([("Expiration < 30 jours", RED), ("Entre 31 et 90 jours", ORANGE), ("Entre 91 et 180 jours", BLUE)]):
        d.add(Rect(785, 316-i*42, 14, 14, rx=3, fillColor=c, strokeColor=None))
        d.add(String(810, 317-i*42, name, fontName="Helvetica", fontSize=9, fillColor=INK))
    d.add(Rect(245, 38, 500, 147, rx=10, fillColor=colors.white, strokeColor=LINE))
    d.add(String(265, 160, "Activite mensuelle", fontName="Helvetica-Bold", fontSize=13, fillColor=INK))
    pts = [(280,75),(350,95),(420,88),(490,125),(560,112),(630,145),(710,135)]
    for a,b in zip(pts,pts[1:]): d.add(Line(a[0],a[1],b[0],b[1],strokeColor=GREEN,strokeWidth=3))
    d.add(Rect(762, 38, 298, 147, rx=10, fillColor=colors.white, strokeColor=LINE))
    d.add(String(782, 160, "Actions d'urgence", fontName="Helvetica-Bold", fontSize=13, fillColor=INK))
    for i in range(3):
        d.add(Circle(790, 125-i*34, 8, fillColor=RED if i == 0 else ORANGE, strokeColor=None))
        d.add(Rect(810, 120-i*34, 210, 8, rx=3, fillColor=colors.HexColor("#DDE7E3"), strokeColor=None))
    return d


def flow_diagram():
    d = Drawing(1100, 350)
    d.add(Rect(0, 0, 1100, 350, fillColor=colors.white, strokeColor=None))
    steps = [
        ("1", "Choisir la periode", "7 a 90 jours"),
        ("2", "Affiner les filtres", "Zone, secteur, norme"),
        ("3", "Lire les indicateurs", "Volumes et tendances"),
        ("4", "Traiter les urgences", "Alertes et echeances"),
        ("5", "Exporter ou ouvrir", "CSV et registres"),
    ]
    for i, (n, title, sub) in enumerate(steps):
        x = 25+i*215
        d.add(Rect(x, 105, 180, 130, rx=16, fillColor=PALE if i % 2 == 0 else colors.HexColor("#F7F9F8"), strokeColor=LINE))
        d.add(Circle(x+35, 205, 18, fillColor=GREEN, strokeColor=None))
        d.add(String(x+30, 199, n, fontName="Helvetica-Bold", fontSize=13, fillColor=colors.white))
        d.add(String(x+18, 165, title, fontName="Helvetica-Bold", fontSize=12, fillColor=INK))
        d.add(String(x+18, 138, sub, fontName="Helvetica", fontSize=9, fillColor=MUTED))
        if i < 4:
            d.add(Line(x+182, 170, x+212, 170, strokeColor=GREEN, strokeWidth=3))
    return d


def fit_drawing(drawing, width):
    factor = width / drawing.width
    drawing.scale(factor, factor)
    drawing.width *= factor
    drawing.height *= factor
    return drawing


dashboard_img = fit_drawing(dashboard_diagram(), 174*mm)
flow_img = fit_drawing(flow_diagram(), 174*mm)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleWhite", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=25, leading=30, textColor=colors.white, alignment=TA_CENTER))
styles.add(ParagraphStyle(name="H1x", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=19, leading=24, textColor=DARK, spaceAfter=10))
styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=GREEN, spaceBefore=8, spaceAfter=6))
styles.add(ParagraphStyle(name="Bodyx", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.4, leading=14, textColor=INK, spaceAfter=6))
styles.add(ParagraphStyle(name="Smallx", parent=styles["BodyText"], fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=9.2, leading=14, textColor=DARK, backColor=PALE, borderColor=colors.HexColor("#9FD5C5"), borderWidth=.6, borderPadding=9, spaceBefore=7, spaceAfter=9))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE); canvas.line(18*mm, 13*mm, 192*mm, 13*mm)
    canvas.setFont("Helvetica", 7); canvas.setFillColor(MUTED)
    canvas.drawString(18*mm, 8*mm, "HAUQE Certif - Guide utilisateur du Tableau de bord")
    canvas.drawRightString(192*mm, 8*mm, f"Page {doc.page}")
    canvas.restoreState()


doc = BaseDocTemplate(str(OUT), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=17*mm, bottomMargin=18*mm, title="Guide utilisateur - Tableau de bord HAUQE")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
doc.addPageTemplates(PageTemplate(id="guide", frames=frame, onPage=footer))

story = []
cover = Table([[Paragraph("GUIDE UTILISATEUR", styles["TitleWhite"])], [Paragraph("Tableau de bord national HAUQE Certif", ParagraphStyle("sub", parent=styles["TitleWhite"], fontSize=16, leading=21))], [Spacer(1, 8*mm)], [Paragraph("Comprendre les indicateurs, filtrer la vue, traiter les priorites et exporter les resultats.", ParagraphStyle("covbody", parent=styles["Bodyx"], textColor=colors.white, alignment=TA_CENTER, fontSize=11, leading=17))]], colWidths=[174*mm], rowHeights=[32*mm, 27*mm, 12*mm, 40*mm])
cover.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),DARK),("BOX",(0,0),(-1,-1),0,DARK),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),15*mm),("RIGHTPADDING",(0,0),(-1,-1),15*mm)]))
story += [Spacer(1, 28*mm), cover, Spacer(1, 16*mm), Paragraph("Public vise : agents HAUQE autorises a consulter le pilotage operationnel.", styles["Callout"]), Paragraph("Version du guide : 1.0 - Juillet 2026", styles["Smallx"]), PageBreak()]

story += [Paragraph("1. A quoi sert cette page ?", styles["H1x"]), Paragraph("Le Tableau de bord rassemble les informations essentielles de la plateforme. Il ne remplace pas les registres metier : il aide a reperer rapidement une tendance, une expiration ou une action urgente, puis dirige l'agent vers la page competente.", styles["Bodyx"]), dashboard_img, Spacer(1, 4*mm)]
data = [["Zone", "Utilisation"], ["Filtres", "Limiter tous les indicateurs au meme perimetre."], ["Cartes d'indicateurs", "Lire les volumes principaux et ouvrir le registre associe."], ["Etat des certifications", "Comparer les statuts presents dans le registre."], ["Echeances", "Identifier les certificats proches de l'expiration."], ["Actions d'urgence", "Ouvrir les alertes qui demandent une intervention."], ["Table recente", "Acceder aux certifications nouvellement mises a jour."]]
data = [[fr_text(cell) for cell in row] for row in data]
t = Table(data, colWidths=[48*mm,126*mm], repeatRows=1)
t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTNAME",(0,1),(0,-1),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.2),("LEADING",(0,0),(-1,-1),11),("GRID",(0,0),(-1,-1),.4,LINE),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F7F9F8")]),("PADDING",(0,0),(-1,-1),6)]))
story += [t, PageBreak()]

story += [Paragraph("2. Parcours recommande", styles["H1x"]), Paragraph("Pour eviter une mauvaise interpretation, appliquez toujours les filtres avant de commenter les chiffres.", styles["Bodyx"]), flow_img, Paragraph("Etape 1 - Choisir la periode", styles["H2x"]), Paragraph("Selectionnez 7, 30, 60 ou 90 jours. La periode influence les activites recentes et les actions affichees.", styles["Bodyx"]), Paragraph("Etape 2 - Affiner le perimetre", styles["H2x"]), Paragraph("La region et le secteur proviennent du registre des entreprises. La norme et l'organisme proviennent du registre des certifications. Reinitialisez les filtres pour revenir a la vue nationale.", styles["Bodyx"]), Paragraph("Etape 3 - Examiner les indicateurs", styles["H2x"]), Paragraph("Un indicateur est un signal de pilotage. Cliquez sur une carte interactive pour ouvrir le registre detaille qui justifie la valeur.", styles["Bodyx"]), Paragraph("Etape 4 - Traiter les urgences", styles["H2x"]), Paragraph("Consultez d'abord les expirations les plus proches et les alertes critiques. Utilisez les liens Calendrier complet et Centre des alertes pour poursuivre le traitement.", styles["Bodyx"]), Paragraph("Etape 5 - Exporter", styles["H2x"]), Paragraph("Le bouton Exporter telecharge un fichier CSV calcule par le serveur avec exactement les filtres actifs.", styles["Bodyx"]), PageBreak()]

story += [Paragraph("3. Lire correctement les informations", styles["H1x"])]
tips = [["Element", "Lecture correcte", "Erreur a eviter"], ["INFC moyen", "Moyenne du dernier calcul disponible dans le perimetre.", "Le confondre avec la classification entreprise ou le SNCC."], ["Certificats a 90 jours", "Certificats dont l'expiration approche.", "Supposer qu'ils sont deja expires."], ["Activite mensuelle", "Evolution des enregistrements sur six mois.", "L'interpreter comme une mesure de conformite."], ["Actions d'urgence", "Alertes actives et echeances critiques.", "Les considerer comme deja traitees."], ["Dernieres mises a jour", "Operations recentes du registre.", "Les prendre pour la liste complete."]]
tips = [[fr_text(cell) for cell in row] for row in tips]
t2 = Table(tips, colWidths=[35*mm,78*mm,61*mm], repeatRows=1)
t2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),("LEADING",(0,0),(-1,-1),11),("GRID",(0,0),(-1,-1),.4,LINE),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F7F9F8")]),("PADDING",(0,0),(-1,-1),6)]))
story += [t2, Spacer(1, 5*mm), Paragraph("Regle de controle", styles["H2x"]), Paragraph("Si un chiffre semble anormal, ouvrez le registre associe et verifiez le perimetre, la periode, les statuts et la date de synchronisation avant de signaler une anomalie.", styles["Callout"]), Paragraph("Droits et securite", styles["H2x"]), Paragraph("Les boutons et informations visibles dependent des permissions du compte. L'export exige le droit de pilotage operationnel. Une absence de bouton peut donc etre normale.", styles["Bodyx"]), PageBreak()]

story += [Paragraph("4. Cas pratiques et depannage", styles["H1x"]), Paragraph("Cas 1 - Rechercher les renouvellements urgents", styles["H2x"]), Paragraph("Choisissez une periode, filtrez eventuellement par region ou organisme, consultez Echeances a surveiller, puis ouvrez le calendrier complet.", styles["Bodyx"]), Paragraph("Cas 2 - Analyser une hausse d'alertes", styles["H2x"]), Paragraph("Lisez le compteur Actions d'urgence, ouvrez le centre des alertes et verifiez la priorite, l'affectation et l'echeance de chaque action.", styles["Bodyx"]), Paragraph("Cas 3 - Produire une situation de pilotage", styles["H2x"]), Paragraph("Appliquez les filtres, controlez le libelle de periode et la date de generation, puis utilisez Exporter. Conservez le fichier avec la periode et le perimetre dans son nom.", styles["Bodyx"])]
faq = [["Situation", "Action conseillee"], ["Les filtres restent en chargement", "Verifier la connexion et actualiser la page. Si le probleme persiste, signaler l'API des referentiels."], ["Le tableau affiche un etat vide", "Verifier les filtres. Une combinaison peut ne contenir aucune donnee."], ["Un indicateur differe du registre", "Comparer la periode, le statut et la date de mise a jour avant de conclure."], ["L'export ne demarre pas", "Verifier la permission et attendre la fin du chargement serveur."], ["Le tableau public est vide", "Une configuration et une demande de publication approuvee sont requises."]]
faq = [[fr_text(cell) for cell in row] for row in faq]
t3 = Table(faq, colWidths=[58*mm,116*mm], repeatRows=1)
t3.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8.2),("LEADING",(0,0),(-1,-1),11),("GRID",(0,0),(-1,-1),.4,LINE),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F7F9F8")]),("PADDING",(0,0),(-1,-1),6)]))
story += [Spacer(1, 4*mm), t3, Spacer(1, 6*mm), Paragraph("Bon reflexe : le Tableau de bord sert a orienter l'action. Toute decision doit etre confirmee dans le dossier ou le registre metier correspondant.", styles["Callout"])]

doc.build(story)
STATIC.write_bytes(OUT.read_bytes())
print(OUT)
print(STATIC)
