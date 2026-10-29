# 대본 스키마 v2 (`episodes/<id>/script.json`)

```json
{
  "id": "2026-11-03-olive-young-sunscreen",
  "status": "draft",
  "pillar": "items",
  "hook_type": "everyone-has-this",
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
      "visual": "Jiwoo in her Mapo studio, holding up a small sunscreen tube to camera, surprised face",
      "narration": "Okay, Korean secret time.",
      "caption": "Korean secret time 🤫",
      "asset": null
    },
    {
      "id": 2,
      "type": "product",
      "duration": 4,
      "visual": "Cinematic macro of the sunscreen tube on a bathroom shelf, morning light",
      "narration": "This is the sunscreen you'll find in literally every Korean bathroom.",
      "caption": "In EVERY Korean bathroom",
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
| `hook_type` | `content/hooks.md`의 훅 ID. 성과 분석에서 훅별 성적을 비교할 때 쓴다 |
| `scenes[].type` | `character` (주인공 등장) / `product` (제품 시네마틱) / `broll` (장소·자료 화면) / `text` (자막만) |
| `scenes[].visual` | Higgsfield 생성용 장면 묘사 (영어) |
| `scenes[].narration` | 주인공이 말하는 문장 (영어). 음성으로 생성된다 |
| `scenes[].caption` | 화면 자막. 내레이션보다 짧게 |
| `scenes[].asset` | 제작 후 클립 경로나 Higgsfield job ID가 채워진다 |
