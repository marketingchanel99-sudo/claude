"""편집 템플릿 렌더러: script.json v2 + 장면 재료 -> final.mp4 (1080x1920, 스타일 가이드 적용).

장면마다 재료를 `scenes[].asset`(영상 또는 이미지)과 `scenes[].audio`(내레이션)에 적는다.
- asset이 영상이면 화면을 꽉 채우게 잘라 쓰고, 오디오가 있으면 그 소리(지우 목소리)를 쓴다.
- asset이 이미지면 천천히 줌인한다.
- asset이 없으면 회색 자리 표시 화면으로 렌더링한다 (미리보기용).
- audio가 있으면 그 파일을 내레이션으로 쓴다 (영상 소리보다 우선).

첫 장면: 시리즈 라벨 + 훅 자막(caption) + pop 효과음.
나머지: 시리즈 라벨 + 본문 자막(caption, [강조 단어]) + 강조가 있으면 swish 효과음.
배경음은 --bgm으로 넣는다 (목소리보다 작게).

    python -m reels.render episodes/<id>/script.json
    python -m reels.render episodes/<id>/script.json --bgm assets/bgm/signature.mp3 -o out.mp4
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from reels.style import SERIES_LABELS, H, W, overlay

FPS = 30
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv"}
BGM_VOLUME = 0.08  # 약 -22dB
SFX_VOLUME = 0.6


def run(*args: str) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def probe(path: Path, entries: str, stream: str | None = None) -> str:
    cmd = ["ffprobe", "-v", "error", "-show_entries", entries, "-of", "csv=p=0"]
    if stream:
        cmd += ["-select_streams", stream]
    return subprocess.check_output([*cmd, str(path)]).decode().strip()


def duration_of(path: Path) -> float:
    return float(probe(path, "format=duration"))


def has_audio(path: Path) -> bool:
    return bool(probe(path, "stream=codec_type", "a"))


def make_sfx(tmp: Path) -> dict[str, Path]:
    """저작권 걱정 없는 효과음을 직접 합성한다."""
    pop, swish = tmp / "pop.wav", tmp / "swish.wav"
    run("-f", "lavfi", "-i", "sine=f=900:d=0.12", "-af",
        "asetrate=44100*1.0,afade=t=out:st=0.02:d=0.1,vibrato=f=30:d=0.4,volume=1.5", "-ar", "44100", str(pop))
    run("-f", "lavfi", "-i", "anoisesrc=d=0.35:c=pink:a=0.6", "-af",
        "highpass=f=1200,lowpass=f=6000,afade=t=in:d=0.15,afade=t=out:st=0.15:d=0.2", "-ar", "44100", str(swish))
    return {"pop": pop, "swish": swish}


def fill_filter() -> str:
    return f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"


def render_scene(scene: dict, index: int, label: str, base: Path, tmp: Path) -> tuple[Path, float, bool]:
    duration = float(scene["duration"])
    is_hook = index == 0
    ov_img, highlighted = overlay(label, scene.get("caption") if is_hook else None,
                                  None if is_hook else scene.get("caption"))
    ov = tmp / f"ov{index}.png"
    ov_img.save(ov)

    asset = base / scene["asset"] if scene.get("asset") else None
    narration = base / scene["audio"] if scene.get("audio") else None
    if asset and not asset.exists():
        raise SystemExit(f"장면 {scene.get('id', index + 1)}: 재료 파일이 없음 {asset}")
    if narration and not narration.exists():
        raise SystemExit(f"장면 {scene.get('id', index + 1)}: 음성 파일이 없음 {narration}")

    frames = round(duration * FPS)
    inputs: list[str] = []
    if asset and asset.suffix.lower() in VIDEO_EXT:
        inputs += ["-i", str(asset)]
        # 클립이 장면보다 짧으면 마지막 프레임으로 채운다
        video = f"[0:v]{fill_filter()},fps={FPS},tpad=stop_mode=clone:stop_duration={duration}[bg]"
        clip_audio = has_audio(asset)
    elif asset:
        inputs += ["-loop", "1", "-i", str(asset)]
        video = (f"[0:v]scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
                 f"zoompan=z='min(zoom+0.0007,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                 f":d={frames}:s={W}x{H}:fps={FPS},setsar=1[bg]")
        clip_audio = False
    else:
        inputs += ["-f", "lavfi", "-i", f"color=c=0x8a8178:s={W}x{H}:r={FPS}"]
        video = "[0:v]setsar=1[bg]"
        clip_audio = False
    inputs += ["-loop", "1", "-i", str(ov)]

    if narration:
        inputs += ["-i", str(narration)]
        audio = "[2:a]aresample=44100,apad[a]"
    elif clip_audio:
        audio = "[0:a]aresample=44100,apad[a]"
    else:
        inputs += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        audio = "[2:a]anull[a]"

    out = tmp / f"scene{index}.mp4"
    run(*inputs, "-filter_complex", f"{video};[bg][1:v]overlay=0:0,format=yuv420p[v];{audio}",
        "-map", "[v]", "-map", "[a]", "-t", f"{duration:.3f}", "-r", str(FPS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", str(out))
    return out, duration, highlighted


def render(script_path: Path, out_path: Path, bgm: Path | None = None) -> Path:
    script = json.loads(script_path.read_text(encoding="utf-8"))
    base = script_path.parent
    label = SERIES_LABELS.get(script.get("pillar", ""), "")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        sfx = make_sfx(tmp)
        parts, cues, t = [], [], 0.0
        for i, scene in enumerate(script["scenes"]):
            part, dur, highlighted = render_scene(scene, i, label, base, tmp)
            parts.append(part)
            if i == 0:
                cues.append(("pop", 0.0))
            elif highlighted:
                cues.append(("swish", t))
            t += dur
            print(f"  장면 {i + 1}/{len(script['scenes'])} 완료 ({dur:g}초)")

        joined = tmp / "joined.mp4"
        (tmp / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
        run("-f", "concat", "-safe", "0", "-i", str(tmp / "list.txt"), "-c", "copy", str(joined))

        # 효과음과 배경음 믹스
        inputs = ["-i", str(joined)]
        chains, mix = [], ["[0:a]"]
        for n, (name, at) in enumerate(cues, start=1):
            inputs += ["-i", str(sfx[name])]
            ms = int(at * 1000)
            chains.append(f"[{n}:a]adelay={ms}|{ms},volume={SFX_VOLUME}[s{n}]")
            mix.append(f"[s{n}]")
        if bgm:
            n = len(cues) + 1
            inputs += ["-stream_loop", "-1", "-i", str(bgm)]
            chains.append(f"[{n}:a]volume={BGM_VOLUME},atrim=0:{t:.3f}[bgm]")
            mix.append("[bgm]")
        graph = ";".join(chains + [f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0[a]"])
        run(*inputs, "-filter_complex", graph, "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out_path))

    print(f"완성: {out_path} ({duration_of(out_path):.1f}초)")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("script", type=Path)
    parser.add_argument("-o", "--out", type=Path, help="기본: 대본 폴더의 final.mp4")
    parser.add_argument("--bgm", type=Path, help="배경음 파일 (반복 재생, 목소리보다 작게)")
    args = parser.parse_args()
    render(args.script, args.out or args.script.parent / "final.mp4", args.bgm)


if __name__ == "__main__":
    main()
