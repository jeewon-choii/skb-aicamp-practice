"""CEO 보고용 도식 PNG 생성기 (Pillow만 사용).

사용: python make_diagram.py --spec diagram.json --out 도식.png
형식: references/diagram-patterns.md 참고 (flow / compare / timeline / structure)
"""
import argparse
import json
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# SKB 색
RED = "#EA002C"
ORANGE = "#F47725"
TEXT = "#202124"
TEXT2 = "#5F6368"
BG = "#FFFFFF"
CARD = "#F7F8FA"
BORDER = "#D0D4DA"
GOOD = "#287D4E"

W = 1600
PAD = 60

FONT_CANDIDATES = [
    # Pretendard (있으면 우선)
    os.path.expanduser("~/Library/Fonts/Pretendard-Regular.otf"),
    "/Library/Fonts/Pretendard-Regular.otf",
    r"C:\Windows\Fonts\Pretendard-Regular.otf",
    # macOS
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    # Windows
    r"C:\Windows\Fonts\malgun.ttf",
    # Linux
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
]
BOLD_CANDIDATES = [
    os.path.expanduser("~/Library/Fonts/Pretendard-Bold.otf"),
    "/Library/Fonts/Pretendard-Bold.otf",
    r"C:\Windows\Fonts\Pretendard-Bold.otf",
    r"C:\Windows\Fonts\malgunbd.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
]


def _load(paths, size, ttc_index=0):
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size, index=ttc_index if p.endswith(".ttc") else 0)
            except OSError:
                continue
    return None


def font(size, bold=False):
    f = None
    if bold:
        f = _load(BOLD_CANDIDATES, size)
        if f is None:  # AppleSDGothicNeo.ttc 안의 Bold (index 6)
            f = _load(["/System/Library/Fonts/AppleSDGothicNeo.ttc"], size, ttc_index=6)
    if f is None:
        f = _load(FONT_CANDIDATES, size)
    if f is None:
        sys.exit("한글 글꼴을 찾지 못했어요. Pretendard·맑은 고딕·Apple SD Gothic Neo 중 하나가 필요해요.")
    return f


def text_w(d, s, f):
    return d.textlength(s, font=f)


def wrap(d, s, f, max_w):
    """글자 단위 줄바꿈 (한글은 띄어쓰기 없이도 나눔)."""
    lines = []
    for para in str(s).split("\n"):
        cur = ""
        for word in para.split(" "):
            cand = (cur + " " + word).strip()
            if text_w(d, cand, f) <= max_w:
                cur = cand
                continue
            if cur:
                lines.append(cur)
            cur = ""
            for ch in word:
                if text_w(d, cur + ch, f) <= max_w:
                    cur += ch
                else:
                    lines.append(cur)
                    cur = ch
        lines.append(cur)
    return [l for l in lines if l != ""] or [""]


def draw_lines(d, lines, f, cx, y, fill, line_h, align="center", x_left=None):
    for ln in lines:
        if align == "center":
            d.text((cx - text_w(d, ln, f) / 2, y), ln, font=f, fill=fill)
        else:
            d.text((x_left, y), ln, font=f, fill=fill)
        y += line_h
    return y


def box(d, xy, highlight=False, fill=CARD):
    d.rounded_rectangle(xy, radius=18, fill=fill,
                        outline=RED if highlight else BORDER, width=5 if highlight else 2)


def arrow(d, x1, y1, x2, y2, color=TEXT2):
    d.line([(x1, y1), (x2, y2)], fill=color, width=5)
    if x2 != x1:  # 가로 화살표
        s = 1 if x2 > x1 else -1
        d.polygon([(x2, y2), (x2 - 18 * s, y2 - 12), (x2 - 18 * s, y2 + 12)], fill=color)
    else:
        d.polygon([(x2, y2), (x2 - 12, y2 - 18), (x2 + 12, y2 - 18)], fill=color)


def card_content(d, item, max_w):
    """카드 안 글자 줄 계산 → (label_lines, sub_lines, height)"""
    fl, fs = font(38, bold=True), font(28)
    label = ("● " if item.get("highlight") else "") + str(item.get("label", ""))
    ll = wrap(d, label, fl, max_w)
    sl = wrap(d, item.get("sub", ""), fs, max_w) if item.get("sub") else []
    h = len(ll) * 50 + (len(sl) * 40 + 10 if sl else 0)
    return ll, sl, h


def draw_card(d, x0, y0, x1, y1, item, ll, sl, content_h):
    box(d, (x0, y0, x1, y1), item.get("highlight"))
    cx = (x0 + x1) / 2
    y = y0 + ((y1 - y0) - content_h) / 2
    y = draw_lines(d, ll, font(38, bold=True), cx, y, RED if item.get("highlight") else TEXT, 50)
    if sl:
        draw_lines(d, sl, font(28), cx, y + 10, TEXT2, 40)


# ---------- 유형별 ----------

def render_flow(d, spec, y):
    items = spec["items"]
    n = len(items)
    gap = 70
    bw = (W - 2 * PAD - gap * (n - 1)) / n
    inner = bw - 40
    contents = [card_content(d, it, inner) for it in items]
    bh = max(c[2] for c in contents) + 70
    for i, (it, (ll, sl, ch)) in enumerate(zip(items, contents)):
        x0 = PAD + i * (bw + gap)
        draw_card(d, x0, y, x0 + bw, y + bh, it, ll, sl, ch)
        if i < n - 1:
            arrow(d, x0 + bw + 10, y + bh / 2, x0 + bw + gap - 10, y + bh / 2)
    return y + bh


def render_structure(d, spec, y):
    root = spec["root"]
    items = spec["items"]
    rw = 640
    ll, sl, ch = card_content(d, root, rw - 40)
    rh = ch + 70
    rx0 = (W - rw) / 2
    box(d, (rx0, y, rx0 + rw, y + rh), root.get("highlight"), fill="#FFF4F6")
    cy = y + (rh - ch) / 2
    cy = draw_lines(d, ll, font(38, bold=True), W / 2, cy, TEXT, 50)
    if sl:
        draw_lines(d, sl, font(28), W / 2, cy + 10, TEXT2, 40)
    y_bus = y + rh + 50
    d.line([(W / 2, y + rh), (W / 2, y_bus)], fill=TEXT2, width=5)
    n = len(items)
    gap = 40
    bw = (W - 2 * PAD - gap * (n - 1)) / n
    contents = [card_content(d, it, bw - 40) for it in items]
    bh = max(c[2] for c in contents) + 70
    centers = [PAD + i * (bw + gap) + bw / 2 for i in range(n)]
    if n > 1:
        d.line([(centers[0], y_bus), (centers[-1], y_bus)], fill=TEXT2, width=5)
    y_child = y_bus + 50
    for c, it, (ll, sl, ch) in zip(centers, items, contents):
        arrow(d, c, y_bus, c, y_child - 4)
        draw_card(d, c - bw / 2, y_child, c + bw / 2, y_child + bh, it, ll, sl, ch)
    return y_child + bh


def render_compare(d, spec, y):
    rows = spec["rows"]
    lab_w = 360
    col_w = (W - 2 * PAD - lab_w - 20 - 70) / 2
    xl = PAD + lab_w + 20
    xr = xl + col_w + 70
    fh = font(36, bold=True)
    # 헤더
    hh = 80
    box(d, (xl, y, xl + col_w, y + hh), fill="#EEF0F3")
    box(d, (xr, y, xr + col_w, y + hh), fill="#FFF4F6")
    d.text((xl + col_w / 2 - text_w(d, spec.get("left_title", "현재"), fh) / 2, y + 20),
           spec.get("left_title", "현재"), font=fh, fill=TEXT2)
    d.text((xr + col_w / 2 - text_w(d, spec.get("right_title", "개선안"), fh) / 2, y + 20),
           spec.get("right_title", "개선안"), font=fh, fill=RED)
    y += hh + 20
    fl, fv = font(32, bold=True), font(32)
    for r in rows:
        hl = r.get("highlight")
        label = ("● " if hl else "") + str(r["label"])
        ll = wrap(d, label, fl, lab_w - 30)
        lv = wrap(d, r.get("left", ""), fv, col_w - 50)
        rv = wrap(d, r.get("right", ""), fv, col_w - 50)
        rh = max(len(ll), len(lv), len(rv)) * 46 + 50
        box(d, (PAD, y, PAD + lab_w, y + rh), hl, fill=BG)
        box(d, (xl, y, xl + col_w, y + rh), fill=CARD)
        box(d, (xr, y, xr + col_w, y + rh), hl, fill=CARD)
        def mid(lines):
            return y + (rh - len(lines) * 46) / 2
        draw_lines(d, ll, fl, 0, mid(ll), RED if hl else TEXT, 46, align="left", x_left=PAD + 24)
        draw_lines(d, lv, fv, xl + col_w / 2, mid(lv), TEXT2, 46)
        draw_lines(d, rv, font(32, bold=True), xr + col_w / 2, mid(rv), TEXT, 46)
        arrow(d, xl + col_w + 12, y + rh / 2, xr - 12, y + rh / 2, color=ORANGE)
        y += rh + 16
    return y


def render_timeline(d, spec, y):
    items = spec["items"]
    n = len(items)
    seg = (W - 2 * PAD) / n
    line_y = y + 90
    d.line([(PAD + seg / 2, line_y), (W - PAD - seg / 2, line_y)], fill=BORDER, width=8)
    fd, fl = font(34, bold=True), font(32)
    bottom = line_y
    for i, it in enumerate(items):
        cx = PAD + seg * i + seg / 2
        done, hl = it.get("done"), it.get("highlight")
        date = str(it.get("date", ""))
        d.text((cx - text_w(d, date, fd) / 2, y), date, font=fd, fill=RED if hl else TEXT2)
        r = 26
        color = RED if hl else (GOOD if done else TEXT2)
        if done:
            d.ellipse((cx - r, line_y - r, cx + r, line_y + r), fill=color)
            d.line([(cx - 12, line_y), (cx - 3, line_y + 10), (cx + 13, line_y - 10)], fill=BG, width=6)
        else:
            d.ellipse((cx - r, line_y - r, cx + r, line_y + r), fill=BG, outline=color, width=6)
        label = ("● " if hl else "") + str(it.get("label", ""))
        status = "완료" if done else "예정"
        ll = wrap(d, label, fl, seg - 30)
        yy = draw_lines(d, ll, fl, cx, line_y + 50, RED if hl else TEXT, 44)
        yy = draw_lines(d, [status], font(26), cx, yy + 4, TEXT2, 36)
        bottom = max(bottom, yy)
    return bottom


RENDER = {"flow": render_flow, "structure": render_structure,
          "compare": render_compare, "timeline": render_timeline}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    t = spec.get("type")
    if t not in RENDER:
        sys.exit(f"type은 {list(RENDER)} 중 하나여야 해요. (받은 값: {t})")

    img = Image.new("RGB", (W, 3000), BG)
    d = ImageDraw.Draw(img)
    y = PAD
    if spec.get("title"):
        d.rectangle((PAD, y + 6, PAD + 10, y + 52), fill=RED)
        d.text((PAD + 28, y), spec["title"], font=font(46, bold=True), fill=TEXT)
        y += 100
    y = RENDER[t](d, spec, y)
    y += 40
    legend = "● 빨간색 표시 = 주목할 곳" if "highlight" in json.dumps(spec) else ""
    note = "   ".join(s for s in [spec.get("note", ""), legend] if s)
    if note:
        for ln in wrap(d, note, font(26), W - 2 * PAD):
            d.text((PAD, y), ln, font=font(26), fill=TEXT2)
            y += 38
    img = img.crop((0, 0, W, int(y + PAD)))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    img.save(a.out)
    print(f"저장: {a.out} ({img.width}x{img.height})")


if __name__ == "__main__":
    main()
