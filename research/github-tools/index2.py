"""v2 index PDF: folder guide + every repo with one-liner and key principle."""
import json, os, glob, subprocess
from render import FOLDERS, CAT2FOLDER, load_rows
from render2 import CSS, E, tint, FONT, WORK, FOOT

rows = load_rows(WORK)
items = []
for fp in sorted(glob.glob(os.path.join(WORK, 'content', '*.json'))):
    j = json.load(open(fp, encoding='utf-8')); r = rows[int(j['rank'])]
    folder, col = CAT2FOLDER[r['category']]
    items.append(dict(rank=r['rank'], name=j['name'], repo=r['repo'], folder=folder, col=col, one=j['one_liner'],
                      key=(j.get('principle') or {}).get('key_idea', ''), d=int(j['difficulty']), warn=bool((j.get('caution') or '').strip())))

c = '#111827'
o = [f'<html><head><meta charset="utf-8"><style>{CSS % {"f": FONT}}'
     '.fg{display:grid;grid-template-columns:1fr 1fr;gap:9px}.fb{border-radius:12px;padding:10px 14px;border-left:6px solid}'
     '.row{display:grid;grid-template-columns:44px 1fr;gap:10px;padding:8px 0;border-bottom:1px solid #e5e7eb;break-inside:avoid}'
     '.rk{border-radius:999px;color:#fff;font-weight:800;text-align:center;height:22px;line-height:22px;font-size:9pt}'
     '.nm{font-weight:800;font-size:11pt}.nm small{font-weight:400;color:#6b7280;font-size:8.6pt;margin-left:6px}'
     '.k{color:#6b7280;font-size:9.2pt}.w{color:#b45309;font-weight:800;font-size:8.6pt;margin-left:6px}'
     f'</style></head><body style="--c:{c};--t1:#f3f4f6;--t2:#e5e7eb;--t3:#d1d5db">']
o.append(f'<div class="hero"><div class="deco"></div><div class="crumb">GitHub 마케팅 AI 툴</div><h1>{len(items)}개 레포, 쉽게 이해하기</h1>'
         '<div class="repo" style="font-size:10.5pt;opacity:.9">숏폼·릴스 기획, 벤치마킹, 제작, 배포에 쓰는 오픈소스를 용도별로 정리했어요.<br>'
         '레포마다 PDF 한 개(5~7쪽): 비유, 작동 원리와 구조도, 실제 화면, 따라 해 보기, 채널 활용 시나리오, 비교, FAQ</div></div>')
o.append('<h2>폴더 안내 <small>용도별 9개</small></h2><div class="fg">')
for name, col, cats in FOLDERS:
    n = sum(1 for i in items if i['folder'] == name)
    o.append(f'<div class="fb" style="background:{tint(col, .08)};border-color:{col}"><b>{E(name)}</b> <b style="color:{col}">{n}개</b>'
             f'<div class="k">{E(", ".join(cats))}</div></div>')
o.append('</div><h2>읽는 법</h2><ul class="dots">'
         '<li>난이도 1~5: 1은 앱처럼 바로 사용, 5는 개발 지식과 고성능 그래픽카드(GPU)가 필요해요.</li>'
         '<li><b style="color:#b45309">주의</b> 표시: 약관·저작권·라이선스(상업 이용 제한 등) 주의 사항이 있는 레포예요. 해당 PDF의 노란 상자를 꼭 읽어 주세요.</li>'
         '<li>모든 내용은 각 레포의 README(설명서)를 근거로 썼어요. README에 없는 기술 원리는 "일반 원리"로 표시했어요.</li></ul>')
for name, col, _ in FOLDERS:
    g = sorted((i for i in items if i['folder'] == name), key=lambda i: i['rank'])
    o.append(f'<h2 style="border-color:{col}">{E(name)} <small>{len(g)}개</small></h2>')
    for i in g:
        o.append(f'<div class="row"><div class="rk" style="background:{col}">{i["rank"]}</div><div>'
                 f'<div class="nm">{E(i["name"])}<small>{E(i["repo"])} · 난이도 {i["d"]}/5</small>' + ('<span class="w">주의</span>' if i['warn'] else '') +
                 f'</div><div>{E(i["one"])}</div>' + (f'<div class="k">원리: {E(i["key"])}</div>' if i['key'] else '') + '</div></div>')
o.append('</body></html>')
tmp = os.path.join(WORK, 'pdf2', '_html'); os.makedirs(tmp, exist_ok=True)
hp = os.path.join(tmp, 'index.html'); open(hp, 'w', encoding='utf-8').write(''.join(o))
jp = os.path.join(tmp, 'jobs_index.json')
json.dump([dict(html=hp, out=os.path.join(WORK, 'pdf2', '000_전체 목록과 폴더 안내.pdf'),
                foot=FOOT.replace('%s', 'GitHub AI tools explained  |  index'))], open(jp, 'w'))
subprocess.run(['node', os.path.join(WORK, 'pdf.js'), jp], check=True)
