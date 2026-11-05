"""Build the animated DITOX AI Rider banner used by the profile README.

Run from the repository root:
    python scripts/make_hero.py
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "ditox-rider-source.png"
OUTPUT = ROOT / "assets" / "ditox-rider.gif"

WIDTH, HEIGHT = 1040, 360
FRAME_COUNT = 24
FRAME_MS = 82

VIOLET = (168, 85, 247)
CYAN = (34, 211, 238)
SOFT_WHITE = (238, 242, 255)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    for directory in (
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/local/share/fonts"),
    ):
        candidate = directory / filename
        if candidate.exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def cover(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    resized = image.resize(
        (round(image.width * scale), round(image.height * scale)),
        Image.Resampling.LANCZOS,
    )
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def build_frame(source: Image.Image, index: int, particles: list[tuple[int, int, int]]) -> Image.Image:
    phase = index / FRAME_COUNT
    wave = math.sin(phase * math.tau)

    # A subtle camera drift keeps the rider alive without distorting the artwork.
    overscan = cover(source, WIDTH + 34, HEIGHT + 14)
    offset_x = round(17 + 11 * wave)
    offset_y = round(7 + 3 * math.sin(phase * math.tau * 2))
    frame = overscan.crop((offset_x, offset_y, offset_x + WIDTH, offset_y + HEIGHT)).convert("RGBA")

    # Pulse cyan/violet bloom around the rider and the roadway.
    bloom = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    glow = ImageDraw.Draw(bloom)
    pulse = round(22 + 14 * (wave + 1) / 2)
    glow.ellipse((655, 95, 1050, 405), fill=(*CYAN, pulse))
    glow.ellipse((560, 10, 1120, 390), fill=(*VIOLET, 18 + pulse // 2))
    bloom = bloom.filter(ImageFilter.GaussianBlur(52))
    frame = Image.alpha_composite(frame, bloom)

    motion = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(motion)

    # Looping speed streaks and digital particles create readable motion in a GIF.
    for n, (start_x, y, length) in enumerate(particles):
        x = (start_x - index * (23 + n % 4) - length) % (WIDTH + 220) - 110
        alpha = 75 + (n % 3) * 36
        color = CYAN if n % 2 == 0 else VIOLET
        draw.line((x, y, x + length, y), fill=(*color, alpha), width=1 + n % 2)

    for n in range(7):
        x = (900 - index * 46 - n * 149) % 990
        y = 245 + (n * 17) % 88
        draw.rounded_rectangle((x, y, x + 4, y + 4), radius=1, fill=(*CYAN, 120))

    # Scanning accent and UI marks on the clean left side.
    scan_x = round(36 + phase * 450)
    draw.line((scan_x, 42, scan_x, 310), fill=(*CYAN, 18), width=1)
    draw.line((48, 297, 445, 297), fill=(*VIOLET, 110), width=2)
    draw.line((48, 297, 118 + round(25 * wave), 297), fill=(*CYAN, 220), width=2)

    frame = Image.alpha_composite(frame, motion)
    draw = ImageDraw.Draw(frame)

    title_font = load_font(59, bold=True)
    label_font = load_font(13, bold=True)
    subtitle_font = load_font(18)

    draw.rounded_rectangle((43, 47, 174, 73), radius=12, fill=(7, 13, 30, 205), outline=(*CYAN, 135))
    draw.ellipse((56, 56, 64, 64), fill=(64, 245, 182, 255))
    draw.text((72, 54), "SYSTEM ONLINE", font=label_font, fill=(171, 255, 232, 255))

    # Layered title gives a restrained cyber-neon edge without sacrificing legibility.
    draw.text((45, 94), "DITOX", font=title_font, fill=(*VIOLET, 145), stroke_width=4, stroke_fill=(20, 8, 45, 120))
    draw.text((48, 90), "DITOX", font=title_font, fill=(*SOFT_WHITE, 255))
    draw.text((51, 166), "AI RIDER", font=subtitle_font, fill=(*CYAN, 255))
    draw.text((51, 198), "AGENTIC AI  /  WEB SYSTEMS", font=label_font, fill=(180, 187, 214, 255))
    draw.text((51, 225), "DESIGN  •  AUTOMATE  •  DEPLOY", font=label_font, fill=(130, 139, 174, 255))

    draw.rounded_rectangle((8, 8, WIDTH - 9, HEIGHT - 9), radius=18, outline=(*VIOLET, 95), width=2)
    return frame.convert("RGB")


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"Missing source artwork: {SOURCE}")

    source = Image.open(SOURCE).convert("RGB")
    random.seed(1029)
    particles = [
        (random.randrange(WIDTH), random.randrange(230, 345), random.randrange(34, 118))
        for _ in range(22)
    ]
    frames = [build_frame(source, index, particles) for index in range(FRAME_COUNT)]

    # A shared adaptive palette keeps the repository asset compact while retaining neon detail.
    palette = frames[0].quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    indexed = [
        frame.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG)
        for frame in frames
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    indexed[0].save(
        OUTPUT,
        save_all=True,
        append_images=indexed[1:],
        duration=FRAME_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Created {OUTPUT} ({OUTPUT.stat().st_size / 1024 / 1024:.2f} MiB)")


if __name__ == "__main__":
    main()
