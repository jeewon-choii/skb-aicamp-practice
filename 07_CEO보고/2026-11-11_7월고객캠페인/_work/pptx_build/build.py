# 7월 고객 캠페인 CEO 보고 PPT 생성 (교육용 실습 자료) — python-pptx
# 사용: python build.py <원본폴더> <출력파일>
import sys, os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

SRC_DIR, OUT = sys.argv[1], sys.argv[2]
if os.path.exists(OUT):
    sys.exit(f"이미 있음: {OUT}")

FONT = "Apple SD Gothic Neo"
def rgb(h): return RGBColor.from_string(h)
RED, ORANGE, TXT, TXT2 = "EA002C", "F47725", "202124", "5F6368"
BG, BG2, LINE, GOOD, RED_TINT = "FFFFFF", "F7F8FA", "E5E7EB", "287D4E", "FDECEF"

SRC_NOTE = "출처: 운영기획팀 「7월 고객 캠페인 월간보고」(2026.08.04) · 교육용 실습 자료(가상 데이터)"
CHECK_NOTE = "* 담당자 확인 전 수치(원본 [확인] 표시)"

W, H = 13.333, 7.5
MX = 0.6; CW = W - 2 * MX

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(W), Inches(H)
BLANK = prs.slide_layouts[6]
prs.core_properties.title = "7월 고객 캠페인 결과 — CEO 보고"
prs.core_properties.author = "SKB AI Camp"


def set_font(run, size, color=TXT, bold=False):
    f = run.font
    f.size = Pt(size); f.bold = bold; f.color.rgb = rgb(color); f.name = FONT
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {}); rPr.append(el)
        el.set("typeface", FONT)


def text(slide, x, y, w, h, paras, size=16, color=TXT, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, space_after=0, name=None):
    """paras: str 또는 [(text, {size,color,bold}) ...] 문단 목록"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name: tb.name = name
    tf = tb.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    if isinstance(paras, str): paras = [(paras, {})]
    for i, (t, o) in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if space_after: p.space_after = Pt(space_after)
        r = p.add_run(); r.text = t
        set_font(r, o.get("size", size), o.get("color", color), o.get("bold", bold))
    return tb


def card(slide, x, y, w, h, fill=BG2, line=LINE, lw=1.0, name=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if name: s.name = name
    s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
    if line: s.line.color.rgb = rgb(line); s.line.width = Pt(lw)
    else: s.line.fill.background()
    s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: s.adjustments[0] = radius
    return s


def title(slide, t):
    text(slide, MX, 0.4, CW, 1.0, t, size=32, bold=True, name="Title")


def footer(slide, n, total=5):
    text(slide, MX, 7.0, 6, 0.3, "SKB AI Camp · 교육용 실습 자료", size=10, color=TXT2, name="Footer")
    text(slide, W - MX - 1.0, 7.0, 1.0, 0.3, f"{n} / {total}", size=10, color=TXT2, align=PP_ALIGN.RIGHT, name="PageNo")


# ---------- 1. 표지 ----------
s = prs.slides.add_slide(BLANK)
text(s, MX, 1.5, 7, 0.5, "SK브로드밴드 · SKB AI Camp", size=20, bold=True, color=RED)
text(s, MX, 2.2, 7.4, 1.1, "7월 고객 캠페인 결과", size=48, bold=True, name="Title")
text(s, MX, 3.4, 7.4, 0.6, "CEO 보고 · 보고(인지) 사항", size=26, color=TXT2)
text(s, MX, 4.4, 7.4, 1.0, [("보고 범위: 7월 1일~31일, 8월 3일 18:00 마감 확정분", {}),
                            ("5개 지역 · 3개 활동(온라인안내·현장상담·기존고객안내)", {})],
     size=16, color=TXT2, space_after=4)
card(s, 8.4, 1.5, 4.33, 3.8, name="KeyCard")
text(s, 8.75, 1.9, 3.7, 0.5, "7월 유효신청", size=20, color=TXT2)
text(s, 8.75, 2.45, 3.7, 1.1, "7,520건", size=60, bold=True, color=RED)
text(s, 8.75, 3.8, 3.7, 1.2, [("목표 7,950건의 94.6%*", {}), ("예산 86.6% 집행", {})], size=20, space_after=6)
text(s, MX, 6.3, CW, 0.6, [(SRC_NOTE, {}), (CHECK_NOTE, {})], size=11, color=TXT2, space_after=2)

# ---------- 2. 결론 + 핵심 숫자 ----------
s = prs.slides.add_slide(BLANK)
title(s, "7월 유효신청 7,520건(목표의 94.6%*), 예산 86.6% 집행 — 영남 비용 점검 필요")
cards = [
    ("유효신청", "7,520건", ["목표 7,950건 대비", "▼ 430건 (94.6%)*"], RED),
    ("집행액", "6,060만 원", ["승인예산 7,000만 원", "집행률 86.6%"], ORANGE),
    ("신청전환율", "21.4%", ["상담 35,150건 기준"], TXT),
    ("건당비용(전체)", "8,059원*", ["6,060만 원 ÷ 7,520건"], TXT),
]
gap = 0.3; cw = (CW - gap * 3) / 4; cy, ch = 1.75, 2.6
for i, (lab, val, sub, col) in enumerate(cards):
    x = MX + i * (cw + gap)
    card(s, x, cy, cw, ch, name=f"StatCard{i+1}")
    text(s, x + 0.25, cy + 0.25, cw - 0.5, 0.4, lab, size=18, color=TXT2)
    text(s, x + 0.25, cy + 0.7, cw - 0.5, 0.8, val, size=36, bold=True, color=col)
    text(s, x + 0.25, cy + 1.6, cw - 0.5, 0.85, [(t, {}) for t in sub], size=16)
py, ph = 4.7, 1.5; pw = (CW - gap) / 2
card(s, MX, py, pw, ph, name="PointGood")
text(s, MX + 0.3, py + 0.2, pw - 0.6, ph - 0.4,
     [("▲ 충청 — 전환율 25.2%", {"size": 22, "bold": True, "color": GOOD}),
      ("5개 지역 중 가장 높음 → 상담 방식 확산 검토", {"size": 16})], anchor=MSO_ANCHOR.MIDDLE, space_after=6)
card(s, MX + pw + gap, py, pw, ph, fill=RED_TINT, line=RED, lw=1.5, name="PointBad")
text(s, MX + pw + gap + 0.3, py + 0.2, pw - 0.6, ph - 0.4,
     [("● 영남 — 건당비용 10,395원", {"size": 22, "bold": True, "color": RED}),
      ("5개 지역 중 가장 높음 → 채널 구성·비용 점검", {"size": 16})], anchor=MSO_ANCHOR.MIDDLE, space_after=6)
text(s, MX, 6.5, CW, 0.35, SRC_NOTE + "   " + CHECK_NOTE, size=11, color=TXT2)
footer(s, 2)

# ---------- 3. 도식 ----------
s = prs.slides.add_slide(BLANK)
title(s, "8월 검토 3가지 — 영남 비용 점검에 주목")
iw = 11.6; ih = iw * 738 / 1600
pic = s.shapes.add_picture(os.path.join(SRC_DIR, "도식.png"), Inches((W - iw) / 2), Inches(1.4), Inches(iw), Inches(ih))
pic.name = "Diagram"
pic._element.nvPicPr.cNvPr.set("descr", "7월 유효신청 7,520건(목표 7,950건의 94.6%, 예산 86.6% 집행)에서 8월 검토 3가지로 이어지는 도식: "
                               "A. 충청 방식 확산(전환율 25.2%, 최고), B. 영남 비용 점검(건당비용 10,395원, 최고, 주목), "
                               "C. 8월 신규 비용(별도 승인 후 집행, 금액 미정)")
footer(s, 3)

# ---------- 4. 지역별 표 ----------
s = prs.slides.add_slide(BLANK)
title(s, "충청은 전환율 25.2%로 최고, 영남은 건당비용 10,395원으로 최고")
header = ["지역", "집행액", "유효신청", "목표 달성률*", "전환율", "건당비용"]
data = [
    ["수도권", "1,650만 원", "2,080건", "94.5%", "19.8%", "7,933원"],
    ["충청", "1,020만 원", "1,610건", "97.6%", "▲ 25.2% 최고", "6,335원"],
    ["호남", "970만 원", "1,300건", "89.7%", "22.2%", "7,462원"],
    ["영남", "1,580만 원", "1,520건", "98.1%", "18.8%", "● 10,395원 최고"],
    ["강원·제주", "840만 원", "1,010건", "91.8%", "23.5%", "8,317원"],
    ["합계", "6,060만 원", "7,520건", "94.6%", "21.4%", "8,059원"],
]
colW = [1.9, 2.1, 1.8, 2.0, 2.2, CW - (1.9 + 2.1 + 1.8 + 2.0 + 2.2)]
nrows = len(data) + 1
tshape = s.shapes.add_table(nrows, 6, Inches(MX), Inches(1.6), Inches(CW), Inches(0.6 * nrows))
tshape.name = "RegionTable"
tbl = tshape.table
# 기본 표 스타일 제거(밴드 색 등)
tblPr = tshape._element.graphic.graphicData.tbl.tblPr
tblPr.set("firstRow", "0"); tblPr.set("bandRow", "0")
for j, w_ in enumerate(colW): tbl.columns[j].width = Inches(w_)
for i in range(nrows): tbl.rows[i].height = Inches(0.6)


def set_border(cell, color=LINE, w=12700):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
        ln = tcPr.makeelement(qn(tag), {"w": str(w)})
        sf = ln.makeelement(qn("a:solidFill"), {}); c = sf.makeelement(qn("a:srgbClr"), {"val": color})
        sf.append(c); ln.append(sf); tcPr.append(ln)


def fill_cell(cell, t, fill=BG, color=TXT, bold=False, align=PP_ALIGN.RIGHT):
    cell.fill.solid(); cell.fill.fore_color.rgb = rgb(fill)
    cell.margin_left = cell.margin_right = Inches(0.15)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = cell.text_frame.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = t; set_font(r, 18, color, bold)
    set_border(cell)


for j, t in enumerate(header):
    fill_cell(tbl.cell(0, j), t, fill=BG2, bold=True, align=PP_ALIGN.CENTER)
for i, row in enumerate(data, start=1):
    is_total = row[0] == "합계"; is_yn = row[0] == "영남"
    rf = BG2 if is_total else (RED_TINT if is_yn else BG)
    for j, t in enumerate(row):
        color, bold = TXT, is_total or j == 0
        if row[0] == "충청" and j == 4: color, bold = GOOD, True
        if is_yn and j == 5: color, bold = RED, True
        fill_cell(tbl.cell(i, j), t, fill=rf, color=color, bold=bold, align=PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT)
text(s, MX, 6.05, CW, 0.8,
     [("집행액은 부가세 제외 · 유효신청 = 신청 − 취소 · 합계 비율은 지역 합계로 계산(단순 평균 아님)", {}),
      (SRC_NOTE + "   " + CHECK_NOTE, {})], size=11, color=TXT2, space_after=4)
footer(s, 4)

# ---------- 5. 결정·다음 할 일 ----------
s = prs.slides.add_slide(BLANK)
title(s, "지금 결정할 사항은 없습니다 — 8월 신규 비용은 별도 승인 요청 예정")
ly, lh, lw = 1.75, 4.4, 4.0
card(s, MX, ly, lw, lh, name="DecisionCard")
text(s, MX + 0.3, ly + 0.3, lw - 0.6, 0.45, "CEO 결정 사항", size=18, color=TXT2)
text(s, MX + 0.3, ly + 0.85, lw - 0.6, 1.0, "없음", size=54, bold=True)
text(s, MX + 0.3, ly + 2.0, lw - 0.6, 2.2,
     [("이번 보고는 보고(인지) 사항입니다.", {}),
      ("8월 신규 활동·콘텐츠 제작비는 별도로 승인을 요청할 예정입니다(금액 미정*).", {})], size=16, space_after=8)
rx = MX + lw + 0.4; rw = CW - lw - 0.4
text(s, rx, ly, rw, 0.45, "다음 할 일", size=20, bold=True)
items = [("A", "충청 상담 방식", "다른 지역에 적용할 수 있는지 확인", False),
         ("B", "영남 채널 구성·비용 점검 ← 주목", "온라인·현장·기존고객 안내 구성과 건당비용 점검", True),
         ("C", "8월 신규 활동·콘텐츠 제작비", "별도 승인 후 집행", False)]
ih, ig = 1.1, 0.25
for i, (k, t, d, hi) in enumerate(items):
    y = ly + 0.65 + i * (ih + ig)
    card(s, rx, y, rw, ih, fill=RED_TINT if hi else BG2, line=RED if hi else LINE, lw=1.5 if hi else 1.0, name=f"Next{k}")
    b = card(s, rx + 0.25, y + (ih - 0.6) / 2, 0.6, 0.6, fill=RED if hi else TXT2, line=None, shape=MSO_SHAPE.OVAL, name=f"Badge{k}")
    text(s, rx + 0.25, y + (ih - 0.6) / 2, 0.6, 0.6, k, size=20, bold=True, color="FFFFFF", align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, rx + 1.1, y + 0.1, rw - 1.3, ih - 0.2,
         [(t, {"size": 20, "bold": True, "color": RED if hi else TXT}), (d, {"size": 16})], anchor=MSO_ANCHOR.MIDDLE, space_after=2)
text(s, MX, 6.5, CW, 0.35, SRC_NOTE + "   * 원본 [확인] 표시 6건은 담당자 확인 전", size=11, color=TXT2)
footer(s, 5)

prs.save(OUT)
print("saved:", OUT)
