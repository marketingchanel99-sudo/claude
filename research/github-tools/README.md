# GitHub 마케팅 AI 툴 쉽게 이해하기 (레포별 PDF 원고)

구글 드라이브 스프레드시트 「GitHub 마케팅 AI 툴 리서치 (숏폼·릴스·벤치마킹·기획)」의 레포 159개를
중학생도 이해할 수 있게 설명한 2쪽짜리 PDF의 원고와 렌더러.

- `repos.tsv`: 순위, 카테고리, 레포, 스타 수 (시트 기준)
- `content/NNN.json`: 레포별 원고. 각 레포 README만 근거로 작성 (`sources`에 근거 메모)
- `SCHEMA.md`: 원고 작성 규칙
- `render.py`: 원고 → PDF (비유 그림, 작동 흐름도, 기능 아이콘, 난이도 게이지). 용도별 9개 폴더로 분류
- `index.py`: 전체 목록·폴더 안내 PDF

PDF 다시 만들기 (원고 수정 후):

```bash
pip install reportlab
python3 render.py && python3 index.py   # pdf/<폴더>/NNN_이름.pdf
```

PDF는 표준 한글 CID 폰트(HYGothic-Medium)를 내장하지 않고 참조해서 파일당 약 12KB입니다.

## v2 상세판 (원리·구조도·실제 화면·따라 하기 포함)

- `SCHEMA2.md`: v2 원고 규칙 (principle, architecture, howto, scenario, compare, faq, images 추가)
- `render2.py` + `pdf.js`: HTML을 만들고 Chromium(Playwright)으로 PDF 출력. 나눔고딕 폰트를 PDF에 넣어 어느 뷰어에서도 한글이 깨지지 않음
- `index2.py`: 전체 목록 PDF
- `images/`: README에서 가져온 실제 화면 (출처는 각 레포 README)
- 폰트는 저장소에 넣지 않았어요. `fonts/`에 NanumGothic-Regular/Bold/ExtraBold, NanumGothicCoding-Regular(.ttf, google/fonts 저장소의 ofl/nanumgothic*)를 두고 실행하세요.

```bash
NODE_PATH=$(npm root -g) python3 render2.py && NODE_PATH=$(npm root -g) python3 index2.py
```
