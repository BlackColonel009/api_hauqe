from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
src = root / "tmp" / "guide_v32_word_pngs"
out = root / "tmp" / "guide_v32_word_contacts"
out.mkdir(parents=True, exist_ok=True)
for old in out.glob("contact_*.jpg"):
    old.unlink()

pages = sorted(src.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
assert len(pages) == 53, len(pages)

cols, rows = 3, 2
thumb_w, thumb_h = 500, 650
pad, label_h = 18, 30

for start in range(0, len(pages), cols * rows):
    batch = pages[start:start + cols * rows]
    sheet = Image.new(
        "RGB",
        (cols * (thumb_w + pad) + pad, rows * (thumb_h + label_h + pad) + pad),
        "#d9d9d9",
    )
    draw = ImageDraw.Draw(sheet)
    for offset, page_path in enumerate(batch):
        image = Image.open(page_path).convert("RGB")
        image.thumbnail((thumb_w, thumb_h))
        x = pad + (offset % cols) * (thumb_w + pad)
        y = pad + (offset // cols) * (thumb_h + label_h + pad)
        sheet.paste(image, (x + (thumb_w - image.width) // 2, y))
        draw.text((x + 8, y + thumb_h + 5), f"Page {start + offset + 1}", fill="black")
    sheet.save(out / f"contact_{start + 1:02d}_{start + len(batch):02d}.jpg", quality=90)

print(len(list(out.glob("contact_*.jpg"))))
