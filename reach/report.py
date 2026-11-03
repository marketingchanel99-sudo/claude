"""분석 결과를 `/ideas`가 읽을 후보 리포트(md)로 쓴다."""
from __future__ import annotations

import datetime as dt

from .analyze import Cluster

SERIES_NAMES = {
    "items": "Korean Secret", "explained": "Why Koreans…?", "tips": "Seoul Survival", "ranked": "Ranked",
    "unsorted": "미분류",
}


def _cell(text: str, limit: int = 90) -> str:
    text = " ".join(str(text).split()).replace("|", "\\|")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _evidence(c: Cluster) -> str:
    bits = []
    if c.total_score:
        bits.append(f"추천 {c.total_score:,}")
    if c.total_comments:
        bits.append(f"댓글 {c.total_comments:,}")
    if c.total_views:
        bits.append(f"조회 {c.total_views:,}")
    return f"글 {len(c.posts)}개 · " + " · ".join(bits) if bits else f"글 {len(c.posts)}개"


def _links(c: Cluster, n: int = 3) -> str:
    top = sorted(c.posts, key=lambda p: -(p.score + 2 * p.comments))[:n]
    return " ".join(f"[{i + 1}]({p.url})" for i, p in enumerate(top))


def render(result: dict, attempts: list, sources_label: str, min_demand: int = 1, today: dt.date = None) -> str:
    today = today or dt.date.today()
    clusters = [c for c in result["clusters"] if c.demand >= min_demand]
    lines = [
        f"# 질문 수집 리포트 · {today.isoformat()}",
        "",
        "> `python -m reach`가 자동으로 만든 **후보** 목록이다. 아직 `content/ideas.md`에 들어간 게 아니다.",
        "> `/ideas`가 근거 링크를 열어 확인하고, 가제·제휴·제작 쉬움 점수를 매긴 뒤 옮긴다.",
        "> 수요 점수는 같은 질문을 한 글 수와 반응(추천·댓글·조회)만 본 값이다.",
        "",
        f"- 입력: {sources_label}",
        f"- 글 {result['total']}개 → 기간 안 {result['recent']}개 → 질문 {result['questions']}개 → "
        f"묶음 {len(result['clusters'])}개 (표에는 수요 {min_demand} 이상 {len(clusters)}개)",
        "",
    ]
    for code in ("items", "explained", "tips", "ranked", "unsorted"):
        group = [c for c in clusters if c.series == code]
        if not group:
            continue
        lines += [
            f"## {SERIES_NAMES[code]} (`{code}`) · {len(group)}개",
            "",
            "| 수요 | 대표 질문 (원문) | 추천 훅 | 반응 | 근거 | 묶인 질문 예 |",
            "|---|---|---|---|---|---|",
        ]
        for c in group:
            others = [p.title for p in c.posts if p is not c.lead][:2]
            lines.append(
                f"| {c.demand} | {_cell(c.lead.title)} | `{c.hook}` | {_evidence(c)} | {_links(c)} | "
                f"{_cell(' / '.join(others), 120) if others else '-'} |"
            )
        lines.append("")

    failed = [a for a in attempts if not a.ok]
    if attempts:
        ok = sum(1 for a in attempts if a.ok)
        lines += ["## 수집 기록", "", f"시도 {len(attempts)}번 · 성공 {ok}번 · 실패 {len(failed)}번", ""]
        if failed:
            lines += ["| 소스 | 백엔드 | 검색 | 오류 |", "|---|---|---|---|"]
            for a in failed[:30]:
                lines.append(f"| {a.source} | {a.backend} | {_cell(a.query, 40)} | {_cell(a.error, 80)} |")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"
