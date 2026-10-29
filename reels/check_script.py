"""대본(script.json v2) 자동 검사.

훅 규칙(content/hooks.md), 길이, 내레이션 속도, 제휴 고지, 금지 표현을 검사한다.
오류가 있으면 종료 코드 1, 경고만 있으면 0.

    python -m reels.check_script episodes/<id>/script.json
"""
import argparse
import json
import re
import sys
from pathlib import Path

HOOKS_FILE = Path(__file__).resolve().parent.parent / "content" / "hooks.md"
STATUSES = {"draft", "approved", "produced", "published"}
# 시리즈별 길이 (docs/WORKFLOW.md, content/series/)
SERIES_SECONDS = {"items": (20, 30), "explained": (25, 35), "tips": (15, 25), "ranked": (30, 40), "brand": (20, 30)}
PILLARS = set(SERIES_SECONDS)
SCENE_TYPES = {"character", "product", "broll", "text"}

HOOK_MAX_SECONDS = 3
HOOK_MAX_WORDS = 10
HOOK_CAPTION_MAX_WORDS = 6
TOTAL_SECONDS = (15, 45)
WORDS_PER_SECOND = 2.8  # 빠른 숏폼 영어 내레이션 기준 상한
CAPTION_MAX_CHARS = 42
BANNED_OPENERS = ("hi", "hello", "hey guys", "welcome", "today", "in this video", "so", "okay", "my name")
BANNED_PHRASES = ("you need this", "best ever", "guaranteed", "100%", "miracle", "cure")
# AI 가상 인물이 직접 써 본 것처럼 말하면 기만 광고가 된다 (character/bible.md)
FAKE_EXPERIENCE = (
    r"\bi(?:'ve| have)? (?:tried|tested|used)\b", r"\bi use (?:this|it)\b", r"\bi(?:'ve| have) been using\b",
    r"\bmy (?:holy grail|go-to|favorite)\b", r"\bin my experience\b", r"\bmy skin\b",
)
MOTION_WORDS = (
    "push", "pull", "zoom", "pan", "orbit", "dolly", "tracking", "whip", "reach", "hold", "thrust", "shove",
    "open", "unzip", "drop", "pour", "splash", "tap", "swipe", "walk", "run", "turn", "spin", "throw", "slam",
    "point", "lean", "grab", "pick", "wave", "shake", "burst", "fall", "slide", "rush",
)


def hook_ids() -> set[str]:
    return set(re.findall(r"^\| `([a-z-]+)` \|", HOOKS_FILE.read_text(encoding="utf-8"), re.M))


def words(text: str) -> int:
    return len(re.findall(r"[\w'’$%-]+", text or ""))


def check(script: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    known_hooks = hook_ids()

    for field in ("id", "status", "pillar", "hook_type", "title", "scenes"):
        if not script.get(field):
            errors.append(f"필수 필드 없음: {field}")
    if script.get("status") and script["status"] not in STATUSES:
        errors.append(f"status 값이 잘못됨: {script['status']}")
    if script.get("pillar") and script["pillar"] not in PILLARS:
        errors.append(f"pillar 값이 잘못됨: {script['pillar']}")
    if script.get("hook_type") and script["hook_type"] not in known_hooks:
        errors.append(f"hook_type '{script['hook_type']}'이 content/hooks.md에 없음")

    candidates = script.get("hook_candidates", [])
    if len(candidates) < 3:
        warnings.append(f"훅 후보가 {len(candidates)}개 (3개 권장)")
    elif len({c.get("hook_type") for c in candidates}) < len(candidates):
        warnings.append("훅 후보끼리 같은 템플릿을 씀. 서로 다른 템플릿으로 만들 것")

    scenes = script.get("scenes") or []
    if scenes:
        # 훅 (첫 장면)
        hook = scenes[0]
        narration = (hook.get("narration") or "").strip()
        if hook.get("type") != "character":
            warnings.append("첫 장면이 주인공 등장(character)이 아님")
        if hook.get("duration", 0) > HOOK_MAX_SECONDS:
            errors.append(f"첫 장면이 {hook['duration']}초 (훅은 {HOOK_MAX_SECONDS}초 이하)")
        if not narration:
            errors.append("첫 장면에 내레이션(훅 문장)이 없음")
        elif words(narration) > HOOK_MAX_WORDS:
            errors.append(f"훅 문장이 {words(narration)}단어 ({HOOK_MAX_WORDS}단어 이하): \"{narration}\"")
        if re.match(rf"({'|'.join(map(re.escape, BANNED_OPENERS))})\b", narration.lower()):
            errors.append(f"훅이 인사·입버릇으로 시작함: \"{narration}\"")
        if not hook.get("caption"):
            errors.append("첫 장면에 자막이 없음 (0초부터 자막 필요)")
        elif words(hook["caption"]) > HOOK_CAPTION_MAX_WORDS:
            errors.append(f"훅 자막이 {words(hook['caption'])}단어 ({HOOK_CAPTION_MAX_WORDS}단어 이하)")
        if not re.search(rf"\b({'|'.join(MOTION_WORDS)})", (hook.get("visual") or "").lower()):
            warnings.append("첫 장면 visual에 움직임 묘사가 안 보임 (첫 프레임부터 동작이 있어야 함)")

    total = 0.0
    for scene in scenes:
        sid = scene.get("id", "?")
        if scene.get("type") not in SCENE_TYPES:
            errors.append(f"장면 {sid}: type 값이 잘못됨 ({scene.get('type')})")
        duration = scene.get("duration") or 0
        if duration <= 0:
            errors.append(f"장면 {sid}: duration 없음")
        total += duration
        spoken = words(scene.get("narration", ""))
        if duration and spoken / duration > WORDS_PER_SECOND:
            errors.append(
                f"장면 {sid}: {duration}초에 {spoken}단어는 너무 빠름 (최대 {int(duration * WORDS_PER_SECOND)}단어)"
            )
        if len(scene.get("caption") or "") > CAPTION_MAX_CHARS:
            warnings.append(f"장면 {sid}: 자막이 {len(scene['caption'])}자 ({CAPTION_MAX_CHARS}자 이하 권장)")

    low, high = SERIES_SECONDS.get(script.get("pillar"), TOTAL_SECONDS)
    if scenes and not low <= total <= high:
        errors.append(f"전체 길이 {total:g}초 (이 시리즈는 {low}~{high}초)")

    # 제휴 고지
    affiliate = script.get("affiliate") or {}
    if affiliate.get("links"):
        disclosure = (affiliate.get("disclosure") or "").strip()
        if not disclosure:
            errors.append("제휴 링크가 있는데 disclosure가 없음")
        else:
            for name, post in (script.get("platforms") or {}).items():
                text = post.get("caption") or post.get("description") or ""
                if disclosure not in text:
                    errors.append(f"{name} 캡션에 제휴 고지 문구가 없음")

    youtube_title = (script.get("platforms") or {}).get("youtube", {}).get("title", "")
    if len(youtube_title) > 100:
        errors.append(f"YouTube 제목이 {len(youtube_title)}자 (100자 이하)")

    # 금지 표현
    text_blob = json.dumps(script, ensure_ascii=False).lower()
    for phrase in BANNED_PHRASES:
        if phrase in text_blob:
            warnings.append(f"과장·금지 표현 포함: \"{phrase}\"")
    for pattern in FAKE_EXPERIENCE:
        match = re.search(pattern, text_blob)
        if match:
            errors.append(f"직접 써 본 것처럼 말함: \"{match.group(0)}\" (근거 기반으로 바꿀 것: Koreans use this, #1 at Olive Young)")

    if script.get("pillar") in {"items", "explained"} and not script.get("sources"):
        warnings.append("sources가 비어 있음 (가격·성분·문화 주장 근거 필요)")

    return errors, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scripts", nargs="+", type=Path)
    args = parser.parse_args()

    failed = False
    for path in args.scripts:
        errors, warnings = check(json.loads(path.read_text(encoding="utf-8")))
        print(f"{'❌' if errors else '✅'} {path}")
        for e in errors:
            print(f"   오류: {e}")
        for w in warnings:
            print(f"   경고: {w}")
        failed |= bool(errors)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
