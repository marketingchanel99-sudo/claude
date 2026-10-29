# 훅 규칙과 템플릿

첫 3초에 시청자의 80%가 넘길지 말지를 정한다. 훅은 **말 + 화면 + 소리 + 자막**이 0초에 동시에 터져야 한다.
`reels/check_script.py`가 아래 "자동 검사" 항목을 검사한다.

## 3박자 규칙

| 요소 | 규칙 | 자동 검사 |
|---|---|---|
| **말** | 첫 문장이 곧 훅. 인사·자기소개·입버릇으로 시작하지 않는다. 10단어 이내 | ✅ 단어 수, 금지 시작어 |
| **화면** | 첫 프레임부터 움직임이 있다 (주인공이 제품을 들이밀기, 카메라 푸시인, 손동작). 로고·타이틀 카드·정지 화면 금지 | ✅ `visual`에 동작 묘사 여부 |
| **자막** | 0초부터 화면 상단 1/3에 큰 자막. 훅 문장을 그대로 쓰지 말고 6단어 이내로 압축 | ✅ 자막 유무, 단어 수 |
| **소리** | 첫 0.1초부터 소리가 난다 (목소리 또는 효과음). 무음 시작 금지 | 제작 단계에서 확인 |
| **길이** | 첫 장면은 3초 이하 | ✅ |
| **호기심 간격** | 훅에서 답을 주지 않는다. 답은 2번째 장면 이후에 | 대본 검토 시 확인 |

금지 시작어: `Hi`, `Hello`, `Hey guys`, `Welcome`, `Today`, `In this video`, `So`, `Okay`, `My name`

## 훅 장면 영상 생성 규칙 (Higgsfield 프롬프트)

동작을 "A 하고, B 하고, 말한다"처럼 순서대로 쓰면 모델이 그 순서대로 천천히 연기해서 훅이 죽는다 (2026-10-29 테스트에서 확인).

- **타임코드로 쓴다:** `0.0s:` `1.5s:` 처럼 초 단위로 무엇이 일어나는지 지정한다.
- **0.0초에 이미 동작 중:** "already mid-motion at the first frame". 기울이기, 들어 올리기 같은 준비 동작을 쓰지 않는다.
- **0.0초에 말 시작:** "starts speaking instantly at 0.0s". 대사는 2초 안에 끝낸다.
- **빠르고 에너지 있는 전달:** "fast, punchy, energetic delivery", "no pause before speaking".
- **장면 길이는 최소(4초)로:** 길이가 길면 모델이 동작을 늘어뜨린다. 남는 시간은 리액션(눈썹 올리기, 씩 웃기)으로 채운다.
- **카메라도 움직인다:** "fast handheld push-in" 또는 "quick whip-in".
- **자막·효과음은 편집에서 얹는다:** 원본 클립에 글자를 넣지 않는다 (`no text`). 훅 자막과 0초 효과음(whoosh, pop)은 `final.mp4` 합성 단계에서 넣는다.

## 템플릿

대본마다 서로 다른 템플릿으로 **후보 3개**를 만들고 사용자가 고른다 (`script.json`의 `hook_candidates`).
`script.json`의 `hook_type`에 고른 ID를 적고, `/review`가 템플릿별 3초 유지율을 `content/hook-stats.md`에 쌓는다.

| ID | 템플릿 | 예시 | 첫 화면 예시 |
|---|---|---|---|
| `everyone-has-this` | Every Korean has ___ | Every Korean has this in their bathroom. | 주인공이 제품을 카메라 쪽으로 쭉 내민다 |
| `why-koreans` | Why do Koreans ___? | Why do Koreans never tip? | 계산대에서 카드를 내미는 손, 고개를 갸웃하는 주인공 |
| `dont-do-this` | Don't ___ in Korea | Don't do this on the Seoul subway. | 주인공이 손으로 X자를 그리며 다가온다 |
| `secret` | Koreans don't tell tourists this | Koreans don't tell tourists this about Olive Young. | 주인공이 주위를 살피고 귓속말하는 제스처 |
| `ranking` | I ranked ___ so you don't have to | I ranked every Korean convenience store snack. | 과자 10개가 테이블에 쏟아진다 |
| `whats-inside` | What's inside a Korean ___'s ___ | What's inside a Korean office worker's bag? | 가방 지퍼를 확 여는 클로즈업 |
| `how-to` | How to ___ like a local | How to use T-money like a local. | 개찰구에 카드를 탁 찍는 순간 |
| `price-shock` | This costs ___ in Korea | This costs $3 in Korea. | 제품을 들고 놀란 표정, 가격표 클로즈업 |
| `vs` | Korea vs ___: ___ | Korean vs American sunscreen. | 양손에 제품 하나씩 들고 저울질 |
| `pov` | POV: you ___ in Seoul | POV: your first Korean sauna. | 1인칭 시점으로 문을 열고 들어간다 |
