"""이 채널만의 로직: 질문 판별 → 묶기 → 시리즈·훅 추천 → 수요 점수.

규칙은 전부 이 파일 위쪽 상수에 있다. 결과가 이상하면 여기 키워드를 고친다.
점수는 "몇 명이 같은 걸 묻는가 + 얼마나 반응했나"만 본다. 제휴·제작 쉬움 점수는 `/ideas`가 매긴다.
"""
from __future__ import annotations

import datetime as dt
import math
import re
from dataclasses import dataclass, field
from typing import Optional

from .model import Post

# 질문으로 볼 시작어 (영어권 레딧·유튜브 제목 기준)
QUESTION_STARTS = (
    "why", "how", "what", "which", "where", "when", "who", "is", "are", "do", "does", "did", "can", "could",
    "should", "would", "will", "any", "anyone", "anybody", "has anyone", "recommend", "recommendations",
    "best", "help", "looking for", "need", "worth", "tips", "advice", "first time",
)
# 질문이 아닌 글 (후기, 사진 자랑, 공지)
NOT_QUESTION = re.compile(
    r"^\s*(?:\[?(?:psa|meta|news|weekly|daily|megathread|announcement|photo|pic|oc|haul|review|trip report)\]?\b)",
    re.I,
)

STOPWORDS = set("""
a an the and or but if of to in on at for from by with about as into over under is are was were be been being
do does did doing have has had i me my we our you your he she it its they them their this that these those
what which who whom why how where when can could should would will shall may might must any anyone anybody
some there here than then so too very just really also not no yes get got go going went im ive id dont
korea korean koreans seoul south sk kr please help question questions advice tips thanks thank anything
one ones thing things way best good like know need want looking first time trip travel visit visiting
use used using actually usually really people person someone everyone common normal okay ok
""".split())

# 시리즈 판별 키워드. 맞은 개수가 가장 많은 시리즈를 고른다. 동점이면 아래 순서가 우선.
SERIES_KEYWORDS = {
    "explained": (
        "why", "culture", "cultural", "etiquette", "custom", "customs", "normal", "rude", "polite", "tradition",
        "tipping", "age", "drinking", "superstition", "meaning", "mean", "considered", "offensive",
    ),
    "tips": (
        "subway", "metro", "bus", "taxi", "tmoney", "t-money", "visa", "k-eta", "keta", "sim", "esim",
        "airport", "incheon", "bank", "atm", "cash", "card", "app", "naver", "kakao", "map", "maps", "scam",
        "avoid", "mistake", "mistakes", "dont", "rules", "rule", "pharmacy", "hospital", "delivery", "luggage",
    ),
    "items": (
        "sunscreen", "skincare", "serum", "toner", "cream", "moisturizer", "cleanser", "mask", "product",
        "products", "brand", "buy", "bought", "olive", "daiso", "souvenir", "souvenirs", "gift", "gifts",
        "must-have", "must", "haul", "kbeauty", "k-beauty", "makeup", "cushion", "shampoo", "gadget",
    ),
    "ranked": (
        "best", "top", "ranking", "ranked", "favorite", "favourite", "snack", "snacks", "ramen", "ramyeon",
        "convenience", "cu", "gs25", "7-eleven", "flavor", "worst", "tier", "compare", "vs",
    ),
}
SERIES_ORDER = ("explained", "tips", "items", "ranked")

# 훅 템플릿 추천 (content/hooks.md의 ID). 위에서부터 처음 맞는 규칙을 쓴다.
HOOK_RULES = (
    (r"\b(?:price|cost|costs|cheap|cheaper|expensive|how much|\$\d|won)\b", "price-shock"),
    (r"\b(?:vs|versus|or|better than|compared)\b", "vs"),
    (r"\b(?:don'?t|avoid|rude|mistake|mistakes|offensive|banned|illegal)\b", "dont-do-this"),
    (r"^why\b", "why-koreans"),
    (r"\b(?:best|top|ranking|ranked|favorite|favourite|worst)\b", "ranking"),
    (r"\b(?:every ?one|all koreans|locals use|koreans use|everyday)\b", "everyone-has-this"),
    (r"\b(?:bag|fridge|bathroom|pouch|kit|routine)\b", "whats-inside"),
    (r"^(?:how|where)\b", "how-to"),
    (r"\b(?:first time|first|arriving|landing)\b", "pov"),
)
SERIES_DEFAULT_HOOK = {"explained": "why-koreans", "tips": "how-to", "items": "secret", "ranked": "ranking"}

# 같은 질문 판정: 씨앗 질문과 키워드가 이만큼 겹치면 묶는다 (겹친 수 ÷ 짧은 쪽 키워드 수)
CLUSTER_OVERLAP = 0.5
MIN_TOKENS = 1


def is_question(title: str) -> bool:
    t = title.strip().lower()
    if not t or NOT_QUESTION.match(t):
        return False
    if "?" in t:
        return True
    t = re.sub(r"^[\[\(][^\]\)]*[\]\)]\s*", "", t)  # "[Question] ..." 같은 머리표 제거
    return any(t == s or t.startswith(s + " ") for s in QUESTION_STARTS)


def _stem(w: str) -> str:
    """아주 단순한 어간 처리. 비교용이라 모양이 같기만 하면 된다: tipping→tip, store/stored→stor, cities→city."""
    if len(w) > 5 and w.endswith("ing"):
        w = w[:-3]
        if len(w) > 2 and w[-1] == w[-2] and w[-1] not in "lsz":  # tipp → tip
            w = w[:-1]
    elif len(w) > 4 and w.endswith(("ied", "ies")):
        w = w[:-3] + "y"
    elif len(w) > 4 and w.endswith("ed") and not w.endswith("eed"):
        w = w[:-2]
    elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    if len(w) > 3 and w.endswith("e") and not w.endswith("ee"):
        w = w[:-1]
    return w


def tokens(title: str) -> set:
    words = re.findall(r"[a-z0-9][a-z0-9'\-]*", title.lower().replace("’", "'"))
    out = set()
    for w in words:
        w = w.strip("'-").replace("'", "")
        if len(w) < 2 or w in STOPWORDS or w.isdigit():
            continue
        out.add(_stem(w))
    return out


def classify_series(title: str) -> tuple:
    """(시리즈 코드, 맞은 키워드들). 아무것도 안 맞으면 ("unsorted", [])."""
    words = set(re.findall(r"[a-z0-9][a-z0-9\-]*", title.lower().replace("'", "")))
    stems = {_stem(w) for w in words}
    best, hits = "unsorted", []
    for code in SERIES_ORDER:
        matched = [k for k in SERIES_KEYWORDS[code] if k in words or _stem(k) in stems]
        if len(matched) > len(hits):
            best, hits = code, matched
    return best, hits


def suggest_hook(title: str, series: str) -> str:
    t = title.lower().strip()
    for pattern, hook in HOOK_RULES:
        if re.search(pattern, t):
            return hook
    return SERIES_DEFAULT_HOOK.get(series, "secret")


@dataclass
class Cluster:
    posts: list = field(default_factory=list)
    keywords: set = field(default_factory=set)  # 씨앗(반응이 가장 큰 첫 글)의 키워드. 묶을수록 번지지 않게 고정
    series: str = "unsorted"
    series_hits: list = field(default_factory=list)
    hook: str = ""
    demand: int = 1
    strength: float = 0.0

    @property
    def lead(self) -> Post:
        return max(self.posts, key=lambda p: (p.score + 2 * p.comments, len(p.title)))

    @property
    def communities(self) -> list:
        return sorted({p.community for p in self.posts if p.community})

    @property
    def total_score(self) -> int:
        return sum(p.score for p in self.posts if p.source == "reddit")

    @property
    def total_comments(self) -> int:
        return sum(p.comments for p in self.posts)

    @property
    def total_views(self) -> int:
        return sum(p.score for p in self.posts if p.source == "youtube")


def _similar(a: set, b: set) -> float:
    shared = len(a & b)
    if not shared:
        return 0.0
    if min(len(a), len(b)) >= 3 and shared < 2:  # 긴 제목끼리는 키워드 2개 이상 겹쳐야 같은 질문
        return 0.0
    return shared / min(len(a), len(b))


def dedupe(posts: list) -> list:
    seen, out = set(), []
    for p in posts:
        key = p.url.split("?")[0].rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def _within(p: Post, since_days: Optional[int], now: dt.datetime) -> bool:
    if not since_days or not p.published_at:
        return True
    try:
        t = dt.datetime.fromisoformat(p.published_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return (now - t).days <= since_days


def cluster(posts: list) -> list:
    """씨앗 질문과 키워드가 많이 겹치는 질문끼리 묶는다. 반응이 큰 글부터 씨앗으로 잡는다."""
    clusters: list = []
    for p in sorted(posts, key=lambda p: -(p.score + 2 * p.comments)):
        toks = tokens(p.title)
        if len(toks) < MIN_TOKENS:
            continue
        best, best_sim = None, 0.0
        for c in clusters:
            sim = _similar(toks, c.keywords)
            if sim > best_sim:
                best, best_sim = c, sim
        if best is not None and best_sim >= CLUSTER_OVERLAP:
            best.posts.append(p)
        else:
            clusters.append(Cluster(posts=[p], keywords=set(toks)))
    return clusters


def _strength(c: Cluster) -> float:
    # 같은 질문을 한 사람 수가 가장 중요하다 (글 1개당 3점). 반응은 로그로 눌러서 한 글이 독식하지 않게.
    reddit = sum(math.log1p(max(p.score, 0)) + math.log1p(p.comments) for p in c.posts if p.source == "reddit")
    youtube = sum(math.log1p(max(p.score, 0)) / 2 for p in c.posts if p.source == "youtube")
    places = len(c.communities)
    return 3 * len(c.posts) + reddit + youtube + (2 if places >= 2 else 0)


def demand_score(strength: float) -> int:
    """수요 1-5. 기준은 고정값이라 달마다 비교할 수 있다."""
    for score, floor in ((5, 40), (4, 25), (3, 15), (2, 8)):
        if strength >= floor:
            return score
    return 1


def analyze(posts: list, since_days: Optional[int] = None, now: Optional[dt.datetime] = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    posts = dedupe(posts)
    recent = [p for p in posts if _within(p, since_days, now)]
    questions = [p for p in recent if is_question(p.title)]
    clusters = cluster(questions)
    for c in clusters:
        c.series, c.series_hits = classify_series(" ".join(p.title for p in c.posts))
        c.hook = suggest_hook(c.lead.title, c.series)
        c.strength = _strength(c)
        c.demand = demand_score(c.strength)
    clusters.sort(key=lambda c: (-c.demand, -c.strength))
    return {
        "total": len(posts), "recent": len(recent), "questions": len(questions),
        "clusters": clusters,
    }
