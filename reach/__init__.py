"""Jiwoo Reach: 외국인이 실제로 묻는 질문을 모아 `/ideas`에 넘길 후보로 정리한다.

Agent Reach(https://github.com/Panniantong/Agent-Reach)의 설계를 빌려 왔다.
- 소스마다 백엔드 목록을 순서대로 시도한다 (앞의 것이 실패하면 다음 것).
- 결과는 한 가지 모양(Post)으로 통일한다.
- 읽기만 한다. 글쓰기, 댓글, 로그인 대행은 하지 않는다.

그 위에 이 채널만의 로직을 얹는다.
- 질문 판별 → 비슷한 질문끼리 묶기 → 시리즈·훅 추천 → 수요 점수(1-5)
- 결과는 `content/research/`에 원본 JSON과 후보 리포트(md)로 남긴다.
  `content/ideas.md`에는 직접 쓰지 않는다. `/ideas`가 근거를 확인한 뒤 옮긴다.

    python -m reach collect                      # content/research/queries.json대로 수집 + 분석
    python -m reach analyze <raw.json> [...]     # 저장해 둔 결과(우리 raw, Agent Reach 출력, 레딧 JSON)만 분석
"""
