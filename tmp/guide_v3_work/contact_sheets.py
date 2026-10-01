from pathlib import Path
from PIL import Image, ImageDraw

root = Path(r"C:\Users\hp\Documents\APK WEB Projets R.1.3.5 et R1.4.3\tmp\guide_v3_work")
pages = sorted(root.glob("page-*.png"))
assert len(pages) == 54, len(pages)
for start in range(0, len(pages), 6):
    canvas = Image.new("RGB", (1350, 1275), "#dddddd")
    draw = ImageDraw.Draw(canvas)
    for position, page in enumerate(pages[start:start + 6]):
        with Image.open(page) as opened:
            im = opened.convert("RGB")
            im.thumbnail((420, 585))
            x = 20 + (position % 3) * 445
            y = 25 + (position // 3) * 630
            canvas.paste(im, (x, y + 25))
            draw.text((x, y), page.stem, fill="black")
    canvas.save(root / f"contact-{start // 6 + 1:02}.png")
