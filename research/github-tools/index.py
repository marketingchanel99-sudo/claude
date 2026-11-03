"""Build 000 index PDF: folder guide + per-folder list of every repo with its one-liner."""
import json, os, glob
import render as R
from reportlab.lib.colors import HexColor, white

work = os.path.dirname(os.path.abspath(__file__))
rows = R.load_rows(work)
items = []
for fp in sorted(glob.glob(os.path.join(work, 'content', '*.json'))):
    j = json.load(open(fp, encoding='utf-8'))
    r = rows[int(j['rank'])]
    folder, col = R.CAT2FOLDER[r['category']]
    items.append(dict(rank=r['rank'], name=j['name'], repo=r['repo'], cat=r['category'], folder=folder, col=col,
                      one=j['one_liner'], diff=int(j['difficulty']), stars=r['stars'], caution=bool(j.get('caution', '').strip())))

out = os.path.join(work, 'pdf', '000_전체 목록과 폴더 안내.pdf')
d = R.Doc(out, '000 GitHub 마케팅 AI 툴 159개 - 전체 목록과 폴더 안내')
d.foot = 'GitHub 마케팅 AI 툴 쉽게 이해하기  ·  전체 목록  ·  README 기준 정리 (2026-11)'
c = d.c; W, H, M = R.W, R.H, R.M
c.setFillColor(HexColor('#111827')); c.rect(0, H - 170, W, 170, fill=1, stroke=0)
for k, (_, col, _) in enumerate(R.FOLDERS):
    c.setFillColor(HexColor(col)); c.circle(W - 60 - (k % 3) * 34, H - 40 - (k // 3) * 34, 13, fill=1, stroke=0)
d.text(M, H - 50, 'GitHub 마케팅 AI 툴', 13, HexColor('#9ca3af'))
d.text(M, H - 88, f'{len(items)}개 레포, 쉽게 이해하기', 26, white, bold=True)
d.text(M, H - 116, '숏폼·릴스 기획, 벤치마킹, 제작, 배포에 쓰는 오픈소스를 용도별로 정리했어요.', 10.5, HexColor('#d1d5db'))
d.text(M, H - 136, '레포마다 PDF 한 개(2쪽): 비유 그림, 작동 흐름도, 핵심 기능, 우리 채널 활용법, 난이도', 10.5, HexColor('#d1d5db'))
d.y = H - 192

d.heading('폴더 안내 (용도별 9개)', '#111827')
bw = (W - 2 * M - 12) / 2; bh = 50
for k, (name, col, cats) in enumerate(R.FOLDERS):
    if k % 2 == 0:
        d.need(bh + 8); top = d.y
    x = M + (k % 2) * (bw + 12)
    n = sum(1 for i in items if i['folder'] == name)
    c.setFillColor(R.tint(col, 0.1)); c.roundRect(x, top - bh, bw, bh, 8, fill=1, stroke=0)
    c.setFillColor(HexColor(col)); c.roundRect(x, top - bh, 6, bh, 3, fill=1, stroke=0)
    d.text(x + 16, top - 20, name[3:], 10.5, R.INK, bold=True)
    d.text(x + 16 + R.sw(name[3:], 10.5) + 8, top - 20, f'{n}개', 10.5, HexColor(col), bold=True)
    cl = R.wrap(', '.join(cats), 8, bw - 26)
    d.text(x + 16, top - 36, cl[0] + (' …' if len(cl) > 1 else ''), 8, R.SUB)
    if k % 2 == 1 or k == len(R.FOLDERS) - 1:
        d.y = top - bh - 8

d.heading('읽는 법', '#111827')
for t in ('난이도 1~5: 1은 앱처럼 바로 사용, 5는 개발 지식과 고성능 그래픽카드(GPU)가 필요해요.',
          '[주의] 표시: 약관·저작권·라이선스(상업 이용 제한 등) 주의 사항이 있는 레포예요. 해당 PDF 마지막의 노란 상자를 꼭 읽어 주세요.',
          '모든 내용은 각 레포의 README(설명서)를 근거로 썼어요. 가격·성능은 README에 적힌 것만 옮겼어요.'):
    c.setFillColor(R.INK); c.circle(M + 6, d.y - 7, 2.2, fill=1, stroke=0)
    d.para(M + 16, t, 9.5, W - 2 * M - 16, R.INK, 1.5); d.y -= 2

for name, col, _ in R.FOLDERS:
    group = sorted((i for i in items if i['folder'] == name), key=lambda i: i['rank'])
    d.heading(f'{name}  ({len(group)}개)', col)
    for i in group:
        lines = R.wrap(i['one'], 9, W - 2 * M - 200)
        h = max(28, 13 * len(lines) + 16)
        d.need(h); top = d.y
        c.setFillColor(HexColor(col)); c.roundRect(M, top - 20, 30, 16, 8, fill=1, stroke=0)
        c.setFillColor(white); c.setFont('Helvetica-Bold', 8.5); c.drawCentredString(M + 15, top - 15, f"{i['rank']}")
        d.text(M + 38, top - 15, i['name'][:26], 10, R.INK, bold=True)
        d.text(M + 38, top - 27, f"난이도 {i['diff']}/5" + ('  [주의]' if i['caution'] else ''), 7.5, R.AMBER if i['caution'] else R.SUB)
        yy = top - 15
        for ln in lines:
            d.text(M + 190, yy, ln, 9, R.INK); yy -= 13
        c.setStrokeColor(R.LINE); c.line(M, top - h + 3, W - M, top - h + 3)
        d.y = top - h
d.footer(); c.save()
print(os.path.getsize(out), out)
