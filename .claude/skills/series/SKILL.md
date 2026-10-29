---
name: series
description: 시리즈 포맷 작성·수정. content/series/<시리즈>.md에 장면 구성, 길이, 고정 멘트, 주제 기준을 정한다. "시리즈 포맷 만들어줘", "시리즈 구성 바꾸자" 요청 시 사용.
---

1. `docs/MASTER_PLAN.md`(시리즈 정의), `docs/WORKFLOW.md`(비율·길이), `character/bible.md`, `content/hooks.md`, `docs/STYLE_GUIDE.md`, `content/series/_TEMPLATE.md`를 읽는다.
2. 벤치마킹: 같은 유형의 인기 숏폼(영어권, 한국 소개·제품 소개)의 구성을 웹에서 조사하고, 참고한 출처를 문서 끝에 남긴다.
3. `_TEMPLATE.md` 형식으로 `content/series/<slug>.md`를 쓴다.
   - 장면 구성표는 초 단위로 쓰고, 합계가 시리즈 길이 범위 안에 들어가야 한다.
   - 첫 장면은 훅 규칙(`content/hooks.md`)을 따른다. 영상(크레딧)이 필요한 장면은 훅과 꼭 움직여야 하는 컷만으로 제한한다 (`content/budget.md` 규칙 5).
   - 지우가 "써 봤다"고 말하는 구조를 만들지 않는다. 근거(랭킹, 리뷰 수, 한국인 사용 비율)가 들어갈 자리를 만든다.
4. 예시로 실제 주제 1개를 골라 장면 구성표를 채워 보여준다.
5. ✋ 사용자 승인을 받는다. 승인되면 `content/series/README.md` 상태를 ✅로 바꾸고, 수정이면 변경 기록에 날짜·이유를 남긴다.
