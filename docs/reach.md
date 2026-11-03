# 질문 수집기 (`reach/`)

외국인이 레딧·유튜브에서 실제로 묻는 질문을 모아서 `/ideas`가 쓸 **후보 리포트**를 만든다.
[Agent Reach](https://github.com/Panniantong/Agent-Reach)의 설계를 빌려 와서 이 채널에 맞게 새로 짠 것이다.

## 무엇을 하나

```
queries.json ─▶ 수집 (소스마다 백엔드를 순서대로 시도) ─▶ 원본 저장 (<날짜>-raw.json)
                                                           │
             질문만 고르기 ◀─ 중복 제거 · 기간 필터 ◀───────┘
                  │
                  ▼
     비슷한 질문 묶기 ─▶ 시리즈 판별 ─▶ 훅 추천 ─▶ 수요 점수 1-5 ─▶ <날짜>-questions.md
```

| 단계 | 규칙 (전부 `reach/analyze.py` 위쪽 상수) |
|---|---|
| 수집 | 레딧: `agent-reach`(설치·로그인돼 있으면) → 레딧 공개 JSON. 유튜브: `agent-reach` → `yt-dlp`. 앞의 것이 실패하면 다음 것을 쓰고, 시도는 모두 리포트에 남긴다 |
| 질문 고르기 | `?`가 있거나 Why/How/Is/Any/Best… 로 시작하는 제목. 사진·후기·공지 글은 뺀다 |
| 묶기 | 반응이 큰 글을 씨앗으로 잡고, 키워드가 절반 이상 겹치는 질문을 붙인다 (tip/tipping, store/stores는 같은 단어로 본다) |
| 시리즈 | 키워드가 가장 많이 맞는 시리즈: `explained`(why, rude, tipping…), `tips`(subway, visa, taxi…), `items`(sunscreen, olive young, daiso…), `ranked`(best, snack, convenience…). 안 맞으면 `unsorted` |
| 훅 | `content/hooks.md` ID. 가격 → `price-shock`, A vs B → `vs`, 하지 마 → `dont-do-this`, why → `why-koreans`, best → `ranking`, how → `how-to`. 없으면 시리즈 기본값 |
| 수요 점수 | 글 1개당 3점 + log(추천+1) + log(댓글+1) + 유튜브 log(조회+1)/2 + 커뮤니티 2곳 이상이면 2점. 40점 이상 5, 25 이상 4, 15 이상 3, 8 이상 2, 나머지 1 |

**하지 않는 것:** 글쓰기·댓글·로그인 대행. `content/ideas.md` 직접 수정(이건 `/ideas`가 근거를 확인한 뒤에 한다). 가제·제휴·제작 쉬움 점수(이건 사람의 판단이 필요하다).

## 쓰는 법

```bash
pip install -r requirements.txt
```

```bash
python -m reach collect
```

```bash
python -m reach collect --only reddit --since-days 180 --min-demand 3
```

```bash
python -m reach analyze content/research/2026-11-03-raw.json
```

- 검색어와 서브레딧은 `content/research/queries.json`에서 바꾼다.
- `analyze`는 네트워크를 쓰지 않는다. 우리 raw, Agent Reach 출력(`agent-reach reddit search ... > a.json`), 레딧 JSON, yt-dlp JSONL을 모두 읽는다.
- 테스트는 `python -m unittest tests.test_reach -v`로 돌린다.

## 어디서 돌리나

- **사용자 PC (권장):** 레딧 공개 JSON은 로그인 없이 된다. 막히면 Agent Reach를 설치하고(`docs/install.md` 참고, PyPI 패키지는 다른 프로젝트라 쓰면 안 된다) **부계정**으로 레딧에 로그인해 둔다. 유튜브는 `pip install yt-dlp`를 하면 된다.
- **클라우드 세션:** 환경의 네트워크 허용 목록에 `www.reddit.com`, `www.youtube.com`이 있어야 한다. 없으면 수집이 0개로 끝나고, `/ideas`는 웹 검색만으로 진행한다.
