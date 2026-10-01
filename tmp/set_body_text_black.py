from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.dml.color import RGBColor


root = Path(__file__).resolve().parents[1]
path = root / "output" / "docx" / "Guide_global_utilisation_SNGSC_HAUQE_v3_mis_a_jour.docx"

doc = Document(path)

# Le corps du guide repose sur le style Normal. Les titres et repères
# institutionnels disposent déjà de styles ou de couleurs directes distincts.
doc.styles["Normal"].font.color.rgb = RGBColor(0x00, 0x00, 0x00)

doc.save(path)

with ZipFile(path) as package:
    assert package.testzip() is None

print(path)
