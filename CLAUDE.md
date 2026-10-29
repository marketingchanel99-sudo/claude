# 채널 운영 시스템: Claude Code 작업 규칙

이 저장소는 외국인 대상 "한국 생활템·문화" 숏폼 채널을 운영하는 시스템이다.
전체 흐름은 [docs/WORKFLOW.md](docs/WORKFLOW.md)를 따른다.

## 항상 지킬 것
- 대본, 기획, 캡션을 쓰기 전에 [character/bible.md](character/bible.md)를 읽고 주인공의 말투와 금지 사항을 따른다.
- ✋ 승인 지점(캘린더, 대본, 최종 영상, 업로드)에서는 멈추고 사용자의 확인을 받는다. 승인 없이 다음 단계로 넘어가지 않는다.
- 업로드는 사용자가 요청했을 때만 하고, 항상 `--dry-run`을 먼저 보여준다.
- **크레딧은 한 달 치다. 바닥나면 안 된다.** 규칙은 [content/budget.md](content/budget.md)를 따른다.
  - Higgsfield로 무언가 생성하기 전에는 **매번** 잔액과 예상 비용을 보여주고 승인을 받는다 (비용 조회 `get_cost`는 무료라 승인 없이 해도 된다).
  - 테스트는 480p 초안으로만 한다. 잔액이 비상금(450) 이하로 내려가면 생성하지 않는다.
  - 생성한 뒤에는 `content/budget.md` 사용 기록에 적는다.
- 제휴 링크가 있는 영상은 고지 문구 없이 업로드하지 않는다.
- 확인되지 않은 사실(가격, 성분, 문화적 이유)은 쓰지 않는다. 근거는 `sources`에 남긴다.

## 단계별 스킬
| 요청 | 스킬 |
|---|---|
| 주제·아이디어 찾기 | `/ideas` |
| 주간 캘린더 | `/plan-week` |
| 대본 | `/script <에피소드 ID>` |
| 영상 제작 | `/produce <에피소드 ID>` |
| 업로드 | `/publish <에피소드 ID>` |
| 성과 분석 | `/review` |

## 파일 위치
- 대본 스키마: `docs/script-schema.md`
- 아이디어 백로그: `content/ideas.md`, 훅 템플릿: `content/hooks.md`
- 에피소드: `episodes/<YYYY-MM-DD-slug>/` (script.json, shots.json, assets/, final.mp4)
- 렌더러·업로더 코드: `reels/`
