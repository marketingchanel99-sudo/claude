"""v2 renderer: content/NNN.json -> detailed A4 PDF via HTML + headless Chromium.

Korean fonts (Nanum Gothic) are embedded (subset) so the PDF looks the same in every viewer.
Usage: python3 render2.py [content/NNN.json ...]   (no args = all)
"""
import json, os, sys, glob, html, math, asyncio
from render import FOLDERS, CAT2FOLDER, load_rows, safe

WORK = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(WORK, 'fonts')
E = lambda s: html.escape(str(s or ''))

ICONS = {
    'video': '<rect x="2" y="6" width="14" height="12" rx="2"/><polygon points="22 8 16 12 22 16 22 8"/>',
    'mic': '<path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/>',
    'text': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
    'search': '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    'download': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
    'upload': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
    'robot': '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>',
    'clock': '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    'chart': '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    'globe': '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    'image': '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
    'gear': '<circle cx="12" cy="12" r="3"/><path d="M12 1v3M12 20v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M1 12h3M20 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1"/>',
    'money': '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    'shield': '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    'bolt': '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    'link': '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    'code': '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
    'chat': '<path d="M21 11.5a8.4 8.4 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.4 8.4 0 0 1-3.8-.9L3 21l1.9-5.7a8.4 8.4 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.4 8.4 0 0 1 3.8-.9h.5a8.5 8.5 0 0 1 8 8v.5z"/>',
    'magic': '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    'eye': '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
}


def icon(name, size=22, color='currentColor'):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS.get(name, ICONS["magic"])}</svg>')


def face(happy, col):
    mouth = 'M14 31 Q22 38 30 31' if happy else 'M14 34 Q22 27 30 34'
    drop = '' if happy else '<path d="M39 9 q3 5 0 7 q-3 -2 0 -7z" fill="#60a5fa"/>'
    return (f'<svg width="52" height="52" viewBox="0 0 44 44"><circle cx="22" cy="22" r="19" fill="#fff" stroke="{col}" stroke-width="2.5"/>'
            f'<circle cx="15" cy="18" r="2.2" fill="{col}"/><circle cx="29" cy="18" r="2.2" fill="{col}"/>'
            f'<path d="{mouth}" fill="none" stroke="{col}" stroke-width="2.5" stroke-linecap="round"/>{drop}</svg>')


def wrap_svg_text(t, maxc):
    """Split label into <=2 lines of ~maxc chars for SVG boxes."""
    t = str(t); words = t.split(' '); lines = ['']
    for w in words:
        if len(lines[-1]) + len(w) + 1 <= maxc or not lines[-1]:
            lines[-1] = (lines[-1] + ' ' + w).strip()
        else:
            lines.append(w)
    out = []
    for l in lines:
        while len(l) > maxc:
            out.append(l[:maxc]); l = l[maxc:]
        out.append(l)
    return out[:3]


def architecture_svg(a, col, tint):
    ins, core, outs = a.get('inputs', [])[:3], a.get('core', [])[:4], a.get('outputs', [])[:2]
    if not core:
        return ''
    W, bw, bh, gap = 660, 150, 46, 14
    H = max(len(ins), len(core), len(outs)) * (bh + gap) + 50
    s = [f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" font-family="NG">',
         f'<defs><marker id="ah" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="{col}"/></marker></defs>']
    cols = [(20, ins, '입력', '#f3f4f6', '#374151'), (255, core, '속에서 처리', tint, '#111827'), (490, outs, '결과', col, '#ffffff')]
    centers = []
    for x, items, label, bg, fg in cols:
        s.append(f'<text x="{x + bw / 2 + (0 if x != 255 else 0)}" y="16" text-anchor="middle" font-size="12" fill="#6b7280" font-weight="700">{label}</text>')
        n = len(items); top = 28 + ((H - 40) - n * (bh + gap)) / 2
        cs = []
        for i, it in enumerate(items):
            y = top + i * (bh + gap)
            s.append(f'<rect x="{x}" y="{y}" width="{bw}" height="{bh}" rx="10" fill="{bg}" stroke="{col if x == 255 else "none"}" stroke-width="1.5"/>')
            ls = wrap_svg_text(it, 11)
            for k, l in enumerate(ls):
                yy = y + bh / 2 + 4.5 + (k - (len(ls) - 1) / 2) * 15
                s.append(f'<text x="{x + bw / 2}" y="{yy}" text-anchor="middle" font-size="12.5" font-weight="700" fill="{fg}">{E(l)}</text>')
            cs.append((x, y + bh / 2))
            if x == 255 and i < n - 1:
                s.append(f'<line x1="{x + bw / 2}" y1="{y + bh}" x2="{x + bw / 2}" y2="{y + bh + gap - 1}" stroke="{col}" stroke-width="2" marker-end="url(#ah)"/>')
        centers.append(cs)
    if centers[0]:
        for (x, y) in centers[0]:
            s.append(f'<path d="M{x + bw} {y} C {x + bw + 40} {y}, {255 - 40} {centers[1][0][1]}, {255 - 3} {centers[1][0][1]}" fill="none" stroke="{col}" stroke-width="2" marker-end="url(#ah)"/>')
    for (x, y) in centers[2]:
        cy = centers[1][-1][1]
        s.append(f'<path d="M{255 + bw} {cy} C {255 + bw + 40} {cy}, {490 - 40} {y}, {490 - 3} {y}" fill="none" stroke="{col}" stroke-width="2" marker-end="url(#ah)"/>')
    s.append('</svg>')
    return ''.join(s)


def tint(hexcol, a):
    h = hexcol.lstrip('#'); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return '#%02x%02x%02x' % tuple(int(255 - (255 - v) * a) for v in (r, g, b))


CSS = """
@font-face{font-family:NG;src:url('file://%(f)s/NanumGothic-Regular.ttf');font-weight:400}
@font-face{font-family:NG;src:url('file://%(f)s/NanumGothic-Bold.ttf');font-weight:700}
@font-face{font-family:NG;src:url('file://%(f)s/NanumGothic-ExtraBold.ttf');font-weight:800}
@font-face{font-family:NGC;src:url('file://%(f)s/NanumGothicCoding-Regular.ttf')}
@page{size:A4}
*{box-sizing:border-box}
body{font-family:NG;color:#1f2937;font-size:10.6pt;line-height:1.68;margin:0;word-break:keep-all;overflow-wrap:anywhere}
.hero{background:var(--c);color:#fff;border-radius:18px;padding:22px 26px 20px;position:relative;overflow:hidden}
.hero .deco{position:absolute;right:-30px;top:-40px;width:190px;height:190px;border-radius:50%%;background:rgba(255,255,255,.14)}
.hero .ic{position:absolute;right:30px;top:30px;opacity:.9}
.hero .crumb{font-size:9.5pt;opacity:.85}
.hero h1{font-size:27pt;font-weight:800;margin:6px 0 2px;line-height:1.2;letter-spacing:-.5px;max-width:78%%}
.hero .repo{font-size:10pt;opacity:.8}
.badges{margin-top:12px;display:flex;gap:7px;flex-wrap:wrap}
.badge{background:#fff;color:#111827;border-radius:999px;padding:3px 12px;font-size:9.2pt;font-weight:700}
.quote{margin:16px 0 4px;background:var(--t1);border:1.5px solid var(--t3);border-radius:14px;padding:14px 18px 14px 50px;font-size:14pt;font-weight:800;position:relative;line-height:1.45}
.quote:before{content:'\\201C';position:absolute;left:14px;top:-2px;font-size:40pt;color:var(--c);font-family:Georgia,serif}
h2{font-size:14.5pt;font-weight:800;margin:22px 0 10px;padding-left:12px;border-left:6px solid var(--c);line-height:1.3;break-after:avoid}
h2 small{font-size:9.5pt;color:#6b7280;font-weight:400;margin-left:6px}
h3{font-size:11.5pt;font-weight:800;margin:0 0 4px}
p{margin:0 0 8px}
.card{border-radius:12px;padding:12px 16px;break-inside:avoid}
.ba{display:grid;grid-template-columns:1fr 40px 1fr;align-items:stretch;gap:0;break-inside:avoid}
.ba .card{display:flex;gap:12px;align-items:center}
.ba .arrow{display:flex;align-items:center;justify-content:center;color:var(--c);font-size:22pt;font-weight:800}
.bad{background:#fef2f2}.good{background:#f0fdf4}
.bad h3{color:#dc2626}.good h3{color:#16a34a}
.analogy{color:#4b5563;margin-top:8px;font-size:10.2pt;padding-left:4px}
ul.dots{padding-left:18px;margin:0}
ul.dots li{margin:3px 0}
ul.dots li::marker{color:var(--c)}
.deep p{text-indent:0;background:#f9fafb;border-radius:10px;padding:10px 14px}
.key{background:var(--c);color:#fff;border-radius:12px;padding:12px 16px;font-weight:800;font-size:12pt;break-inside:avoid}
.key span{display:block;font-size:9pt;font-weight:400;opacity:.85;margin-bottom:2px}
.pan{margin:8px 0 10px;color:#374151;background:var(--t1);border-radius:10px;padding:9px 14px;break-inside:avoid}
.tl{position:relative;margin-left:6px}
.tl .st{display:grid;grid-template-columns:36px 1fr;gap:10px;margin-bottom:10px;break-inside:avoid}
.tl .n{width:30px;height:30px;border-radius:50%%;background:var(--c);color:#fff;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:11pt}
.arch{border:1.5px dashed var(--t3);border-radius:14px;padding:10px 12px 4px;margin:6px 0 4px;break-inside:avoid}
.flow{display:flex;gap:0;align-items:stretch;break-inside:avoid}
.flow .b{flex:1;background:var(--t1);border:1.5px solid var(--t3);border-radius:12px;padding:20px 8px 10px;text-align:center;position:relative}
.flow .b .num{position:absolute;top:-12px;left:50%%;transform:translateX(-50%%);width:24px;height:24px;border-radius:50%%;background:var(--c);color:#fff;font-weight:800;font-size:10pt;line-height:24px}
.flow .b b{display:block;font-size:10.5pt;margin-bottom:3px}
.flow .b span{font-size:9pt;color:#6b7280;line-height:1.45;display:block}
.flow .ar{width:22px;display:flex;align-items:center;justify-content:center;color:var(--c);font-weight:800}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.feat{background:#f9fafb;border:1px solid #e5e7eb;display:flex;gap:12px;align-items:flex-start}
.feat .i{flex:none;width:40px;height:40px;border-radius:50%%;background:var(--c);display:flex;align-items:center;justify-content:center}
.feat p{font-size:9.6pt;color:#4b5563;margin:0;line-height:1.5}
figure{margin:8px 0 12px;break-inside:avoid;text-align:center}
figure img{max-width:100%%;max-height:88mm;border-radius:10px;border:1px solid #e5e7eb}
figcaption{font-size:9pt;color:#6b7280;margin-top:4px}
.how{display:grid;grid-template-columns:30px 1fr;gap:10px;margin-bottom:10px;break-inside:avoid}
.how .n{width:26px;height:26px;border-radius:8px;background:var(--t2);color:var(--c);font-weight:800;display:flex;align-items:center;justify-content:center}
pre{font-family:NGC;background:#111827;color:#e5e7eb;border-radius:8px;padding:8px 12px;font-size:8.6pt;line-height:1.5;white-space:pre-wrap;word-break:break-all;margin:5px 0 0}
.scn{background:var(--t1);border-radius:14px;padding:14px 16px;break-inside:avoid}
.scn ol{margin:6px 0 0;padding-left:20px}
.scn li{margin:4px 0}
.uses{display:flex;flex-direction:column;gap:8px;margin-top:10px}
.use{display:flex;gap:12px;align-items:center;background:#f9fafb;border-radius:10px;padding:9px 14px;break-inside:avoid}
.phone{flex:none;width:22px;height:34px;border-radius:5px;background:var(--c);position:relative}
.phone:after{content:'';position:absolute;left:3px;top:4px;width:16px;height:24px;background:#fff;border-radius:2px}
table{border-collapse:collapse;width:100%%;font-size:9.8pt;break-inside:avoid}
th,td{border-bottom:1px solid #e5e7eb;padding:7px 8px;text-align:left;vertical-align:top}
th{background:var(--t1);font-weight:800}
.pc{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.pc ul{list-style:none;padding:0;margin:6px 0 0}
.pc li{padding-left:24px;position:relative;margin:5px 0}
.pc li:before{position:absolute;left:0;top:1px;width:17px;height:17px;border-radius:50%%;color:#fff;font-weight:800;font-size:10pt;line-height:17px;text-align:center}
.good li:before{content:'+';background:#16a34a}.bad li:before{content:'-';background:#dc2626}
.meta{display:grid;grid-template-columns:70px 1fr;gap:8px 12px;align-items:center;break-inside:avoid}
.meta .k{color:#6b7280;font-weight:800}
.gauge{display:flex;gap:4px;align-items:center}
.gauge i{width:34px;height:11px;border-radius:4px;background:#e5e7eb;display:inline-block}
.gauge i.on{background:var(--c)}
.chip{display:inline-block;background:var(--t2);border-radius:999px;padding:2px 11px;margin:2px 4px 2px 0;font-size:9.4pt}
.faq{break-inside:avoid;margin-bottom:9px}
.faq .q{font-weight:800}
.faq .q:before{content:'Q. ';color:var(--c)}
.faq .a{color:#374151;padding-left:22px}
.gl{display:grid;grid-template-columns:120px 1fr;gap:6px 12px;break-inside:avoid}
.gl .t{background:var(--t2);border-radius:8px;padding:3px 8px;font-weight:800;text-align:center;font-size:9.6pt}
.warn{background:#fffbeb;border:1.5px solid #fcd34d;border-radius:12px;padding:12px 16px 12px 54px;position:relative;margin-top:16px;break-inside:avoid}
.warn:before{content:'!';position:absolute;left:16px;top:13px;width:26px;height:26px;border-radius:50%%;background:#d97706;color:#fff;font-weight:800;text-align:center;line-height:26px}
.warn b{color:#b45309}
.src{margin-top:18px;border-top:1px solid #e5e7eb;padding-top:8px;font-size:8.4pt;color:#6b7280;line-height:1.55}
"""


def card_html(j, folder, col):
    c = col; t1, t2, t3 = tint(col, .08), tint(col, .16), tint(col, .35)
    a = j.get('analogy', {}); pr = j.get('principle') or {}
    o = [f'<html><head><meta charset="utf-8"><style>{CSS % {"f": FONT}}</style></head>'
         f'<body style="--c:{c};--t1:{t1};--t2:{t2};--t3:{t3}">']
    lic = j.get('license') or ''
    feats = j.get('features') or []
    o.append(f'<div class="hero"><div class="deco"></div><div class="ic">{icon(feats[0]["icon"] if feats else "magic", 64, "rgba(255,255,255,.85)")}</div>'
             f'<div class="crumb">{E(folder[3:])} &nbsp;·&nbsp; {E(j["category"])}</div><h1>{E(j["name"])}</h1>'
             f'<div class="repo">github.com/{E(j["repo"])}</div><div class="badges">'
             f'<span class="badge">인기 순위 {j["rank"]}위</span><span class="badge">GitHub 스타 {int(j["stars"]):,}개</span>'
             f'<span class="badge">난이도 {j["difficulty"]}/5</span>' + (f'<span class="badge">라이선스 {E(lic[:28])}</span>' if lic else '') + '</div></div>')
    o.append(f'<div class="quote">{E(j["one_liner"])}</div>')

    imgs = [im for im in (j.get('images') or []) if os.path.exists(os.path.join(WORK, im.get('file', '')))]
    # 1. analogy
    o.append('<h2>한눈에 이해하기 <small>비유로 보는 전과 후</small></h2>')
    o.append(f'<div class="ba"><div class="card bad">{face(False, "#dc2626")}<div><h3>이 도구가 없으면</h3>{E(a.get("before"))}</div></div>'
             f'<div class="arrow">&rarr;</div><div class="card good">{face(True, "#16a34a")}<div><h3>이 도구를 쓰면</h3>{E(a.get("after"))}</div></div></div>'
             f'<div class="analogy">{E(a.get("text"))}</div>')
    # 2. what + deep dive
    o.append('<h2>이게 뭐예요?</h2><ul class="dots">' + ''.join(f'<li>{E(s)}</li>' for s in j.get('what', [])) + '</ul>')
    if imgs:
        im = imgs[0]
        o.append(f'<figure><img src="file://{os.path.join(WORK, im["file"])}"><figcaption>실제 화면: {E(im.get("caption"))} (출처: 레포 README)</figcaption></figure>')
    if j.get('deep_dive'):
        o.append('<h2>조금 더 자세히</h2><div class="deep">' + ''.join(f'<p>{E(p)}</p>' for p in j['deep_dive']) + '</div>')
    # 3. principle
    if pr:
        o.append('<h2>작동 원리 <small>속을 들여다보면</small></h2>')
        if pr.get('key_idea'):
            o.append(f'<div class="key"><span>핵심 원리 한 줄</span>{E(pr["key_idea"])}</div>')
        if pr.get('analogy'):
            o.append(f'<div class="pan">{E(pr["analogy"])}</div>')
        if j.get('architecture'):
            o.append('<div class="arch">' + architecture_svg(j['architecture'], c, t2) + '</div>')
        o.append('<div class="tl">' + ''.join(
            f'<div class="st"><div class="n">{i + 1}</div><div><h3>{E(s.get("title"))}</h3>{E(s.get("text"))}</div></div>'
            for i, s in enumerate(pr.get('steps', []))) + '</div>')
    # 4. usage flow
    fl = j.get('flow', [])[:5]
    if fl:
        o.append('<h2>사용 흐름 <small>사용자 입장에서 보면</small></h2><div class="flow">')
        for i, s in enumerate(fl):
            if i:
                o.append('<div class="ar">&rarr;</div>')
            o.append(f'<div class="b"><div class="num">{i + 1}</div><b>{E(s["label"])}</b><span>{E(s["desc"])}</span></div>')
        o.append('</div>')
    # 5. features
    if feats:
        o.append('<h2>핵심 기능</h2><div class="grid2">' + ''.join(
            f'<div class="card feat"><div class="i">{icon(f.get("icon"), 22, "#fff")}</div><div><h3>{E(f["title"])}</h3><p>{E(f["desc"])}</p></div></div>'
            for f in feats[:4]) + '</div>')
    for im in imgs[1:2]:
        o.append(f'<figure><img src="file://{os.path.join(WORK, im["file"])}"><figcaption>실제 화면: {E(im.get("caption"))} (출처: 레포 README)</figcaption></figure>')
    # 6. howto
    if j.get('howto'):
        o.append('<h2>따라 해 보기 <small>설치부터 첫 결과까지</small></h2>')
        for i, h in enumerate(j['howto']):
            cmd = (h.get('cmd') or '').strip()
            o.append(f'<div class="how"><div class="n">{i + 1}</div><div><h3>{E(h.get("step"))}</h3>{E(h.get("detail"))}'
                     + (f'<pre>{E(cmd)}</pre>' if cmd else '') + '</div></div>')
    # 7. channel
    sc = j.get('scenario') or {}
    o.append('<h2>우리 채널에서는 이렇게 써요</h2>')
    if sc:
        o.append(f'<div class="scn"><h3>시나리오: {E(sc.get("title"))}</h3><ol>' + ''.join(f'<li>{E(s)}</li>' for s in sc.get('steps', [])) + '</ol></div>')
    o.append('<div class="uses">' + ''.join(f'<div class="use"><div class="phone"></div><div>{E(u)}</div></div>' for u in j.get('channel_use', [])) + '</div>')
    # 8. compare
    if j.get('compare'):
        o.append('<h2>비슷한 도구와 비교</h2><table><tr><th style="width:30%">도구</th><th>차이점</th></tr>' + ''.join(
            f'<tr><td><b>{E(x.get("name"))}</b>' + (f' <span style="color:#6b7280">({x["rank"]}위)</span>' if x.get('rank') else '') + f'</td><td>{E(x.get("diff"))}</td></tr>'
            for x in j['compare']) + '</table>')
    # 9. pros/cons
    o.append('<h2>좋은 점 vs 아쉬운 점</h2><div class="pc">'
             f'<div class="card good"><h3>좋은 점</h3><ul>' + ''.join(f'<li>{E(x)}</li>' for x in j.get('pros', [])) + '</ul></div>'
             f'<div class="card bad"><h3>아쉬운 점</h3><ul>' + ''.join(f'<li>{E(x)}</li>' for x in j.get('cons', [])) + '</ul></div></div>')
    # 10. meta
    d = int(j.get('difficulty', 3))
    o.append('<h2>시작하기 전에</h2><div class="meta">'
             f'<div class="k">난이도</div><div><span class="gauge">' + ''.join(f'<i class="{"on" if k < d else ""}"></i>' for k in range(5)) +
             f'</span> <b style="margin-left:6px">{["", "쉬움", "할 만함", "보통", "어려움", "전문가용"][d]}</b><div style="color:#6b7280;font-size:9.6pt">{E(j.get("difficulty_note"))}</div></div>'
             f'<div class="k">비용</div><div>{E(j.get("cost"))}</div>'
             f'<div class="k">준비물</div><div>' + ''.join(f'<span class="chip">{E(n)}</span>' for n in j.get('needs', [])) + '</div></div>')
    # 11. faq
    if j.get('faq'):
        o.append('<h2>자주 묻는 질문</h2>' + ''.join(f'<div class="faq"><div class="q">{E(f.get("q"))}</div><div class="a">{E(f.get("a"))}</div></div>' for f in j['faq']))
    # 12. glossary
    if j.get('glossary'):
        o.append('<h2>어려운 말 풀이</h2><div class="gl">' + ''.join(f'<div class="t">{E(g["term"])}</div><div>{E(g["meaning"])}</div>' for g in j['glossary']) + '</div>')
    if (j.get('caution') or '').strip():
        o.append(f'<div class="warn"><b>꼭 주의하세요</b><br>{E(j["caution"])}</div>')
    o.append(f'<div class="src">링크: https://github.com/{E(j["repo"])}' + (f' &nbsp;·&nbsp; 라이선스: {E(lic)}' if lic else '') +
             '<br>근거(README에서 확인, "일반 원리"는 널리 알려진 기술 설명): ' + ' / '.join(E(s) for s in j.get('sources', [])) +
             '<br>GitHub 마케팅 AI 툴 쉽게 이해하기 · README 기준 정리 (2026-11)</div>')
    o.append('</body></html>')
    return ''.join(o)


FOOT = ('<div style="font-size:7.5px;color:#9ca3af;width:100%;padding:0 15mm;display:flex;justify-content:space-between;font-family:Helvetica">'
        '<span>%s</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')


def main(files):
    """Write HTML pages + jobs.json, then print them to PDF with Node Playwright (pdf.js)."""
    import subprocess
    rows = load_rows(WORK)
    jobs = []
    tmp = os.path.join(WORK, 'pdf2', '_html'); os.makedirs(tmp, exist_ok=True)
    for fp in files:
        j = json.load(open(fp, encoding='utf-8'))
        r = rows[int(j['rank'])]
        j.update(category=r['category'], repo=r['repo'], stars=r['stars'], rank=r['rank'])
        folder, col = CAT2FOLDER[j['category']]
        od = os.path.join(WORK, 'pdf2', folder); os.makedirs(od, exist_ok=True)
        hp = os.path.join(tmp, f'{j["rank"]:03d}.html')
        open(hp, 'w', encoding='utf-8').write(card_html(j, folder, col))
        jobs.append(dict(html=hp, out=os.path.join(od, f'{j["rank"]:03d}_{safe(j["name"])}.pdf'),
                         foot=FOOT.replace('%s', html.escape(f'{j["repo"]}  |  GitHub AI tools explained'))))
    jp = os.path.join(tmp, 'jobs.json'); json.dump(jobs, open(jp, 'w'))
    subprocess.run(['node', os.path.join(WORK, 'pdf.js'), jp], check=True)


if __name__ == '__main__':
    main(sys.argv[1:] or sorted(glob.glob(os.path.join(WORK, 'content', '*.json'))))
