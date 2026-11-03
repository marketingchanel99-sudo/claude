"""명령줄 진입점.

    python -m reach collect [--only reddit|youtube] [--since-days 365] [--min-demand 2]
    python -m reach analyze <파일> [<파일> ...] [--since-days N] [--min-demand N]

결과: content/research/<날짜>-raw.json (수집한 원본), content/research/<날짜>-questions.md (후보 리포트)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import asdict
from pathlib import Path

from . import analyze as az
from . import report, sources

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "content" / "research"
QUERIES = RESEARCH / "queries.json"


def _write(result: dict, attempts: list, label: str, min_demand: int, out_dir: Path, stem: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    md = out_dir / f"{stem}-questions.md"
    md.write_text(report.render(result, attempts, label, min_demand=min_demand), encoding="utf-8")
    return md


def _summary(result: dict, md: Path) -> None:
    by_series: dict = {}
    for c in result["clusters"]:
        by_series.setdefault(c.series, []).append(c.demand)
    parts = [f"{k} {len(v)}개(수요4+ {sum(1 for d in v if d >= 4)})" for k, v in sorted(by_series.items())]
    print(f"질문 {result['questions']}개 → 묶음 {len(result['clusters'])}개: " + (", ".join(parts) or "없음"))
    print(f"리포트: {md.relative_to(ROOT) if md.is_relative_to(ROOT) else md}")


def cmd_collect(args) -> int:
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    col = sources.collect(config, only=args.only)
    stem = dt.date.today().isoformat()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = out_dir / f"{stem}-raw.json"
    raw.write_text(json.dumps({
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "config": config,
        "attempts": [asdict(a) for a in col.attempts],
        "posts": [p.to_dict() for p in col.posts],
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    ok = sum(1 for a in col.attempts if a.ok)
    print(f"수집: 시도 {len(col.attempts)}번, 성공 {ok}번, 글 {len(col.posts)}개 → {raw.name}")
    if not col.posts:
        errors = sorted({a.error for a in col.attempts if a.error})[:5]
        print("가져온 글이 없다. 리포트를 만들지 않는다. 오류:", *errors, sep="\n  ", file=sys.stderr)
        return 2
    result = az.analyze(col.posts, since_days=args.since_days)
    _summary(result, _write(result, col.attempts, f"`{raw.name}` ({args.config})", args.min_demand, out_dir, stem))
    return 0


def cmd_analyze(args) -> int:
    posts, attempts = [], []
    for f in args.files:
        posts += sources.load_any(Path(f))
        data = json.loads(Path(f).read_text(encoding="utf-8")) if f.endswith(".json") else {}
        if isinstance(data, dict):
            attempts += [sources.Attempt(**a) for a in data.get("attempts", [])]
    if not posts:
        print("읽은 글이 없다.", file=sys.stderr)
        return 2
    result = az.analyze(posts, since_days=args.since_days)
    label = ", ".join(f"`{Path(f).name}`" for f in args.files)
    _summary(result, _write(result, attempts, label, args.min_demand, Path(args.out), args.stem or dt.date.today().isoformat()))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m reach", description="외국인 질문 수집기 (읽기 전용)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("collect", help="queries.json대로 수집하고 분석")
    c.add_argument("--config", default=str(QUERIES))
    c.add_argument("--only", choices=("reddit", "youtube"))

    a = sub.add_parser("analyze", help="저장해 둔 결과 파일만 분석 (네트워크 안 씀)")
    a.add_argument("files", nargs="+")
    a.add_argument("--stem", help="출력 파일 이름 앞부분 (기본: 오늘 날짜)")

    for p in (c, a):
        p.add_argument("--since-days", type=int, default=365, help="이 기간 안의 글만 (0이면 전부)")
        p.add_argument("--min-demand", type=int, default=2, help="리포트 표에 넣을 최소 수요 점수")
        p.add_argument("--out", default=str(RESEARCH))

    args = ap.parse_args(argv)
    try:
        return cmd_collect(args) if args.cmd == "collect" else cmd_analyze(args)
    except sources.SourceError as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 2
