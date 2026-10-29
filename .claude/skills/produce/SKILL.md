---
name: produce
description: 승인된 대본으로 영상 제작. Higgsfield로 장면 클립과 음성을 만들고 final.mp4로 합친다. "영상 만들어줘", "/produce <id>" 요청 시 사용.
---

1. `episodes/<id>/script.json`을 읽는다. `status`가 `approved`가 아니면 멈추고 대본 승인을 먼저 요청한다.
2. 장면 타입별 생성:
   - `character`: 바이블의 캐릭터 시트(job ID)를 참조 이미지로 넣어 같은 얼굴을 유지한다.
   - `product`: 제품 사진이 `assets/`에 있으면 참조로 쓰고, 없으면 사용자에게 요청한다 (제휴 영상은 실제 제품과 같아야 한다).
   - `broll`: 장소·분위기 영상.
3. 생성 전에 전체 예상 크레딧을 `get_cost`로 합산해 보여준다. 150 크레딧을 넘으면 승인을 받는다.
4. 모든 job ID와 결과 URL을 `episodes/<id>/shots.json`에 기록한다.
5. 내레이션 음성은 바이블에 고정된 음성으로 생성한다.
6. 클립, 음성, 자막을 합쳐 `episodes/<id>/final.mp4` (1080x1920)를 만든다.
7. ✋ 최종 영상을 보여주고 확인을 받는다. 확인되면 `status`를 `produced`로 바꾼다.
