"""Render repo explainer cards (content/NNN.json) into compact 2-page PDFs.

Uses the standard Adobe-Korea1 CID font (not embedded) so each PDF stays ~10KB.
"""
import json, math, os, sys, glob
import reportlab.rl_config as _rc
_rc.useA85 = 0
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.colors import HexColor, white

pdfmetrics.registerFont(UnicodeCIDFont('HYGothic-Medium'))
F = 'HYGothic-Medium'
W, H = 595.0, 842.0
M = 40.0

FOLDERS = [
    ("01_트렌드·레퍼런스 서칭", "#2563eb", ["콘텐츠 서칭", "트렌드 리서치", "트렌드 모니터링", "트렌드/여론 분석", "콘텐츠 서칭/대본", "트렌드/브랜드 모니터링", "벤치마킹/리서치"]),
    ("02_벤치마킹 자료 수집(다운로드·크롤링)", "#0891b2", ["콘텐츠 수집/다운로드", "콘텐츠 수집/크롤링", "콘텐츠 수집/분석", "콘텐츠 수집/API"]),
    ("03_기획·카피·마케팅 스킬", "#7c3aed", ["AI 스킬 모음", "기획/카피 스킬", "마케팅 지식"]),
    ("04_숏폼 제작·편집 자동화", "#db2777", ["숏폼 자동생성", "영상 제작 에이전트", "영상편집/모션그래픽", "영상편집", "영상편집 에이전트", "영상편집 스킬", "롱폼→숏폼/해설", "롱폼→숏폼 클립"]),
    ("05_AI 이미지·영상 생성·디자인", "#ea580c", ["영상 생성 모델", "이미지/영상 생성", "이미지 생성 모델", "프롬프트 라이브러리", "아바타/디지털휴먼", "아바타/립싱크", "디자인/콘텐츠", "디자인/카드뉴스"]),
    ("06_음성·내레이션(TTS·보이스클론)", "#16a34a", ["음성/TTS", "음성/보이스클론"]),
    ("07_자막·받아쓰기·번역더빙", "#0d9488", ["자막/STT", "자막/번역/더빙"]),
    ("08_업로드·자동화·운영", "#4f46e5", ["자동화 워크플로우", "자동화/브라우저 에이전트", "자동화/모니터링", "AI 인프라", "업로드/스케줄링", "마케팅 자동화", "SNS 에이전트", "참고(주의)"]),
    ("09_광고·SEO·블로그", "#ca8a04", ["광고/퍼포먼스", "광고/UGC", "벤치마킹/광고", "SEO/GEO", "롱폼/블로그"]),
]
CAT2FOLDER = {c: (name, col) for name, col, cats in FOLDERS for c in cats}

INK = HexColor('#1f2937'); SUB = HexColor('#6b7280'); LINE = HexColor('#e5e7eb'); SOFT = HexColor('#f9fafb')
GREEN = HexColor('#16a34a'); RED = HexColor('#dc2626'); AMBER = HexColor('#d97706')


def tint(hexcol, a):
    c = HexColor(hexcol)
    return HexColor('#%02x%02x%02x' % tuple(int(255 - (255 - v * 255) * a) for v in (c.red, c.green, c.blue)))


def sw(t, size):
    return pdfmetrics.stringWidth(t, F, size)


def wrap(text, size, width):
    """Greedy wrap: break at spaces when possible, otherwise at any char (CJK)."""
    out = []
    for para in str(text).split('\n'):
        line = ''
        for word in para.split(' '):
            cand = (line + ' ' + word) if line else word
            if sw(cand, size) <= width:
                line = cand
                continue
            if line:
                out.append(line); line = ''
            while sw(word, size) > width:  # hard-break long token
                i = 1
                while i < len(word) and sw(word[:i + 1], size) <= width:
                    i += 1
                out.append(word[:i]); word = word[i:]
            line = word
        out.append(line)
    return out


class Doc:
    def __init__(self, path, title):
        self.c = canvas.Canvas(path, pagesize=(W, H), pageCompression=1)
        self.c.setTitle(title); self.c.setAuthor('채널 운영 리서치'); self.c.setCreator('render.py')
        self.y = H - M; self.page = 1

    def text(self, x, y, t, size=10, color=INK, bold=False):
        c = self.c
        c.setFillColor(color)
        to = c.beginText(x, y); to.setFont(F, size)
        if bold:
            c.setStrokeColor(color); c.setLineWidth(size * 0.035); to.setTextRenderMode(2)
        else:
            to._code.append('0 Tr')  # Tr persists across BT/ET; reset explicitly
        to.textOut(t); c.drawText(to)
        if bold:
            c._code.append('0 Tr')

    def para(self, x, t, size, width, color=INK, lead=1.5, bold=False):
        for ln in wrap(t, size, width):
            self.need(size * lead)
            self.text(x, self.y - size, ln, size, color, bold)
            self.y -= size * lead

    def need(self, h):
        if self.y - h < M + 20:
            self.newpage()

    def newpage(self):
        self.footer(); self.c.showPage(); self.page += 1; self.y = H - M

    def footer(self):
        self.text(M, 22, getattr(self, 'foot', ''), 7, SUB)
        self.text(W - M - 20, 22, str(self.page), 8, SUB)

    def heading(self, t, col, icon=None):
        self.need(40)
        self.y -= 8
        c = self.c
        c.setFillColor(HexColor(col)); c.roundRect(M, self.y - 20, 5, 20, 2, fill=1, stroke=0)
        self.text(M + 13, self.y - 15, t, 13.5, INK, bold=True)
        self.y -= 30


# ---------------------------------------------------------------- icons
def icon(c, kind, x, y, s, col):
    """Draw icon centered at (x,y) with size s in colour col (white on col circle)."""
    c.saveState()
    c.setFillColor(col); c.circle(x, y, s / 2, fill=1, stroke=0)
    c.setStrokeColor(white); c.setFillColor(white); c.setLineWidth(s * 0.06); c.setLineCap(1); c.setLineJoin(1)
    u = s * 0.2
    p = c.beginPath
    if kind == 'video':
        c.roundRect(x - 1.5 * u, y - u, 3 * u, 2 * u, u * 0.3, fill=0, stroke=1)
        pa = p(); pa.moveTo(x - 0.4 * u, y - 0.55 * u); pa.lineTo(x - 0.4 * u, y + 0.55 * u); pa.lineTo(x + 0.6 * u, y); pa.close(); c.drawPath(pa, fill=1, stroke=0)
    elif kind == 'mic':
        c.roundRect(x - 0.55 * u, y - 0.3 * u, 1.1 * u, 1.8 * u, 0.55 * u, fill=1, stroke=0)
        c.arc(x - u, y - 1.1 * u, x + u, y + 0.9 * u, 200, 140); c.line(x, y - 1.1 * u, x, y - 1.6 * u)
    elif kind == 'text':
        for i, l in enumerate([1.4, 1.4, 0.9]):
            c.line(x - 1.2 * u, y + 0.8 * u - i * 0.8 * u, x - 1.2 * u + 2 * l * u * 0.85, y + 0.8 * u - i * 0.8 * u)
    elif kind == 'search':
        c.circle(x - 0.3 * u, y + 0.3 * u, 0.9 * u, fill=0, stroke=1); c.line(x + 0.35 * u, y - 0.35 * u, x + 1.2 * u, y - 1.2 * u)
    elif kind in ('download', 'upload'):
        a, b = (y + 1.2 * u, y - 0.4 * u) if kind == 'download' else (y - 0.4 * u, y + 1.2 * u)
        c.line(x, a, x, b); d = -1 if kind == 'download' else 1
        c.line(x - 0.6 * u, b - d * 0.6 * u, x, b); c.line(x + 0.6 * u, b - d * 0.6 * u, x, b)
        c.line(x - 1.2 * u, y - 0.6 * u, x - 1.2 * u, y - 1.2 * u); c.line(x - 1.2 * u, y - 1.2 * u, x + 1.2 * u, y - 1.2 * u); c.line(x + 1.2 * u, y - 1.2 * u, x + 1.2 * u, y - 0.6 * u)
    elif kind == 'robot':
        c.roundRect(x - 1.2 * u, y - u, 2.4 * u, 1.8 * u, 0.4 * u, fill=0, stroke=1)
        c.setFillColor(white); c.circle(x - 0.5 * u, y - 0.1 * u, 0.22 * u, fill=1, stroke=0); c.circle(x + 0.5 * u, y - 0.1 * u, 0.22 * u, fill=1, stroke=0)
        c.line(x, y + 0.8 * u, x, y + 1.4 * u); c.circle(x, y + 1.5 * u, 0.15 * u, fill=1, stroke=0)
    elif kind == 'clock':
        c.circle(x, y, 1.3 * u, fill=0, stroke=1); c.line(x, y, x, y + 0.9 * u); c.line(x, y, x + 0.7 * u, y - 0.3 * u)
    elif kind == 'chart':
        for i, h in enumerate([0.9, 1.6, 2.3]):
            c.rect(x - 1.25 * u + i * 0.95 * u, y - 1.1 * u, 0.6 * u, h * u, fill=1, stroke=0)
    elif kind == 'globe':
        c.circle(x, y, 1.3 * u, fill=0, stroke=1); c.ellipse(x - 0.55 * u, y - 1.3 * u, x + 0.55 * u, y + 1.3 * u, fill=0, stroke=1); c.line(x - 1.3 * u, y, x + 1.3 * u, y)
    elif kind == 'image':
        c.roundRect(x - 1.4 * u, y - 1.1 * u, 2.8 * u, 2.2 * u, 0.25 * u, fill=0, stroke=1)
        pa = p(); pa.moveTo(x - 1.1 * u, y - 0.8 * u); pa.lineTo(x - 0.3 * u, y + 0.2 * u); pa.lineTo(x + 0.3 * u, y - 0.4 * u); pa.lineTo(x + 0.6 * u, y - 0.1 * u); pa.lineTo(x + 1.1 * u, y - 0.8 * u); pa.close(); c.drawPath(pa, fill=1, stroke=0)
        c.circle(x + 0.6 * u, y + 0.5 * u, 0.25 * u, fill=1, stroke=0)
    elif kind == 'gear':
        for k in range(8):
            a = k * math.pi / 4
            c.line(x + math.cos(a) * 0.9 * u, y + math.sin(a) * 0.9 * u, x + math.cos(a) * 1.4 * u, y + math.sin(a) * 1.4 * u)
        c.circle(x, y, 0.95 * u, fill=0, stroke=1); c.circle(x, y, 0.35 * u, fill=1, stroke=0)
    elif kind == 'money':
        c.circle(x, y, 1.3 * u, fill=0, stroke=1); c.setFont('Helvetica-Bold', 1.8 * u); c.drawCentredString(x, y - 0.62 * u, '$')
    elif kind == 'shield':
        pa = p(); pa.moveTo(x, y + 1.4 * u); pa.lineTo(x + 1.2 * u, y + 0.9 * u); pa.lineTo(x + 1.0 * u, y - 0.5 * u); pa.lineTo(x, y - 1.4 * u); pa.lineTo(x - 1.0 * u, y - 0.5 * u); pa.lineTo(x - 1.2 * u, y + 0.9 * u); pa.close(); c.drawPath(pa, fill=0, stroke=1)
        c.line(x - 0.5 * u, y, x - 0.1 * u, y - 0.4 * u); c.line(x - 0.1 * u, y - 0.4 * u, x + 0.55 * u, y + 0.4 * u)
    elif kind == 'bolt':
        pa = p(); pa.moveTo(x + 0.3 * u, y + 1.5 * u); pa.lineTo(x - 0.9 * u, y - 0.1 * u); pa.lineTo(x - 0.05 * u, y - 0.1 * u); pa.lineTo(x - 0.3 * u, y - 1.5 * u); pa.lineTo(x + 0.9 * u, y + 0.2 * u); pa.lineTo(x + 0.05 * u, y + 0.2 * u); pa.close(); c.drawPath(pa, fill=1, stroke=0)
    elif kind == 'link':
        c.saveState(); c.translate(x, y); c.rotate(45)
        c.roundRect(-1.5 * u, -0.45 * u, 1.8 * u, 0.9 * u, 0.45 * u, fill=0, stroke=1); c.roundRect(-0.3 * u, -0.45 * u, 1.8 * u, 0.9 * u, 0.45 * u, fill=0, stroke=1)
        c.restoreState()
    elif kind == 'code':
        c.line(x - 0.6 * u, y + 0.8 * u, x - 1.3 * u, y); c.line(x - 1.3 * u, y, x - 0.6 * u, y - 0.8 * u)
        c.line(x + 0.6 * u, y + 0.8 * u, x + 1.3 * u, y); c.line(x + 1.3 * u, y, x + 0.6 * u, y - 0.8 * u); c.line(x + 0.25 * u, y + 1.0 * u, x - 0.25 * u, y - 1.0 * u)
    elif kind == 'chat':
        c.roundRect(x - 1.4 * u, y - 0.6 * u, 2.8 * u, 1.8 * u, 0.5 * u, fill=1, stroke=0)
        pa = p(); pa.moveTo(x - 0.8 * u, y - 0.5 * u); pa.lineTo(x - 1.0 * u, y - 1.3 * u); pa.lineTo(x - 0.1 * u, y - 0.5 * u); pa.close(); c.drawPath(pa, fill=1, stroke=0)
        c.setFillColor(col)
        for k in (-0.7, 0, 0.7):
            c.circle(x + k * u, y + 0.3 * u, 0.18 * u, fill=1, stroke=0)
    elif kind == 'magic':
        star(c, x, y, 1.4 * u, 0.6 * u, white)
    elif kind == 'eye':
        pa = p(); pa.moveTo(x - 1.5 * u, y); pa.curveTo(x - 0.6 * u, y + 1.2 * u, x + 0.6 * u, y + 1.2 * u, x + 1.5 * u, y); pa.curveTo(x + 0.6 * u, y - 1.2 * u, x - 0.6 * u, y - 1.2 * u, x - 1.5 * u, y); c.drawPath(pa, fill=0, stroke=1)
        c.circle(x, y, 0.45 * u, fill=1, stroke=0)
    else:
        c.circle(x, y, 0.4 * u, fill=1, stroke=0)
    c.restoreState()


def star(c, x, y, r1, r2, col):
    pa = c.beginPath()
    for k in range(10):
        r = r1 if k % 2 == 0 else r2
        a = math.pi / 2 + k * math.pi / 5
        (pa.moveTo if k == 0 else pa.lineTo)(x + r * math.cos(a), y + r * math.sin(a))
    pa.close(); c.setFillColor(col); c.drawPath(pa, fill=1, stroke=0)


def face(c, x, y, r, happy, col):
    c.saveState()
    c.setFillColor(white); c.setStrokeColor(col); c.setLineWidth(2)
    c.circle(x, y, r, fill=1, stroke=1)
    c.setFillColor(col)
    c.circle(x - r * 0.35, y + r * 0.2, r * 0.1, fill=1, stroke=0); c.circle(x + r * 0.35, y + r * 0.2, r * 0.1, fill=1, stroke=0)
    if happy:
        c.arc(x - r * 0.45, y - r * 0.6, x + r * 0.45, y + r * 0.1, 200, 140)
    else:
        c.arc(x - r * 0.4, y - r * 0.65, x + r * 0.4, y - r * 0.05, 20, 140)
        c.setFillColor(HexColor('#60a5fa'))  # sweat drop
        pa = c.beginPath(); dx, dy = x + r * 0.95, y + r * 0.55
        pa.moveTo(dx, dy + r * 0.3); pa.curveTo(dx + r * 0.2, dy, dx + r * 0.15, dy - r * 0.15, dx, dy - r * 0.15); pa.curveTo(dx - r * 0.15, dy - r * 0.15, dx - r * 0.2, dy, dx, dy + r * 0.3); c.drawPath(pa, fill=1, stroke=0)
    c.restoreState()


def arrow(c, x1, y1, x2, y2, col, w=2.2):
    c.saveState(); c.setStrokeColor(col); c.setFillColor(col); c.setLineWidth(w)
    a = math.atan2(y2 - y1, x2 - x1); h = 7
    c.line(x1, y1, x2 - h * 0.8 * math.cos(a), y2 - h * 0.8 * math.sin(a))
    pa = c.beginPath(); pa.moveTo(x2, y2)
    pa.lineTo(x2 - h * math.cos(a - 0.45), y2 - h * math.sin(a - 0.45)); pa.lineTo(x2 - h * math.cos(a + 0.45), y2 - h * math.sin(a + 0.45)); pa.close()
    c.drawPath(pa, fill=1, stroke=0); c.restoreState()


# ---------------------------------------------------------------- page sections
def header(d, j, folder, col):
    c = d.c; hc = HexColor(col)
    c.setFillColor(hc); c.rect(0, H - 150, W, 150, fill=1, stroke=0)
    c.setFillColor(tint(col, 0.75)); c.circle(W - 70, H - 40, 90, fill=1, stroke=0)
    c.setFillColor(hc); c.circle(W - 70, H - 40, 62, fill=1, stroke=0)
    icon(c, (j.get('features') or [{}])[0].get('icon', 'magic'), W - 92, H - 95, 54, tint(col, 0.6))
    d.text(M, H - 38, f"{folder[3:]}  ·  {j['category']}", 9.5, white)
    d.text(M, H - 76, j['name'], 27 if sw(j['name'], 27) < 380 else 20, white, bold=True)
    d.text(M, H - 98, j['repo'], 10, tint(col, 0.25))
    # badges
    bx = M; by = H - 132
    for label in (f"인기 순위 {j['rank']}위", f"스타 {int(j['stars']):,}개", f"난이도 {j['difficulty']}/5"):
        wdt = sw(label, 9.5) + 26
        c.setFillColor(white); c.roundRect(bx, by, wdt, 21, 10.5, fill=1, stroke=0)
        if label.startswith('스타'):
            star(c, bx + 11, by + 10.5, 5.5, 2.4, AMBER); d.text(bx + 19, by + 7, label, 9.5, INK)
        else:
            d.text(bx + 13, by + 7, label, 9.5, INK)
        bx += wdt + 8
    d.y = H - 170


def one_liner(d, j, col):
    c = d.c
    lines = wrap(j['one_liner'], 15, W - 2 * M - 50)
    h = 22 * len(lines) + 22
    c.setFillColor(tint(col, 0.1)); c.setStrokeColor(tint(col, 0.35)); c.roundRect(M, d.y - h, W - 2 * M, h, 10, fill=1, stroke=1)
    c.setFillColor(HexColor(col)); c.setFont('Helvetica-Bold', 40); c.drawString(M + 10, d.y - 38, '“')
    yy = d.y - 27
    for ln in lines:
        d.text(M + 40, yy, ln, 15, INK, bold=True); yy -= 22
    d.y -= h + 6


def analogy(d, j, col):
    a = j['analogy']; c = d.c
    d.heading('비유로 이해하기', col)
    pw = (W - 2 * M - 50) / 2; ph = 92
    d.need(ph + 40)
    top = d.y
    for i, (lab, txt, happy) in enumerate((('이 도구가 없으면', a['before'], False), ('이 도구를 쓰면', a['after'], True))):
        x = M + i * (pw + 50)
        bg = HexColor('#fef2f2') if not happy else HexColor('#f0fdf4'); fg = RED if not happy else GREEN
        c.setFillColor(bg); c.roundRect(x, top - ph, pw, ph, 10, fill=1, stroke=0)
        face(c, x + 30, top - ph / 2, 17, happy, fg)
        d.text(x + 58, top - 20, lab, 10, fg, bold=True)
        yy = top - 38
        for ln in wrap(txt, 9.5, pw - 68)[:4]:
            d.text(x + 58, yy, ln, 9.5, INK); yy -= 14
    arrow(c, M + pw + 10, top - ph / 2, M + pw + 40, top - ph / 2, HexColor(col), 3)
    d.y = top - ph - 10
    d.para(M + 4, a['text'], 10, W - 2 * M - 8, SUB)
    d.y -= 4


def what(d, j, col):
    d.heading('이게 뭐예요?', col)
    for s in j['what']:
        d.need(18)
        d.c.setFillColor(HexColor(col)); d.c.circle(M + 6, d.y - 7, 2.3, fill=1, stroke=0)
        d.para(M + 16, s, 10.5, W - 2 * M - 16, INK, 1.55)
        d.y -= 3


def flow(d, j, col):
    steps = j['flow'][:5]; n = len(steps)
    if not n:
        return
    d.heading('어떻게 작동할까요?', col)
    gap = 22; bw = (W - 2 * M - gap * (n - 1)) / n; bh = 96
    d.need(bh + 10)
    c = d.c; top = d.y
    for i, s in enumerate(steps):
        x = M + i * (bw + gap)
        c.setFillColor(tint(col, 0.08 + 0.1 * i)); c.setStrokeColor(tint(col, 0.4)); c.roundRect(x, top - bh, bw, bh, 9, fill=1, stroke=1)
        c.setFillColor(HexColor(col)); c.circle(x + bw / 2, top - 4, 12, fill=1, stroke=0)
        c.setFillColor(white); c.setFont('Helvetica-Bold', 12); c.drawCentredString(x + bw / 2, top - 8.5, str(i + 1))
        yy = top - 30
        for ln in wrap(s['label'], 11, bw - 12)[:2]:
            d.text(x + bw / 2 - sw(ln, 11) / 2, yy, ln, 11, INK, bold=True); yy -= 15
        yy -= 3
        for ln in wrap(s['desc'], 8.8, bw - 14)[:4]:
            d.text(x + bw / 2 - sw(ln, 8.8) / 2, yy, ln, 8.8, SUB); yy -= 12.5
        if i < n - 1:
            arrow(c, x + bw + 3, top - bh / 2, x + bw + gap - 3, top - bh / 2, HexColor(col), 2.2)
    d.y = top - bh - 12


def features(d, j, col):
    fs = j['features'][:4]
    d.heading('핵심 기능', col)
    cw = (W - 2 * M - 14) / 2; ch = 64; c = d.c
    for i, f in enumerate(fs):
        if i % 2 == 0:
            d.need(ch + 10); top = d.y
        x = M + (i % 2) * (cw + 14)
        c.setFillColor(SOFT); c.setStrokeColor(LINE); c.roundRect(x, top - ch, cw, ch, 9, fill=1, stroke=1)
        icon(c, f.get('icon', 'magic'), x + 28, top - ch / 2, 34, HexColor(col))
        d.text(x + 54, top - 22, f['title'], 11, INK, bold=True)
        yy = top - 38
        for ln in wrap(f['desc'], 9, cw - 64)[:2]:
            d.text(x + 54, yy, ln, 9, SUB); yy -= 12.5
        if i % 2 == 1 or i == len(fs) - 1:
            d.y = top - ch - 10


def channel(d, j, col):
    uses = j['channel_use'][:3]
    d.heading('우리 채널에서는 이렇게 써요', col)
    c = d.c
    for i, u in enumerate(uses):
        lines = wrap(u, 10, W - 2 * M - 80)
        h = max(44, 15 * len(lines) + 20)
        d.need(h + 8); top = d.y
        c.setFillColor(tint(col, 0.07)); c.roundRect(M, top - h, W - 2 * M, h, 9, fill=1, stroke=0)
        # phone
        px = M + 14; py = top - h / 2 - 15
        c.setFillColor(HexColor(col)); c.roundRect(px, py, 20, 30, 4, fill=1, stroke=0)
        c.setFillColor(white); c.rect(px + 2.5, py + 4, 15, 21, fill=1, stroke=0)
        c.setFillColor(HexColor(col)); pa = c.beginPath(); pa.moveTo(px + 7.5, py + 10); pa.lineTo(px + 7.5, py + 19); pa.lineTo(px + 14, py + 14.5); pa.close(); c.drawPath(pa, fill=1, stroke=0)
        d.text(M + 46, top - 16, f"장면 {i + 1}", 8.5, HexColor(col), bold=True)
        yy = top - 30
        for ln in lines:
            d.text(M + 46, yy, ln, 10, INK); yy -= 15
        d.y = top - h - 8


def pros_cons(d, j, col):
    d.heading('좋은 점 vs 아쉬운 점', col)
    c = d.c; cw = (W - 2 * M - 14) / 2
    cols = []
    for items, size in ((j['pros'], 9.5), (j['cons'], 9.5)):
        cols.append([wrap(t, size, cw - 40) for t in items[:3]])
    h = max(sum(15 * len(l) + 6 for l in col_) for col_ in cols) + 38
    d.need(h + 6); top = d.y
    for k, (lab, fg, bg, mark) in enumerate((('좋은 점', GREEN, '#f0fdf4', '+'), ('아쉬운 점', RED, '#fef2f2', '-'))):
        x = M + k * (cw + 14)
        c.setFillColor(HexColor(bg)); c.roundRect(x, top - h, cw, h, 9, fill=1, stroke=0)
        d.text(x + 14, top - 20, lab, 11, fg, bold=True)
        yy = top - 40
        for lines in cols[k]:
            c.setFillColor(fg); c.circle(x + 20, yy + 3.5, 6, fill=1, stroke=0)
            c.setFillColor(white); c.setFont('Helvetica-Bold', 10); c.drawCentredString(x + 20, yy - 0.3, mark)
            for ln in lines:
                d.text(x + 32, yy, ln, 9.5, INK); yy -= 15
            yy -= 6
    d.y = top - h - 8


def meta(d, j, col):
    d.heading('시작하기 전에', col)
    c = d.c; top = d.y; d.need(100); top = d.y
    # difficulty gauge
    d.text(M, top - 12, '난이도', 10, SUB, bold=True)
    for k in range(5):
        on = k < int(j['difficulty'])
        c.setFillColor(HexColor(col) if on else LINE); c.roundRect(M + 50 + k * 34, top - 15, 30, 11, 4, fill=1, stroke=0)
    d.text(M + 50 + 5 * 34 + 6, top - 13, ['', '쉬움', '할 만함', '보통', '어려움', '전문가용'][int(j['difficulty'])], 9.5, INK, bold=True)
    yy = top - 30
    for ln in wrap(j.get('difficulty_note', ''), 9, W - 2 * M - 50)[:2]:
        d.text(M + 50, yy, ln, 9, SUB); yy -= 12.5
    yy -= 6
    d.text(M, yy - 2, '비용', 10, SUB, bold=True)
    icon(c, 'money', M + 59, yy + 2, 15, AMBER)
    for ln in wrap(j.get('cost', ''), 9.5, W - 2 * M - 75)[:2]:
        d.text(M + 72, yy - 2, ln, 9.5, INK); yy -= 13.5
    yy -= 8
    d.text(M, yy - 2, '준비물', 10, SUB, bold=True)
    cx = M + 50; cy = yy - 6
    for n in j.get('needs', [])[:4]:
        wdt = sw(n, 9) + 18
        if cx + wdt > W - M:
            cx = M + 50; cy -= 22
        c.setFillColor(tint(col, 0.12)); c.roundRect(cx, cy - 3, wdt, 18, 9, fill=1, stroke=0)
        d.text(cx + 9, cy + 2, n, 9, INK); cx += wdt + 6
    d.y = cy - 14


def glossary(d, j, col):
    g = j.get('glossary', [])[:3]
    if not g:
        return
    d.heading('어려운 말 풀이', col)
    c = d.c
    for t in g:
        lines = wrap(t['meaning'], 9.5, W - 2 * M - 120)
        h = 15 * len(lines) + 10
        d.need(h); top = d.y
        c.setFillColor(tint(col, 0.15)); c.roundRect(M, top - h + 2, 100, h - 4, 6, fill=1, stroke=0)
        d.text(M + 50 - sw(t['term'], 9.5) / 2, top - h / 2 - 3, t['term'], 9.5, INK, bold=True)
        yy = top - 15
        for ln in lines:
            d.text(M + 112, yy, ln, 9.5, INK); yy -= 15
        d.y = top - h - 2


def caution(d, j):
    t = j.get('caution', '').strip()
    if not t:
        return
    c = d.c
    lines = wrap(t, 9.5, W - 2 * M - 60)
    h = 15 * len(lines) + 26
    d.y -= 8; d.need(h + 6); top = d.y
    c.setFillColor(HexColor('#fffbeb')); c.setStrokeColor(HexColor('#fcd34d')); c.roundRect(M, top - h, W - 2 * M, h, 9, fill=1, stroke=1)
    # warning triangle
    tx, ty = M + 24, top - h / 2
    pa = c.beginPath(); pa.moveTo(tx, ty + 11); pa.lineTo(tx + 12, ty - 9); pa.lineTo(tx - 12, ty - 9); pa.close(); c.setFillColor(AMBER); c.drawPath(pa, fill=1, stroke=0)
    c.setFillColor(white); c.setFont('Helvetica-Bold', 12); c.drawCentredString(tx, ty - 6.5, '!')
    d.text(M + 46, top - 17, '꼭 주의하세요', 10, AMBER, bold=True)
    yy = top - 32
    for ln in lines:
        d.text(M + 46, yy, ln, 9.5, INK); yy -= 15
    d.y = top - h - 6


def sources(d, j, col):
    d.y -= 6
    d.need(40)
    d.c.setStrokeColor(LINE); d.c.line(M, d.y, W - M, d.y); d.y -= 6
    lic = f"  ·  라이선스: {j['license']}" if j.get('license') else ''
    d.para(M, f"링크: https://github.com/{j['repo']}{lic}", 8.5, W - 2 * M, SUB, 1.45)
    d.para(M, '근거(README에서 확인): ' + ' / '.join(j.get('sources', [])), 8, W - 2 * M, SUB, 1.45)


def render(j, out):
    folder, col = CAT2FOLDER[j['category']]
    d = Doc(out, f"{j['rank']:03d} {j['name']} - 쉽게 이해하기")
    d.foot = f"{j['name']}  ·  GitHub 마케팅 AI 툴 쉽게 이해하기  ·  README 기준 정리 (2026-11)"
    header(d, j, folder, col)
    one_liner(d, j, col)
    analogy(d, j, col)
    what(d, j, col)
    flow(d, j, col)
    features(d, j, col)
    channel(d, j, col)
    pros_cons(d, j, col)
    meta(d, j, col)
    glossary(d, j, col)
    caution(d, j)
    sources(d, j, col)
    d.footer(); d.c.save()
    return folder


def load_rows(work):
    rows = {}
    for l in open(os.path.join(work, 'repos.tsv'), encoding='utf-8'):
        r, cat, repo, st = l.rstrip('\n').split('\t')
        rows[int(r)] = dict(rank=int(r), category=cat, repo=repo, stars=int(st))
    return rows


def safe(name):
    return ''.join(ch if ch.isalnum() or ch in '-_.' else '-' for ch in name)


if __name__ == '__main__':
    work = os.path.dirname(os.path.abspath(__file__))
    rows = load_rows(work)
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(work, 'content', '*.json')))
    manifest = []
    for fp in files:
        j = json.load(open(fp, encoding='utf-8'))
        r = rows[int(j['rank'])]
        j.update(category=r['category'], repo=r['repo'], stars=r['stars'], rank=r['rank'])
        folder, _ = CAT2FOLDER[j['category']]
        os.makedirs(os.path.join(work, 'pdf', folder), exist_ok=True)
        out = os.path.join(work, 'pdf', folder, f"{j['rank']:03d}_{safe(j['name'])}.pdf")
        render(j, out)
        manifest.append(dict(rank=j['rank'], folder=folder, path=out, title=os.path.basename(out), size=os.path.getsize(out)))
    json.dump(manifest, open(os.path.join(work, 'manifest_last.json'), 'w'), ensure_ascii=False, indent=1)
    for m in manifest:
        print(m['size'], m['folder'], m['title'])
