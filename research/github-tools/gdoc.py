"""content/NNN.json -> compact Google-Docs-friendly HTML (imported via Drive text upload)."""
import json, os, sys, glob, html
from render import CAT2FOLDER, load_rows
E = lambda s: html.escape(str(s or ''), quote=False)
W = os.path.dirname(os.path.abspath(__file__)); rows = load_rows(W)
os.makedirs(os.path.join(W, 'gdoc'), exist_ok=True)
for fp in sys.argv[1:] or sorted(glob.glob(os.path.join(W, 'content', '*.json'))):
    j = json.load(open(fp, encoding='utf-8')); r = rows[int(j['rank'])]
    folder, col = CAT2FOLDER[r['category']]
    srcmap = {}
    key = r['repo'].replace('/', '_')
    try:
        srcmap = {d['file']: d['src'] for d in json.load(open(os.path.join(W, 'images', key + '.json')))}
    except Exception:
        pass
    imgs = [(srcmap.get(i['file']), i.get('caption')) for i in (j.get('images') or []) if srcmap.get(i['file'])]
    a = j.get('analogy', {}); p = j.get('principle') or {}; ar = j.get('architecture') or {}
    o = [f'<h1>{E(j["name"])}</h1>',
         f'<p><b>{E(folder[3:])} · {E(r["category"])}</b> | 순위 {r["rank"]}위 | GitHub 스타 {r["stars"]:,}개 | 난이도 {j["difficulty"]}/5'
         + (f' | 라이선스 {E(j.get("license"))}' if j.get('license') else '') + f'<br>https://github.com/{E(r["repo"])}</p>',
         f'<h3>“{E(j["one_liner"])}”</h3>',
         '<h2>한눈에 이해하기</h2>',
         f'<table border="1"><tr><th>이 도구가 없으면</th><th>이 도구를 쓰면</th></tr><tr><td>{E(a.get("before"))}</td><td>{E(a.get("after"))}</td></tr></table>',
         f'<p><i>{E(a.get("text"))}</i></p>',
         '<h2>이게 뭐예요?</h2><ul>' + ''.join(f'<li>{E(s)}</li>' for s in j.get('what', [])) + '</ul>']
    for u, cap in imgs[:1]:
        o.append(f'<p><img src="{E(u)}" width="560"><br><i>실제 화면: {E(cap)} (출처: README)</i></p>')
    if j.get('deep_dive'):
        o.append('<h2>조금 더 자세히</h2>' + ''.join(f'<p>{E(x)}</p>' for x in j['deep_dive']))
    if p:
        o.append('<h2>작동 원리</h2>')
        o.append(f'<p><b>핵심 원리 한 줄: {E(p.get("key_idea"))}</b></p><p><i>{E(p.get("analogy"))}</i></p>')
        if ar:
            o.append('<table border="1"><tr><th>입력</th><th>속에서 처리 (순서대로)</th><th>결과</th></tr><tr>'
                     f'<td>{"<br>".join(E(x) for x in ar.get("inputs", []))}</td>'
                     f'<td>{" → ".join(E(x) for x in ar.get("core", []))}</td>'
                     f'<td>{"<br>".join(E(x) for x in ar.get("outputs", []))}</td></tr></table>')
        o.append('<ol>' + ''.join(f'<li><b>{E(s.get("title"))}</b>: {E(s.get("text"))}</li>' for s in p.get('steps', [])) + '</ol>')
    if j.get('flow'):
        o.append('<h2>사용 흐름</h2><p>' + ' → '.join(f'<b>{E(s["label"])}</b>({E(s["desc"])})' for s in j['flow']) + '</p>')
    if j.get('features'):
        o.append('<h2>핵심 기능</h2><ul>' + ''.join(f'<li><b>{E(f["title"])}</b>: {E(f["desc"])}</li>' for f in j['features']) + '</ul>')
    for u, cap in imgs[1:2]:
        o.append(f'<p><img src="{E(u)}" width="560"><br><i>실제 화면: {E(cap)} (출처: README)</i></p>')
    if j.get('howto'):
        o.append('<h2>따라 해 보기</h2><ol>' + ''.join(
            f'<li><b>{E(h.get("step"))}</b>: {E(h.get("detail"))}' + (f'<br><code>{E(h["cmd"])}</code>' if h.get('cmd') else '') + '</li>' for h in j['howto']) + '</ol>')
    sc = j.get('scenario') or {}
    o.append('<h2>우리 채널에서는 이렇게 써요</h2>')
    if sc:
        o.append(f'<p><b>시나리오: {E(sc.get("title"))}</b></p><ol>' + ''.join(f'<li>{E(s)}</li>' for s in sc.get('steps', [])) + '</ol>')
    o.append('<ul>' + ''.join(f'<li>{E(u)}</li>' for u in j.get('channel_use', [])) + '</ul>')
    if j.get('compare'):
        o.append('<h2>비슷한 도구와 비교</h2><table border="1"><tr><th>도구</th><th>차이점</th></tr>' + ''.join(
            f'<tr><td>{E(x.get("name"))}' + (f' ({x["rank"]}위)' if x.get('rank') else '') + f'</td><td>{E(x.get("diff"))}</td></tr>' for x in j['compare']) + '</table>')
    o.append('<h2>좋은 점 vs 아쉬운 점</h2><table border="1"><tr><th>좋은 점</th><th>아쉬운 점</th></tr><tr>'
             f'<td>{"<br>".join("+ " + E(x) for x in j.get("pros", []))}</td><td>{"<br>".join("- " + E(x) for x in j.get("cons", []))}</td></tr></table>')
    o.append('<h2>시작하기 전에</h2><ul>'
             f'<li><b>난이도</b> {"■" * int(j["difficulty"])}{"□" * (5 - int(j["difficulty"]))} {j["difficulty"]}/5: {E(j.get("difficulty_note"))}</li>'
             f'<li><b>비용</b>: {E(j.get("cost"))}</li><li><b>준비물</b>: {E(", ".join(j.get("needs", [])))}</li></ul>')
    if j.get('faq'):
        o.append('<h2>자주 묻는 질문</h2>' + ''.join(f'<p><b>Q. {E(f.get("q"))}</b><br>{E(f.get("a"))}</p>' for f in j['faq']))
    if j.get('glossary'):
        o.append('<h2>어려운 말 풀이</h2><ul>' + ''.join(f'<li><b>{E(g["term"])}</b>: {E(g["meaning"])}</li>' for g in j['glossary']) + '</ul>')
    if (j.get('caution') or '').strip():
        o.append(f'<h2>꼭 주의하세요</h2><p><b>{E(j["caution"])}</b></p>')
    o.append('<p><small>근거(README에서 확인, "일반 원리"는 널리 알려진 기술 설명): ' + ' / '.join(E(s) for s in j.get('sources', [])) +
             '<br>GitHub 마케팅 AI 툴 쉽게 이해하기 · README 기준 정리 (2026-11)</small></p>')
    out = os.path.join(W, 'gdoc', f'{r["rank"]:03d}.html')
    open(out, 'w', encoding='utf-8').write('<html><head><meta charset="utf-8"></head><body>' + ''.join(o) + '</body></html>')
