"""Create an original, vertical Maison Douce MP4 without external media assets.

Run: python scripts/create_video.py
Requires Pillow and ffmpeg. Saves outputs/maison_douce_test.mp4.
"""
from pathlib import Path
import math
import subprocess
import shutil
import textwrap

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs"
TEMP = OUTPUT / "frames"
SIZE = (720, 1280)
SLIDE_SECONDS = 4

SLIDES = [
    ("MAISON DOUCE", "3 astuces pour un salon plus chaleureux", "Déco cozy · Petit budget"),
    ("01 / LUMIÈRE", "Préfère plusieurs lampes à une seule lumière de plafond.", "Une ambiance plus douce, le soir"),
    ("02 / MATIÈRES", "Ajoute un plaid texturé et deux coussins de tons naturels.", "Des détails simples qui changent tout"),
    ("03 / DÉTAILS", "Associe une plante, une matière boisée et un coin lecture.", "Enregistre cette idée pour plus tard"),
]


def font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in paths:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def wrap(text, draw, typeface, max_width):
    words = text.split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if line and draw.textbbox((0, 0), test, font=typeface)[2] > max_width:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def render_slide(index, eyebrow, title, footer):
    width, height = SIZE
    image = Image.new("RGB", SIZE)
    pixels = image.load()
    for y in range(height):
        t = y / height
        base = (241 - int(24 * t), 229 - int(24 * t), 211 - int(19 * t))
        for x in range(width):
            glow = max(0, 1 - math.hypot((x - 565) / 580, (y - 330) / 750))
            pixels[x, y] = tuple(min(255, round(c + 12 * glow)) for c in base)
    draw = ImageDraw.Draw(image)
    draw.ellipse((430, 65, 960, 590), fill=(224, 202, 177), outline=(207, 174, 143), width=4)
    draw.ellipse((-230, 1000, 380, 1610), fill=(223, 206, 183))
    draw.rounded_rectangle((68, 210, 652, 990), radius=44, fill=(249, 243, 232), outline=(209, 187, 163), width=3)
    draw.text((112, 293), eyebrow, fill=(132, 97, 69), font=font(27, True), spacing=8)
    title_font = font(50 if index else 48, True)
    lines = wrap(title, draw, title_font, 480)
    line_height = 77
    top = 430 - (len(lines) - 2) * 21
    for j, line in enumerate(lines):
        draw.text((106, top + j * line_height), line, fill=(67, 53, 45), font=title_font)
    draw.line((107, 795, 300, 795), fill=(190, 140, 109), width=6)
    footer_font = font(25)
    for i, line in enumerate(wrap(footer, draw, footer_font, 470)):
        draw.text((107, 839 + i * 39), line, fill=(113, 90, 77), font=footer_font)
    draw.text((91, 1130), "@maisondouce.deco", fill=(95, 78, 64), font=font(26, True))
    return image


def main():
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is required to create the MP4")
    TEMP.mkdir(parents=True, exist_ok=True)
    images = []
    for i, content in enumerate(SLIDES):
        path = TEMP / f"slide_{i:02d}.png"
        render_slide(i, *content).save(path)
        images.append(path)
    playlist = TEMP / "slides.txt"
    with playlist.open("w", encoding="utf-8") as output:
        for path in images:
            output.write(f"file '{path.name}'\n")
            output.write(f"duration {SLIDE_SECONDS}\n")
        output.write(f"file '{images[-1].name}'\n")
    target = OUTPUT / "maison_douce_test.mp4"
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(playlist),
        "-vf", "fps=25,format=yuv420p",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
        "-movflags", "+faststart", str(target),
    ]
    subprocess.run(cmd, check=True, cwd=TEMP)
    print(f"Video created: {target} ({target.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
