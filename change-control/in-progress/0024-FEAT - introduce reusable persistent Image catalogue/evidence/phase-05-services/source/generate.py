"""Synthetic fixtures; optional regeneration with Pillow, never required by Gradle."""
from pathlib import Path
from PIL import Image

directory = Path(__file__).resolve().parent
image = Image.new("RGB", (16, 12))
for y in range(12):
    for x in range(16):
        image.putpixel((x, y), (x * 16, y * 20, (x + y) * 8))
for name, format in [("sample.jpg", "JPEG"), ("sample.png", "PNG"), ("sample.gif", "GIF"), ("sample.webp", "WEBP")]:
    image.save(directory / name, format=format)
image.save(directory / "lossless.webp", format="WEBP", lossless=True)
for format in ["GIF", "WEBP"]:
    image.save(directory / ("animated." + format.lower()), format=format, save_all=True,
               append_images=[Image.new("RGB", (16, 12), "red")], duration=100, loop=0)
