from pathlib import Path
from PIL import Image, ImageDraw

root = Path("tmp/pdfs/dictionnaire-donnees")
pages = sorted(root.glob("page-*.png"))
thumb_w, thumb_h = 420, 297
cols, rows = 3, 4
for batch_start in range(0, len(pages), cols * rows):
    batch = pages[batch_start:batch_start + cols * rows]
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + 24)), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, path in enumerate(batch):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_w - 8, thumb_h - 8))
        x = (idx % cols) * thumb_w + 4
        y = (idx // cols) * (thumb_h + 24) + 4
        sheet.paste(image, (x, y))
        draw.text((x, y + thumb_h), path.stem, fill="black")
    output = root / f"contact-{batch_start // (cols * rows) + 1:02d}.png"
    sheet.save(output)
    print(output)
