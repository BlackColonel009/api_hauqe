from pathlib import Path
from PIL import Image, ImageDraw


root = Path(__file__).resolve().parent
pages = sorted((root / "pages").glob("page-*.png"))
assert len(pages) == 55, len(pages)
for start in range(0, len(pages), 6):
    canvas = Image.new("RGB", (1350, 1275), "#dddddd")
    draw = ImageDraw.Draw(canvas)
    for position, page in enumerate(pages[start:start + 6]):
        with Image.open(page) as opened:
            image = opened.convert("RGB")
            image.thumbnail((420, 585))
            x = 20 + (position % 3) * 445
            y = 25 + (position // 3) * 630
            canvas.paste(image, (x, y + 25))
            draw.text((x, y), page.stem, fill="black")
    canvas.save(root / f"contact-final-{start // 6 + 1:02}.png")
