# 릴스 오토파일럿

Claude Code에 **말로 시키면** 숏폼 영상을 만들고 **유튜브 쇼츠 · 인스타 릴스 · 틱톡**에 동시에 올리는 파이프라인.

```
대본 JSON ──▶ make_video (TTS 음성 + 배경 줌 + 자막) ──▶ 1080x1920 mp4 ──▶ upload_all ──▶ YouTube / Instagram / TikTok
```

## 1. 설치 (한 번만)

준비물: Python 3.10+, [ffmpeg](https://ffmpeg.org/download.html)

```bash
python -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
cp .env.example .env
```

## 2. 영상 만들기

```bash
python -m reels.make_video scripts/example.json
```

결과: `output/example.mp4`. 음성은 Microsoft Edge TTS(무료, 한국어 `ko-KR-SunHiNeural` / `ko-KR-InJoonNeural`)를 사용한다.

대본 형식 (`scripts/*.json`):

| 필드 | 설명 |
|---|---|
| `title`, `description`, `hashtags` | 업로드할 때 제목, 설명, 해시태그로 사용 |
| `voice`, `rate` | TTS 목소리, 속도 (예: `"+10%"`) |
| `scenes[].text` | 화면 자막 (`\n`으로 줄바꿈) |
| `scenes[].narration` | (선택) 자막과 다르게 읽을 문장 |
| `scenes[].image` | (선택) 배경 이미지 경로 (대본 JSON 기준 상대경로). 없으면 그라데이션 배경 |

`--no-tts`를 붙이면 음성 없이 자막만 들어간 영상을 만든다 (배경음악을 따로 깔 때 사용).

## 3. 업로드

먼저 무엇이 올라갈지 확인:

```bash
python -m reels.upload_all output/example.mp4 scripts/example.json --dry-run
```

3개 플랫폼에 동시 업로드:

```bash
python -m reels.upload_all output/example.mp4 scripts/example.json
```

일부만 올릴 때:

```bash
python -m reels.upload_all output/example.mp4 scripts/example.json --only youtube,tiktok
```

## 4. 플랫폼 연결 (`.env` 채우기)

### YouTube 쇼츠
1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트를 만들고 **YouTube Data API v3**를 사용 설정
2. OAuth 동의 화면을 설정하고 본인을 테스트 사용자로 추가
3. 사용자 인증 정보에서 **OAuth 클라이언트 ID (데스크톱 앱)**를 만든 뒤 JSON을 받아 `client_secret.json`으로 저장
4. 첫 업로드 때 브라우저 로그인 창이 뜬다. 이후에는 `token_youtube.json`으로 자동 로그인

### 인스타그램 릴스
1. 인스타 계정을 **비즈니스 또는 크리에이터**로 전환하고 페이스북 페이지에 연결
2. [Meta for Developers](https://developers.facebook.com/)에서 앱을 만들고 Instagram Graph API를 추가
3. `instagram_basic`, `instagram_content_publish` 권한이 있는 **장기 액세스 토큰**을 발급해 `IG_ACCESS_TOKEN`에 입력
4. `IG_USER_ID`: 인스타 비즈니스 계정 ID

### 틱톡
1. [TikTok for Developers](https://developers.tiktok.com/)에서 앱을 만들고 **Content Posting API (Direct Post)**를 추가
2. `video.publish` 스코프로 OAuth 인증을 받아 액세스 토큰과 리프레시 토큰을 `.env`에 입력
3. **TikTok 심사를 통과하기 전의 앱은 `SELF_ONLY`(나만 보기)로만 게시할 수 있다.** 심사를 통과하면 `TIKTOK_PRIVACY=PUBLIC_TO_EVERYONE`으로 바꾼다.

## 5. Claude Code로 말로 시키기

채널 운영 전체 흐름은 [docs/WORKFLOW.md](docs/WORKFLOW.md) 참고.

이 폴더에서 `claude`를 실행하고 이렇게 말하면 된다:

> "다이어트 꿀팁 주제로 30초 릴스 만들어서 세 군데 다 올려줘"

Claude Code는 `CLAUDE.md`의 작업 순서에 따라 대본 작성, 영상 생성, 미리보기 확인, 업로드를 진행한다.

## 주의
- 각 플랫폼은 AI로 만든 콘텐츠에 표시를 요구한다. 업로더는 기본으로 AI 생성 표시를 켠다 (YouTube `containsSyntheticMedia`, TikTok `is_aigc`).
- `.env`, `client_secret*.json`, `token_*.json`은 `.gitignore`에 들어 있다. 절대 커밋하지 말 것.
