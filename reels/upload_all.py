"""영상 하나를 유튜브 쇼츠, 인스타 릴스, 틱톡에 동시에 올린다.

    python -m reels.upload_all output/example.mp4 scripts/example.json
    python -m reels.upload_all output/example.mp4 scripts/example.json --only youtube,tiktok
    python -m reels.upload_all output/example.mp4 scripts/example.json --dry-run

한 플랫폼이 실패해도 나머지는 계속 진행하고, 마지막에 결과를 요약한다.
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from pathlib import Path

from dotenv import load_dotenv

PLATFORMS = {"youtube": "reels.upload_youtube", "instagram": "reels.upload_instagram", "tiktok": "reels.upload_tiktok"}


def run(name: str, video: Path, meta: dict) -> tuple[str, bool, str]:
    try:
        return name, True, import_module(PLATFORMS[name]).upload(video, meta)
    except Exception as e:  # 한 곳의 실패가 다른 플랫폼을 막지 않도록
        return name, False, f"{type(e).__name__}: {e}"


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video", type=Path)
    parser.add_argument("meta", type=Path, help="대본 JSON (title, description, hashtags 사용)")
    parser.add_argument("--only", default=",".join(PLATFORMS), help="쉼표로 구분 (youtube,instagram,tiktok)")
    parser.add_argument("--dry-run", action="store_true", help="업로드하지 않고 무엇을 올릴지만 출력")
    args = parser.parse_args()

    meta = json.loads(args.meta.read_text(encoding="utf-8"))
    targets = [p.strip() for p in args.only.split(",") if p.strip()]
    unknown = set(targets) - PLATFORMS.keys()
    if unknown:
        parser.error(f"알 수 없는 플랫폼: {', '.join(sorted(unknown))}")
    if not args.video.exists():
        parser.error(f"영상 파일이 없습니다: {args.video}")

    if args.dry_run:
        print(f"[dry-run] {args.video} -> {', '.join(targets)}")
        print(f"  제목: {meta['title']}\n  해시태그: {' '.join('#' + t for t in meta.get('hashtags', []))}")
        return

    # 유튜브는 첫 실행 시 브라우저 로그인이 필요하므로 먼저 단독 실행하고, 나머지는 병렬로
    results = []
    if "youtube" in targets:
        results.append(run("youtube", args.video, meta))
    with ThreadPoolExecutor() as pool:
        results += pool.map(lambda n: run(n, args.video, meta), [t for t in targets if t != "youtube"])

    print("\n업로드 결과")
    for name, ok, detail in results:
        print(f"  {'✅' if ok else '❌'} {name:<10} {detail}")
    if not all(ok for _, ok, _ in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
