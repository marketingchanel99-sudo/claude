---
name: plan-month
description: 다음 달 30일 업로드 캘린더 작성. 시리즈 비율대로 아이디어와 상품을 날짜에 배치한다. "다음 달 기획", "월간 캘린더" 요청 시 사용.
---

1. `docs/WORKFLOW.md`(시리즈 비율), `content/ideas.md`, `content/products.md`, `content/budget.md`(남은 예산), 최근 `content/reports/`를 읽는다.
2. 예산 점검: 남은 크레딧 - 비상금을 영상 수로 나눠 편당 예산을 계산한다. 평균 70을 넘으면 편수를 줄이거나 이미지 중심 구성으로 바꾸자고 제안한다.
3. 30일(또는 다음 지급일까지)에 배치한다:
   - 시리즈 비율: Korean Secret 40%, Why Koreans 25%, Seoul Survival 25%, Ranked 10%
   - 같은 시리즈 이틀 연속 금지. 첫 주에는 시리즈 4개가 모두 한 번씩 나오게 한다 (반응 비교).
   - 시즌 이슈(명절, 블랙프라이데이, 수능, 연말, 여행 성수기)는 날짜에 맞춘다.
   - 제휴 상품은 `ready` 또는 `candidate` 상태인 것만 쓴다.
4. `content/calendar/<YYYY-MM>.md`를 만든다. 항목마다: 날짜, 에피소드 ID(`YYYY-MM-DD-영문-슬러그`), 시리즈, 가제, 훅 후보 템플릿, 상품(있으면), 근거 링크, 예상 크레딧.
5. 사용한 아이디어의 상태를 `scheduled`로 바꾼다.
6. ✋ 캘린더를 보여주고 승인을 받는다.
