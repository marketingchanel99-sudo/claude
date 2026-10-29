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
| `pillar` | `items` / `explained` / `tips` / `brand` |
| `hook_type` | 최종 선택한 훅의 ID (`content/hooks.md`). 성과 분석에서 훅별 성적을 비교할 때 쓴다 |
| `hook_candidates` | 서로 다른 템플릿으로 만든 훅 후보 3개 (말, 자막, 첫 화면). 사용자가 고른 것이 `scenes[0]`이 된다 |
| `scenes[].type` | `character` (주인공 등장) / `product` (제품 시네마틱) / `broll` (장소·자료 화면) / `text` (자막만) |
| `scenes[].visual` | Higgsfield 생성용 장면 묘사 (영어) |
| `scenes[].narration` | 주인공이 말하는 문장 (영어). 음성으로 생성된다 |
| `scenes[].caption` | 화면 자막. 내레이션보다 짧게 |
| `scenes[].asset` | 제작 후 클립 경로나 Higgsfield job ID가 채워진다 |
