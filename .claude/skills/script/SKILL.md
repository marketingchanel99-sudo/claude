---
name: script
description: 에피소드 대본 작성. 캘린더 항목으로 episodes/<id>/script.json을 스키마 v2로 만든다. "대본 써줘", "/script <id>" 요청 시 사용.
---

1. `character/bible.md`(말투, 입버릇, 금지 사항), `docs/script-schema.md`, `content/hooks.md`, 해당 주 캘린더 항목을 읽는다.
2. 사실 관련 내용(가격, 성분, 문화적 이유)은 웹에서 확인하고 `sources`에 남긴다. 확인 못 한 주장은 쓰지 않는다.
3. 대본 원칙:
   - 0~3초: 훅 템플릿으로 시작. 첫 장면은 `character` 타입.
   - 길이 20~40초, 장면 5~8개, 장면당 내레이션 한 문장.
   - 영어 내레이션, 한국어는 `korean_phrase`와 포인트로만.
   - 마지막 장면: 바이블의 엔딩 입버릇 + 행동 유도 (저장/팔로우/댓글 키워드).
   - 제휴가 있으면 `affiliate.disclosure`를 넣고 플랫폼별 캡션에도 포함.
4. 플랫폼별 제목·캡션을 각각 쓴다 (YouTube 제목 100자 이내, `#Shorts` 포함).
5. `episodes/<id>/script.json`을 `status: "draft"`로 저장한다.
6. ✋ 장면표(장면 / 화면 / 내레이션 / 자막) 형태로 보여주고 승인을 받는다. 승인되면 `status`를 `approved`로 바꾼다.
