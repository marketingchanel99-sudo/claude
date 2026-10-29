"""스타일 가이드(docs/STYLE_GUIDE.md)를 코드로 옮긴 것. 오버레이 PNG(투명 배경)를 그린다.

자막의 강조 단어는 대괄호로 표시한다: "This is [#1] at Olive Young"
"""
import os
import platform
import re
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920

CORAL = (255, 107, 74)
CREAM = (255, 244, 230)
INK = (24, 24, 24)
WHITE = (255, 255, 255)

# 안전 영역
SAFE_L, SAFE_R = 60, 930  # 본문 자막 (오른쪽 버튼 회피)
HOOK_L, HOOK_R = 60, 1020  # 훅 자막 (버튼보다 위쪽이라 넓게 쓴다)

SERIES_LABELS = {
    "items": "KOREAN SECRET",
    "explained": "WHY KOREANS…?",
    "tips": "SEOUL SURVIVAL",
    "ranked": "RANKED",
    "brand": "KOREAN SECRET",
}

FONT_CANDIDATES = {
    "black": [
        "/usr/share/fonts/opentype/inter/Inter-Black.otf",
        "/Library/Fonts/Inter-Black.otf",
        "C:/Windows/Fonts/Inter-Black.otf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Black.ttf",
    ],
    "extrabold": [
        "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
        "/Library/Fonts/Inter-ExtraBold.otf",
        "C:/Windows/Fonts/Inter-ExtraBold.otf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ],
}


@lru_cache
def font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    env = os.getenv(f"FONT_{weight.upper()}")
    for path in [env] if env else FONT_CANDIDATES[weight]:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size)
    raise SystemExit(
        f"{weight} 폰트를 찾지 못했습니다 ({platform.system()}). Inter 폰트를 설치하거나 .env에 FONT_{weight.upper()}를 지정하세요."
    )


def tokens(text: str) -> list[tuple[str, bool]]:
    """'This is [#1] at Olive Young' -> [('This', False), ('is', False), ('#1', True), ...]"""
    out = []
    for part in re.split(r"(\[[^\]]+\])", text):
        if part.startswith("[") and part.endswith("]"):
            out += [(w, True) for w in part[1:-1].split()]
        else:
            out += [(w, False) for w in part.split()]
    return out


def wrap(words: list[tuple[str, bool]], f: ImageFont.FreeTypeFont, max_w: float) -> list[list[tuple[str, bool]]]:
    gap = f.size * 0.28
    lines, line, width = [], [], 0.0
    for word in words:
        w = f.getlength(word[0])
        if line and width + gap + w > max_w:
            lines.append(line)
            line, width = [], 0.0
        width += (gap if line else 0) + w
        line.append(word)
    if line:
        lines.append(line)
    return lines


def balanced(words, f, max_w, max_lines):
    """줄 수를 넘으면 None. 2줄이면 위아래 길이가 비슷하게 나눈다."""
    lines = wrap(words, f, max_w)
    if len(lines) > max_lines:
        return None
    if len(lines) == 2 and len(words) > 2:
        gap = f.size * 0.28
        best = None
        for i in range(1, len(words)):
            a, b = words[:i], words[i:]
            wa = sum(f.getlength(t) for t, _ in a) + gap * (len(a) - 1)
            wb = sum(f.getlength(t) for t, _ in b) + gap * (len(b) - 1)
            if wa <= max_w and wb <= max_w and (best is None or abs(wa - wb) < best[0]):
                best = (abs(wa - wb), [a, b])
        if best:
            lines = best[1]
    return lines


def fit(words, weight, sizes, max_w, max_lines):
    for size in sizes:
        f = font(weight, size)
        lines = balanced(words, f, max_w, max_lines)
        if lines:
            return f, lines
    f = font(weight, sizes[-1])
    return f, wrap(words, f, max_w)[:max_lines]


def draw_label(d: ImageDraw.ImageDraw, text: str) -> None:
    """① 시리즈 라벨 (A안): 흰 배지 + 코랄 세로선."""
    f = font("extrabold", 40)
    x0, y0 = 60, 270
    d.rounded_rectangle([x0, y0, x0 + f.getlength(text) + 80, y0 + 76], 18, fill=WHITE)
    d.rounded_rectangle([x0 + 22, y0 + 18, x0 + 32, y0 + 58], 4, fill=CORAL)
    d.text((x0 + 50, y0 + 15), text, font=f, fill=INK)


def draw_hook(d: ImageDraw.ImageDraw, text: str) -> None:
    """② 훅 자막 (C안): 코랄 대형 글씨 + 크림 테두리, 최대 2줄."""
    words = [(w, False) for w, _ in tokens(text)]
    f, lines = fit(words, "black", [108, 100, 92, 84], HOOK_R - HOOK_L, 2)
    for i, line in enumerate(lines):
        s = " ".join(t for t, _ in line)
        x = (HOOK_L + HOOK_R - f.getlength(s)) / 2
        d.text((x, 400 + i * f.size * 1.13), s, font=f, fill=CORAL, stroke_width=10, stroke_fill=CREAM)


def draw_caption(d: ImageDraw.ImageDraw, text: str) -> bool:
    """③ 본문 자막 (C안): 흰 글씨 + 잉크 테두리, 강조 단어는 코랄 배경. 강조가 있으면 True."""
    words = tokens(text)
    f, lines = fit(words, "black", [80, 74, 68, 62], SAFE_R - SAFE_L, 2)
    gap = f.size * 0.28
    line_h = f.size * 1.25
    for i, line in enumerate(lines):
        width = sum(f.getlength(t) for t, _ in line) + gap * (len(line) - 1)
        x = (SAFE_L + SAFE_R - width) / 2
        y = 1160 + i * line_h
        for t, hi in line:
            if hi:
                pad = 16
                d.rounded_rectangle([x - pad, y - 6, x + f.getlength(t) + pad, y + f.size * 1.12], 16, fill=CORAL)
            d.text((x, y), t, font=f, fill=WHITE, stroke_width=8, stroke_fill=INK)
            x += f.getlength(t) + gap
    return any(hi for _, hi in words)


def overlay(label: str | None, hook: str | None, caption: str | None) -> tuple[Image.Image, bool]:
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if label:
        draw_label(d, label)
    if hook:
        draw_hook(d, hook)
    highlighted = draw_caption(d, caption) if caption else False
    return img, highlighted
