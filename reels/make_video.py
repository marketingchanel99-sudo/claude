"""대본 JSON -> 1080x1920 세로 영상(mp4).

장면마다 edge-tts로 음성을 만들고, 배경(이미지 또는 그라데이션)에 천천히 줌을 주고
자막을 얹은 뒤, 모든 장면을 이어 붙인다.

    python -m reels.make_video scripts/example.json -o output/example.mp4
"""
import argparse
import asyncio
import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
PALETTES = [
    ((20, 24, 82), (130, 40, 160)),
    ((10, 70, 90), (20, 160, 140)),
    ((90, 20, 50), (220, 90, 60)),
    ((30, 30, 30), (90, 90, 120)),
]
FONT_CANDIDATES = {
    "Darwin": ["/System/Library/Fonts/AppleSDGothicNeo.ttc"],
    "Windows": ["C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf"],
    "Linux": [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    ],
}


def find_font() -> str:
    env = os.getenv("FONT_PATH")
    if env:
        return env
    for path in FONT_CANDIDATES.get(platform.system(), []):
        if Path(path).exists():
            return path
    raise SystemExit("한글 폰트를 찾지 못했습니다. .env에 FONT_PATH를 지정하세요.")


def ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)]
    )
    return float(out.strip())


def make_background(scene: dict, idx: int, path: Path, base_dir: Path) -> None:
    if scene.get("image"):
        img = Image.open(base_dir / scene["image"]).convert("RGB")
        scale = max(W / img.width, H / img.height)
        img = img.resize((round(img.width * scale), round(img.height * scale)))
        left, top = (img.width - W) // 2, (img.height - H) // 2
        img = img.crop((left, top, left + W, top + H))
        # 자막 가독성을 위해 어둡게
        img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), 0.45)
    else:
        top, bottom = PALETTES[idx % len(PALETTES)]
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)
        for y in range(H):
            t = y / (H - 1)
            draw.line([(0, y), (W, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
    img.save(path)


def wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines = []
    for para in text.split("\n"):
        line = ""
        for word in para.split(" "):
            candidate = f"{line} {word}".strip()
            if font.getlength(candidate) <= max_width:
                line = candidate
                continue
            if line:
                lines.append(line)
            # 공백 없이 긴 한글 단어는 글자 단위로 자른다
            line = ""
            for ch in word:
                if font.getlength(line + ch) > max_width:
                    lines.append(line)
                    line = ""
                line += ch
        lines.append(line)
    return lines


def make_caption(text: str, path: Path, font_path: str) -> None:
    font = ImageFont.truetype(font_path, 88)
    lines = wrap(text, font, W - 160)
    line_h = 88 * 1.35
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    y = (H - line_h * len(lines)) / 2
    for line in lines:
        x = (W - font.getlength(line)) / 2
        draw.text((x, y), line, font=font, fill="white", stroke_width=6, stroke_fill="black")
        y += line_h
    img.save(path)


def silence(text: str, path: Path) -> None:
    # TTS 없이 만들 때: 글자 수에 비례한 길이의 무음 트랙
    seconds = max(2.5, len(text) * 0.12)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-t", f"{seconds:.2f}", "-c:a", "libmp3lame", str(path)],
        check=True,
    )


async def tts(text: str, voice: str, rate: str, path: Path) -> None:
    proxy = os.getenv("HTTPS_PROXY") or os.getenv("https_proxy")
    await edge_tts.Communicate(text.replace("\n", " "), voice, rate=rate, proxy=proxy).save(str(path))


def render_scene(bg: Path, caption: Path, audio: Path, out: Path) -> None:
    duration = ffprobe_duration(audio) + 0.35
    frames = round(duration * FPS)
    vf = (
        f"[0:v]scale={W * 2}:-1,zoompan=z='min(zoom+0.0006,1.12)':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}[bg];"
        "[bg][1:v]overlay=0:0,format=yuv420p[v];[2:a]apad[a]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-i", str(bg), "-loop", "1", "-i", str(caption), "-i", str(audio),
         "-filter_complex", vf, "-map", "[v]", "-map", "[a]", "-t", f"{duration:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", str(out)],
        check=True,
    )


def build(script_path: Path, out_path: Path, use_tts: bool = True) -> Path:
    script = json.loads(script_path.read_text(encoding="utf-8"))
    font_path = find_font()
    voice = script.get("voice", "ko-KR-SunHiNeural")
    rate = script.get("rate", "+0%")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        parts = []
        for i, scene in enumerate(script["scenes"]):
            bg, cap, audio, part = (tmp / f"{i}{ext}" for ext in ("_bg.png", "_cap.png", ".mp3", ".mp4"))
            make_background(scene, i, bg, script_path.parent)
            make_caption(scene["text"], cap, font_path)
            narration = scene.get("narration", scene["text"])
            if use_tts:
                asyncio.run(tts(narration, voice, rate, audio))
            else:
                silence(narration, audio)
            render_scene(bg, cap, audio, part)
            parts.append(part)
            print(f"  장면 {i + 1}/{len(script['scenes'])} 완료")

        concat = tmp / "list.txt"
        concat.write_text("".join(f"file '{p}'\n" for p in parts))
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(concat), "-c", "copy", "-movflags", "+faststart", str(out_path)],
            check=True,
        )
    print(f"영상 생성: {out_path} ({ffprobe_duration(out_path):.1f}초)")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("script", type=Path, help="대본 JSON 경로")
    parser.add_argument("-o", "--out", type=Path, help="출력 mp4 (기본: output/<대본이름>.mp4)")
    parser.add_argument("--no-tts", action="store_true", help="음성 없이 자막만 (무음 트랙)")
    args = parser.parse_args()
    build(args.script, args.out or Path("output") / f"{args.script.stem}.mp4", use_tts=not args.no_tts)


if __name__ == "__main__":
    main()
