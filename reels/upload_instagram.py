"""인스타그램 릴스 업로드 (Instagram Graph API, resumable 업로드).

로컬 파일을 그대로 올리므로 영상을 공개 URL에 따로 호스팅하지 않아도 된다.
필요: 비즈니스/크리에이터 계정, IG_USER_ID, instagram_content_publish 권한이 있는 IG_ACCESS_TOKEN.
"""
import os
import time
from pathlib import Path

import requests


def upload(video: Path, meta: dict) -> str:
    user_id = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]
    graph = f"https://graph.facebook.com/{os.getenv('IG_GRAPH_VERSION', 'v23.0')}"
    caption = meta.get("platforms", {}).get("instagram", {}).get("caption") or (
        f"{meta['title']}\n\n{meta.get('description', '')}\n\n" + " ".join(f"#{t}" for t in meta.get("hashtags", []))
    )

    # 1) 업로드용 컨테이너 생성
    r = requests.post(
        f"{graph}/{user_id}/media",
        data={"media_type": "REELS", "upload_type": "resumable", "caption": caption, "access_token": token},
        timeout=60,
    )
    r.raise_for_status()
    container = r.json()["id"]

    # 2) 파일 바이트 전송
    data = video.read_bytes()
    r = requests.post(
        r.json()["uri"],
        headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(len(data))},
        data=data,
        timeout=600,
    )
    r.raise_for_status()

    # 3) 인스타그램 쪽 처리가 끝날 때까지 대기
    for _ in range(60):
        status = requests.get(
            f"{graph}/{container}", params={"fields": "status_code,status", "access_token": token}, timeout=30
        ).json()
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") == "ERROR":
            raise RuntimeError(f"인스타그램 처리 실패: {status}")
        time.sleep(5)
    else:
        raise TimeoutError("인스타그램 처리 대기 시간 초과")

    # 4) 게시
    r = requests.post(
        f"{graph}/{user_id}/media_publish", data={"creation_id": container, "access_token": token}, timeout=60
    )
    r.raise_for_status()
    media_id = r.json()["id"]
    link = requests.get(
        f"{graph}/{media_id}", params={"fields": "permalink", "access_token": token}, timeout=30
    ).json()
    return link.get("permalink", f"media_id={media_id}")
