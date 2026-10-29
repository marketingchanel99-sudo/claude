---
name: produce
description: 승인된 대본으로 영상 제작. Higgsfield로 장면 클립과 음성을 만들고 final.mp4로 합친다. "영상 만들어줘", "/produce <id>" 요청 시 사용.
---

1. `episodes/<id>/script.json`을 읽는다. `status`가 `approved`가 아니면 멈추고 대본 승인을 먼저 요청한다.
2. 장면 타입별 생성:
   - `character`: 바이블의 캐릭터 시트(job ID)를 참조 이미지로 넣어 같은 얼굴을 유지한다. 목소리는 바이블의 음성 설명을 그대로 쓰고, 복제 음성이 있으면 오디오 참조로 넣는다.
   - **첫 장면(훅)은 `content/hooks.md`의 "훅 장면 영상 생성 규칙"을 반드시 따른다** (타임코드, 0초 동작·발화, 4초).
   - `product`: 제품 사진이 `assets/`에 있으면 참조로 쓰고, 없으면 사용자에게 요청한다 (제휴 영상은 실제 제품과 같아야 한다).
   - `broll`: 장소·분위기 영상.
3. 생성 전에 `content/budget.md`를 읽고, 전체 예상 크레딧을 `get_cost`로 합산해 잔액과 함께 보여주고 **매번 승인을 받는다**. 영상 1개 상한은 100, 평균 목표는 70 이하. 생성 후 사용 기록에 적는다.
4. 모든 job ID와 결과 URL을 `episodes/<id>/shots.json`에 기록한다.
5. 내레이션 음성은 바이블에 고정된 음성으로 생성한다.
6. 재료를 `episodes/<id>/assets/`에 두고 `scenes[].asset`·`audio`에 경로를 적은 뒤 렌더링한다:
   `python -m reels.render episodes/<id>/script.json --bgm assets/bgm/<시그니처>.mp3`
   라벨, 훅 자막, 본문 자막(강조 단어), 효과음, 배경음은 렌더러가 `docs/STYLE_GUIDE.md`대로 넣는다. 재료 없이 먼저 돌리면 자막·타이밍만 확인하는 미리보기가 나온다.
7. ✋ 최종 영상을 보여주고 확인을 받는다. 확인되면 `status`를 `produced`로 바꾼다.
