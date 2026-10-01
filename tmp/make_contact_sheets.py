from pathlib import Path
from PIL import Image, ImageDraw

src = Path("tmp/guide_v3_review_v32/pages")
out = Path("tmp/guide_v3_review_v32/contact_sheets")
out.mkdir(parents=True, exist_ok=True)
pages = sorted(src.glob("page-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
assert len(pages) == 54, len(pages)

cols, rows = 3, 2
thumb_w, thumb_h = 510, 660
pad, label_h = 18, 32

for start in range(0, len(pages), cols * rows):
    batch = pages[start:start + cols * rows]
    sheet = Image.new("RGB", (cols * (thumb_w + pad) + pad, rows * (thumb_h + label_h + pad) + pad), "#d9d9d9")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(batch):
        img = Image.open(path).convert("RGB")
        img.thumbnail((thumb_w, thumb_h))
        x = pad + (i % cols) * (thumb_w + pad)
        y = pad + (i // cols) * (thumb_h + label_h + pad)
        px = x + (thumb_w - img.width) // 2
        sheet.paste(img, (px, y))
        draw.text((x + 8, y + thumb_h + 6), f"Page {start + i + 1}", fill="black")
    sheet.save(out / f"contact_{start + 1:02d}_{start + len(batch):02d}.jpg", quality=88)
print(len(list(out.glob('contact_*.jpg'))))
