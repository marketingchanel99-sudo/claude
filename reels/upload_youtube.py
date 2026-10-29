"""YouTube 쇼츠 업로드 (YouTube Data API v3).

세로 영상이고 3분 이하이면 YouTube가 자동으로 쇼츠로 분류한다.
처음 실행할 때 브라우저가 열려 로그인하고, 토큰은 token_youtube.json에 저장된다.
"""
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN = Path("token_youtube.json")


def _credentials() -> Credentials:
    creds = Credentials.from_authorized_user_file(TOKEN, SCOPES) if TOKEN.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        secret = os.getenv("YOUTUBE_CLIENT_SECRET", "client_secret.json")
        creds = InstalledAppFlow.from_client_secrets_file(secret, SCOPES).run_local_server(port=0)
    TOKEN.write_text(creds.to_json())
    return creds


def upload(video: Path, meta: dict) -> str:
    tags = meta.get("hashtags", [])
    custom = meta.get("platforms", {}).get("youtube", {})
    title = custom.get("title", meta["title"])
    if "#shorts" not in title.lower():
        title = f"{title} #Shorts"
    body = {
        "snippet": {
            "title": title[:100],
            "description": custom.get("description")
            or f"{meta.get('description', '')}\n\n" + " ".join(f"#{t}" for t in tags),
            "tags": tags,
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": os.getenv("YOUTUBE_PRIVACY", "public"),
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": True,
        },
    }
    youtube = build("youtube", "v3", credentials=_credentials())
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=MediaFileUpload(str(video), chunksize=-1, resumable=True)
    )
    response = None
    while response is None:
        _, response = request.next_chunk()
    return f"https://youtube.com/shorts/{response['id']}"
