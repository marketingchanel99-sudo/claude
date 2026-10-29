---
name: publish
description: 완성 영상을 쇼츠·릴스·틱톡에 업로드. "/publish <id>", "올려줘" 요청 시 사용.
---

1. `episodes/<id>/script.json`의 `status`가 `produced`인지 확인한다.
2. dry-run을 먼저 실행해서 보여준다:
   `python -m reels.upload_all episodes/<id>/final.mp4 episodes/<id>/script.json --dry-run`
3. 제휴 영상이면 캡션에 고지 문구가 있는지 확인한다. 없으면 업로드하지 않는다.
4. ✋ 승인을 받은 뒤 업로드한다. 일부 플랫폼만 원하면 `--only`를 쓴다.
5. 결과 링크를 `script.json`의 `published` 필드에 기록하고 `status`를 `published`로 바꾼다.
6. 실패한 플랫폼은 원인(토큰 만료, 권한, 용량)과 해결 방법을 알려준다.
