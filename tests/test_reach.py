"""reach 로직 테스트. 네트워크를 쓰지 않는다. 아래 글들은 테스트용으로 지어낸 제목이다 (리서치 결과 아님).

    python -m unittest tests.test_reach -v
"""
import datetime as dt
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from reach import analyze as az
from reach import report, sources
from reach.model import Post

NOW = dt.datetime(2026, 11, 3, tzinfo=dt.timezone.utc)
RECENT = NOW.timestamp() - 30 * 86400
OLD = NOW.timestamp() - 800 * 86400


def listing(*rows):
    return {"kind": "Listing", "data": {"children": [
        {"kind": "t3", "data": {"title": t, "permalink": f"/r/{sub}/comments/{i}/x/", "subreddit": sub,
                                "score": s, "num_comments": c, "created_utc": ts, "selftext": ""}}
        for i, (t, sub, s, c, ts) in enumerate(rows)
    ]}}


FIXTURE = listing(
    ("Why do Koreans not tip at restaurants?", "korea", 900, 300, RECENT),
    ("Why don't Koreans tip? Is tipping rude?", "koreatravel", 150, 80, RECENT),
    ("Is tipping expected in Korea restaurants?", "seoul", 60, 40, RECENT),
    ("How do I use T-money on the subway?", "koreatravel", 40, 25, RECENT),
    ("Which sunscreen do Koreans actually use?", "AsianBeauty", 500, 210, RECENT),
    ("Best convenience store snacks at CU or GS25?", "seoul", 70, 30, RECENT),
    ("[Photo] Sunset at Namsan tower", "seoul", 3000, 50, RECENT),
    ("My trip report: 10 days in Busan", "koreatravel", 200, 40, RECENT),
    ("Why do Koreans sit on the floor?", "korea", 5, 3, OLD),
)


class QuestionTest(unittest.TestCase):
    def test_is_question(self):
        self.assertTrue(az.is_question("Why do Koreans not tip?"))
        self.assertTrue(az.is_question("[Question] best cushion for oily skin"))
        self.assertTrue(az.is_question("Anyone tried the Daiso toner"))
        self.assertFalse(az.is_question("[Photo] Sunset at Namsan tower"))
        self.assertFalse(az.is_question("My trip report: 10 days in Busan"))
        self.assertFalse(az.is_question("Review: is this worth it?"))

    def test_series_and_hook(self):
        cases = {
            "Why do Koreans not tip at restaurants?": ("explained", "why-koreans"),
            "How do I use T-money on the subway?": ("tips", "how-to"),
            "Which sunscreen do Koreans actually use?": ("items", "secret"),
            "Best convenience store snacks at CU or GS25?": ("ranked", "vs"),
            "Is it rude to blow your nose at dinner?": ("explained", "dont-do-this"),
            "How much does Olive Young sunscreen cost?": ("items", "price-shock"),
        }
        for title, (series, hook) in cases.items():
            got = az.classify_series(title)[0]
            self.assertEqual(got, series, title)
            self.assertEqual(az.suggest_hook(title, got), hook, title)


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.posts = sources.parse_reddit_listing(FIXTURE)

    def test_filters_and_clusters(self):
        r = az.analyze(self.posts, since_days=365, now=NOW)
        self.assertEqual(r["total"], 9)
        self.assertEqual(r["recent"], 8)          # 800일 전 글은 빠진다
        self.assertEqual(r["questions"], 6)       # 사진·후기 글은 빠진다
        tipping = r["clusters"][0]
        self.assertEqual(len(tipping.posts), 3)   # 팁 질문 3개는 하나로 묶인다
        self.assertEqual(tipping.series, "explained")
        self.assertEqual(tipping.communities, ["korea", "koreatravel", "seoul"])
        self.assertGreaterEqual(tipping.demand, 4)
        self.assertEqual(tipping.lead.title, "Why do Koreans not tip at restaurants?")
        singles = [c for c in r["clusters"] if c is not tipping]
        self.assertTrue(all(len(c.posts) == 1 for c in singles))
        self.assertTrue(all(c.demand < tipping.demand for c in singles))

    def test_dedupe_by_url(self):
        r = az.analyze(self.posts + self.posts, since_days=0, now=NOW)
        self.assertEqual(r["total"], 9)

    def test_report(self):
        r = az.analyze(self.posts, since_days=365, now=NOW)
        md = report.render(r, [], "fixture", min_demand=1, today=NOW.date())
        self.assertIn("## Why Koreans…? (`explained`)", md)
        self.assertIn("https://www.reddit.com/r/korea/comments/0/x/", md)
        self.assertIn("`why-koreans`", md)
        self.assertNotIn("Namsan", md)


class FormatTest(unittest.TestCase):
    def test_agent_reach_envelope(self):
        env = {"schema_version": 1, "ok": True, "channel": "reddit", "action": "search", "items": [
            {"title": "Is Daiso skincare worth buying?", "url": "https://www.reddit.com/r/x/1",
             "author": "u1", "published_at": "2026-10-01T00:00:00+00:00", "text": "",
             "raw": {"subreddit": "KoreanBeauty", "score": 42, "num_comments": 17}},
        ]}
        [p] = sources.parse_agent_reach(env)
        self.assertEqual((p.source, p.community, p.score, p.comments, p.backend),
                         ("reddit", "KoreanBeauty", 42, 17, "agent-reach"))

    def test_agent_reach_error_raises(self):
        with self.assertRaises(sources.SourceError):
            sources.parse_agent_reach({"ok": False, "error": {"code": "NEED_LOGIN", "message": "x"}})

    def test_ytdlp_lines(self):
        line = json.dumps({"id": "abc", "title": "Why do Koreans bow?", "channel": "C", "view_count": 12000,
                           "comment_count": 300, "upload_date": "20261001"})
        [p] = sources.parse_ytdlp_lines(line)
        self.assertEqual(p.url, "https://www.youtube.com/watch?v=abc")
        self.assertEqual(p.published_at, "2026-10-01T00:00:00+00:00")

    def test_load_any(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "listing.json"
            f.write_text(json.dumps(FIXTURE))
            self.assertEqual(len(sources.load_any(f)), 9)
            ours = Path(d) / "raw.json"
            ours.write_text(json.dumps({"posts": [Post("reddit", "t", "u").to_dict()]}))
            self.assertEqual(sources.load_any(ours)[0].title, "t")


class FallbackTest(unittest.TestCase):
    def test_first_backend_fails_second_used(self):
        def broken(*a):
            raise sources.SourceError("agent-reach 이 설치돼 있지 않음")

        def works(sub, q, limit):
            return sources.parse_reddit_listing(FIXTURE, query=q)[:2]

        with mock.patch.object(sources, "REDDIT_BACKENDS", (("agent-reach", broken), ("reddit-json", works))):
            col = sources.collect({"reddit": {"subreddits": ["korea"], "queries": ["tip"]}}, only="reddit")
        self.assertEqual(len(col.posts), 2)
        self.assertEqual([(a.backend, a.ok) for a in col.attempts], [("agent-reach", False), ("reddit-json", True)])

    def test_all_fail_adds_nothing(self):
        def broken(*a):
            raise sources.SourceError("HTTP 403")

        with mock.patch.object(sources, "YOUTUBE_BACKENDS", (("a", broken), ("b", broken))):
            col = sources.collect({"youtube": {"queries": ["q"]}}, only="youtube")
        self.assertEqual(col.posts, [])
        self.assertEqual(len(col.attempts), 2)


    def test_blocked_backend_skipped_after_three_fails(self):
        calls = []

        def broken(sub, q, limit):
            calls.append(q)
            raise sources.SourceError("HTTP 403")

        config = {"reddit": {"subreddits": ["a", "b"], "queries": ["q1", "q2", "q3"]}}
        with mock.patch.object(sources, "REDDIT_BACKENDS", (("reddit-json", broken),)):
            col = sources.collect(config, only="reddit")
        self.assertEqual(len(calls), 3)
        self.assertIn("건너뜀", col.attempts[-1].error)


class CliTest(unittest.TestCase):
    def test_analyze_command(self):
        root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "listing.json"
            f.write_text(json.dumps(FIXTURE))
            p = subprocess.run(
                ["python3", "-m", "reach", "analyze", str(f), "--out", d, "--stem", "t", "--since-days", "0",
                 "--min-demand", "1"], cwd=root, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("Why do Koreans not tip", (Path(d) / "t-questions.md").read_text())


if __name__ == "__main__":
    unittest.main()
