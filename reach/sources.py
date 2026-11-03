"""소스별 백엔드. 각 소스는 백엔드 목록을 순서대로 시도한다 (Agent Reach 방식).

- reddit:  agent-reach(설치돼 있고 로그인돼 있으면) → 레딧 공개 JSON
- youtube: agent-reach → yt-dlp

모든 백엔드는 읽기만 한다. 로그인을 대신하거나 비밀번호를 묻지 않는다.
"""
from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Iterable, Optional
from urllib.parse import quote_plus

from .model import Attempt, Collection, Post

USER_AGENT = "jiwoo-reach/0.1 (read-only research script)"
TIMEOUT = 30


class SourceError(Exception):
    pass


# ── 공통 파서 (저장해 둔 파일을 다시 읽을 때도 쓴다) ──

def _iso(ts) -> Optional[str]:
    if isinstance(ts, (int, float)):
        return dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc).isoformat()
    if isinstance(ts, str) and len(ts) == 8 and ts.isdigit():  # yt-dlp upload_date: YYYYMMDD
        return f"{ts[:4]}-{ts[4:6]}-{ts[6:]}T00:00:00+00:00"
    return ts or None


def _int(*values) -> int:
    for v in values:
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)):
            return int(v)
        if isinstance(v, str) and v.replace(",", "").isdigit():
            return int(v.replace(",", ""))
    return 0


def parse_reddit_listing(data: dict, query: str = "", backend: str = "reddit-json") -> list:
    """레딧 공개 JSON (`/search.json`, `/top.json`)을 Post 목록으로."""
    posts = []
    for child in (data.get("data") or {}).get("children") or []:
        d = child.get("data") or {}
        if not d.get("title"):
            continue
        posts.append(Post(
            source="reddit", title=d["title"].strip(),
            url="https://www.reddit.com" + d["permalink"] if d.get("permalink") else d.get("url", ""),
            community=d.get("subreddit", ""), text=(d.get("selftext") or "")[:1000],
            score=_int(d.get("score"), d.get("ups")), comments=_int(d.get("num_comments")),
            published_at=_iso(d.get("created_utc")), query=query, backend=backend,
        ))
    return posts


def parse_ytdlp_lines(text: str, query: str = "", backend: str = "yt-dlp") -> list:
    posts = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        info = json.loads(line)
        vid = info.get("id")
        url = info.get("webpage_url") or info.get("url") or (f"https://www.youtube.com/watch?v={vid}" if vid else "")
        if not info.get("title") or not url:
            continue
        posts.append(Post(
            source="youtube", title=info["title"].strip(), url=url,
            community=info.get("channel") or info.get("uploader") or "",
            text=(info.get("description") or "")[:1000],
            score=_int(info.get("view_count")), comments=_int(info.get("comment_count")),
            published_at=_iso(info.get("timestamp") or info.get("upload_date")), query=query, backend=backend,
        ))
    return posts


def parse_agent_reach(envelope: dict, query: str = "") -> list:
    """Agent Reach 출력 `{ok, channel, items:[{title,url,author,published_at,text,raw}]}`을 Post 목록으로."""
    if not envelope.get("ok"):
        err = envelope.get("error") or {}
        raise SourceError(f"agent-reach {err.get('code', 'ERROR')}: {err.get('message', '')}".strip())
    channel = envelope.get("channel") or "web"
    posts = []
    for it in envelope.get("items") or []:
        raw = it.get("raw") if isinstance(it.get("raw"), dict) else {}
        if isinstance(raw.get("post"), dict):  # reddit read: {post, comments}
            raw = raw["post"]
        if not it.get("title") or not it.get("url"):
            continue
        posts.append(Post(
            source=channel, title=str(it["title"]).strip(), url=it["url"],
            community=str(raw.get("subreddit") or it.get("author") or ""),
            text=(it.get("text") or "")[:1000],
            score=_int(raw.get("score"), raw.get("upvotes"), raw.get("ups"), raw.get("view_count"), raw.get("likes")),
            comments=_int(raw.get("num_comments"), raw.get("comments"), raw.get("comment_count")),
            published_at=it.get("published_at"), query=query, backend="agent-reach",
        ))
    return posts


def load_any(path: Path) -> list:
    """저장해 둔 결과 파일을 형식에 맞게 읽는다: 우리 raw, Agent Reach 출력, 레딧 JSON, yt-dlp JSONL."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return parse_ytdlp_lines(text)
    if isinstance(data, dict) and "posts" in data:            # 우리 raw
        return [Post.from_dict(p) for p in data["posts"]]
    if isinstance(data, dict) and "schema_version" in data:   # Agent Reach
        return parse_agent_reach(data)
    if isinstance(data, dict) and data.get("kind") == "Listing":
        return parse_reddit_listing(data)
    if isinstance(data, list) and data and isinstance(data[0], dict) and data[0].get("kind") == "Listing":
        return parse_reddit_listing(data[0])                  # 글 페이지 JSON: [글, 댓글]
    if isinstance(data, dict) and "title" in data:            # yt-dlp 한 줄짜리
        return parse_ytdlp_lines(text)
    raise SourceError(f"{path}: 알 수 없는 형식")


# ── 백엔드 ──

def _http_json(url: str) -> dict:
    import requests  # requirements.txt에 이미 있음

    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    if r.status_code == 429:
        raise SourceError("HTTP 429 (요청이 너무 많음, 잠시 후 다시)")
    if r.status_code != 200:
        raise SourceError(f"HTTP {r.status_code}")
    return r.json()


def _run(cmd: list) -> str:
    if not shutil.which(cmd[0]):
        raise SourceError(f"{cmd[0]} 이 설치돼 있지 않음")
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT * 4)
    if p.returncode != 0 and not p.stdout.strip():
        raise SourceError((p.stderr or f"exit {p.returncode}").strip()[:300])
    return p.stdout


def reddit_agent_reach(sub: str, query: str, limit: int) -> list:
    out = _run(["agent-reach", "reddit", "search", f"subreddit:{sub} {query}", "--limit", str(limit)])
    return parse_agent_reach(json.loads(out), query=query)


def reddit_public_json(sub: str, query: str, limit: int) -> list:
    url = (f"https://www.reddit.com/r/{sub}/search.json?q={quote_plus(query)}"
           f"&restrict_sr=1&sort=top&t=year&limit={limit}")
    return parse_reddit_listing(_http_json(url), query=query)


def youtube_agent_reach(query: str, limit: int) -> list:
    out = _run(["agent-reach", "youtube", "search", query, "--limit", str(limit)])
    return parse_agent_reach(json.loads(out), query=query)


def youtube_ytdlp(query: str, limit: int) -> list:
    # --flat-playlist는 조회수가 비어 올 수 있어서 쓰지 않는다 (조금 느리지만 수요 근거가 필요).
    out = _run(["yt-dlp", "--dump-json", "--skip-download", "--no-warnings", f"ytsearch{limit}:{query}"])
    return parse_ytdlp_lines(out, query=query)


REDDIT_BACKENDS = (("agent-reach", reddit_agent_reach), ("reddit-json", reddit_public_json))
YOUTUBE_BACKENDS = (("agent-reach", youtube_agent_reach), ("yt-dlp", youtube_ytdlp))


MAX_FAILS = 3  # 같은 백엔드가 연속으로 이만큼 실패하면 이번 실행에서는 건너뛴다 (막힌 곳을 계속 두드리지 않게)


def _try(source: str, label: str, backends: Iterable, call: Callable, out: Collection, fails: dict) -> None:
    """백엔드를 순서대로 시도하고, 처음 성공한 결과를 쓴다. 시도는 모두 기록한다."""
    for name, fn in backends:
        key = (source, name)
        if fails.get(key, 0) >= MAX_FAILS:
            continue
        try:
            posts = call(fn)
        except Exception as exc:  # 다음 백엔드로 넘어간다
            fails[key] = fails.get(key, 0) + 1
            note = f" (연속 {MAX_FAILS}번 실패, 이번 실행에서 건너뜀)" if fails[key] == MAX_FAILS else ""
            out.attempts.append(Attempt(source, name, label, ok=False, error=str(exc)[:300] + note))
            continue
        fails[key] = 0
        out.attempts.append(Attempt(source, name, label, ok=True, count=len(posts)))
        if posts:
            out.posts.extend(posts)
            return
    # 모두 실패하거나 결과가 0개면 아무것도 넣지 않는다 (가짜로 채우지 않는다).


def collect(config: dict, only: Optional[str] = None) -> Collection:
    out, fails = Collection(), {}
    limit = int(config.get("limit", 25))
    reddit = config.get("reddit") or {}
    if only in (None, "reddit"):
        for sub in reddit.get("subreddits", []):
            for q in reddit.get("queries", []):
                _try("reddit", f"r/{sub} {q}", REDDIT_BACKENDS, lambda fn: fn(sub, q, limit), out, fails)
    if only in (None, "youtube"):
        for q in (config.get("youtube") or {}).get("queries", []):
            _try("youtube", q, YOUTUBE_BACKENDS, lambda fn: fn(q, min(limit, 15)), out, fails)
    return out
