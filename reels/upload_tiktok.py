"""틱톡 업로드 (TikTok Content Posting API, Direct Post).

필요: video.publish 스코프로 발급한 사용자 액세스 토큰.
토큰은 24시간마다 만료되므로 TIKTOK_REFRESH_TOKEN과 클라이언트 키/시크릿을 넣어두면 자동 갱신한다.
TikTok 심사를 통과하기 전의 앱은 SELF_ONLY(나만 보기)로만 게시할 수 있다.
"""
import math
import os
import time
from pathlib import Path

import requests

API = "https://open.tiktokapis.com/v2"
MAX_SINGLE_CHUNK = 64 * 1024 * 1024
CHUNK = 10 * 1024 * 1024


def _access_token() -> str:
    refresh = os.getenv("TIKTOK_REFRESH_TOKEN")
    if refresh and os.getenv("TIKTOK_CLIENT_KEY"):
        r = requests.post(
            f"{API}/oauth/token/",
            data={
                "client_key": os.environ["TIKTOK_CLIENT_KEY"],
                "client_secret": os.environ["TIKTOK_CLIENT_SECRET"],
                "grant_type": "refresh_token",
                "refresh_token": refresh,
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["access_token"]
    return os.environ["TIKTOK_ACCESS_TOKEN"]


def upload(video: Path, meta: dict) -> str:
    headers = {"Authorization": f"Bearer {_access_token()}", "Content-Type": "application/json; charset=UTF-8"}
    size = video.stat().st_size
    # 64MB 이하면 한 번에, 그보다 크면 10MB 단위 (마지막 조각이 나머지를 포함)
    chunk_size = size if size <= MAX_SINGLE_CHUNK else CHUNK
    chunks = 1 if chunk_size == size else math.floor(size / chunk_size)

    title = meta.get("platforms", {}).get("tiktok", {}).get("caption") or f"{meta['title']} " + " ".join(
        f"#{t}" for t in meta.get("hashtags", [])
    )
    r = requests.post(
        f"{API}/post/publish/video/init/",
        headers=headers,
        json={
            "post_info": {
                "title": title[:2200],
                "privacy_level": os.getenv("TIKTOK_PRIVACY", "SELF_ONLY"),
                "is_aigc": True,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": size,
                "chunk_size": chunk_size,
                "total_chunk_count": chunks,
            },
        },
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()["data"]

    with video.open("rb") as f:
        for i in range(chunks):
            start = i * chunk_size
            end = size - 1 if i == chunks - 1 else start + chunk_size - 1
            f.seek(start)
            requests.put(
                data["upload_url"],
                headers={"Content-Type": "video/mp4", "Content-Range": f"bytes {start}-{end}/{size}"},
                data=f.read(end - start + 1),
                timeout=600,
            ).raise_for_status()

    for _ in range(60):
        status = requests.post(
            f"{API}/post/publish/status/fetch/", headers=headers, json={"publish_id": data["publish_id"]}, timeout=30
        ).json()["data"]
        if status["status"] == "PUBLISH_COMPLETE":
            return f"publish_id={data['publish_id']}"
        if status["status"] == "FAILED":
            raise RuntimeError(f"틱톡 게시 실패: {status.get('fail_reason')}")
        time.sleep(5)
    raise TimeoutError("틱톡 처리 대기 시간 초과")
