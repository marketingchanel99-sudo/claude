# 대본 스키마 v2 (`episodes/<id>/script.json`)

```json
{
  "id": "2026-11-03-olive-young-sunscreen",
  "status": "draft",
  "pillar": "items",
  "hook_type": "everyone-has-this",
  "hook_candidates": [
    {"hook_type": "everyone-has-this", "line": "Every Korean has this in their bathroom.", "caption": "In EVERY Korean bathroom", "visual": "Jiwoo thrusts the tube toward the camera"},
    {"hook_type": "price-shock", "line": "This sunscreen costs $12 in Korea.", "caption": "$12 in Korea?!", "visual": "Jiwoo slams the tube on the counter, price tag close-up"},
    {"hook_type": "secret", "line": "Koreans don't tell tourists this about sunscreen.", "caption": "Koreans won't tell you 🤫", "visual": "Jiwoo leans in and whispers, hand by mouth"}
  ],
  "language": "en",
  "length_sec": 30,

  "title": "The sunscreen every Korean actually uses",
  "hashtags": ["kbeauty", "koreanskincare", "seoul", "oliveyoung"],
  "platforms": {
    "youtube":   {"title": "The sunscreen every Korean actually uses #Shorts", "description": "..."},
    "instagram": {"caption": "...\n\nLink in bio 🔗"},
    "tiktok":    {"caption": "..."}
  },

  "korean_phrase": {"ko": "진짜 대박", "romanization": "jinjja daebak", "meaning": "seriously amazing"},

  "affiliate": {
    "links": [{"name": "Round Lab Birch Sunscreen", "url": "https://...", "network": "amazon"}],
    "disclosure": "As an affiliate, I earn from qualifying purchases."
  },

  "voice": "<Higgsfield voice_id 또는 edge-tts 음성 이름>",

  "scenes": [
    {
      "id": 1,
      "type": "character",
      "duration": 3,
      "visual": "Jiwoo thrusts the tube toward the camera in her Mapo studio, surprised face",
      "narration": "Every Korean has this in their bathroom.",
      "caption": "In EVERY Korean bathroom",
      "asset": null
    },
    {
      "id": 2,
      "type": "product",
      "duration": 4,
      "visual": "Cinematic macro of the sunscreen tube on a bathroom shelf, morning light",
      "narration": "Okay, Korean secret time. This is Round Lab birch sunscreen.",
      "caption": "Round Lab Birch",
      "asset": null
    }
  ],

  "sources": ["https://... (가격·성분·주장의 근거)"],
  "notes": "자유 메모"
}
```

## 필드 설명

| 필드 | 설명 |
|---|---|
| `status` | `draft` → `approved` (사람 승인) → `produced` → `published` |
| `pillar` | 시리즈 코드: `items` (Korean Secret) / `explained` (Why Koreans…?) / `tips` (Seoul Survival) / `ranked` (Ranked) / `brand` (협찬) |
| `hook_type` | 최종 선택한 훅의 ID (`content/hooks.md`). 성과 분석에서 훅별 성적을 비교할 때 쓴다 |
| `hook_candidates` | 서로 다른 템플릿으로 만든 훅 후보 3개 (말, 자막, 첫 화면). 사용자가 고른 것이 `scenes[0]`이 된다 |
| `scenes[].type` | `character` (주인공 등장) / `product` (제품 시네마틱) / `broll` (장소·자료 화면) / `text` (자막만) |
| `scenes[].visual` | Higgsfield 생성용 장면 묘사 (영어) |
| `scenes[].narration` | 주인공이 말하는 문장 (영어). 음성으로 생성된다 |
| `scenes[].caption` | 화면 자막. 내레이션보다 짧게 |
| `scenes[].caption` 강조 | 대괄호로 강조 단어 1개를 표시한다: `"This is [#1] at Olive Young"`. 렌더러가 코랄 배경으로 강조하고 swish 효과음을 넣는다 (첫 장면은 훅 자막이라 강조 없음) |
| `scenes[].asset` | 장면 재료 파일 경로 (에피소드 폴더 기준, 예: `assets/hook.mp4`, `assets/product1.png`). 영상이면 그 소리를 쓰고, 이미지면 줌인 효과를 준다. 비어 있으면 회색 자리 표시로 미리보기 렌더링 |
| `scenes[].audio` | (선택) 내레이션 음성 파일 경로. 있으면 영상 소리보다 우선한다 |
| `scenes[].job_id` | (선택) 재료를 만든 Higgsfield job ID. 재생성·추적용 |
