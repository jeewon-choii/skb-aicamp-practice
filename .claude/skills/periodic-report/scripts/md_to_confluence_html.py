"""보고서 마크다운 → 컨플루언스 붙여넣기용 HTML.

사용: python md_to_confluence_html.py --md 보고서.md --out 보고서.html [--include 비교표=_work/비교표.html]

- 지원: # 제목, > 인용(결론), 1./- 목록, | 표 |, **굵게**, `코드`, ![](이미지), --- 구분선, 빈 줄 문단
- {{이름}} 자리에는 --include 로 준 HTML 파일 내용을 그대로 넣는다 (예: 비교표).
- 컨플루언스가 받아들이는 단순 태그만 쓴다. 결론은 SK Red, [확인]은 SK Orange.
"""
import argparse
import html as H
import re
from pathlib import Path

RED, ORANGE = "#EA002C", "#F47725"


def inline(s):
    s = H.escape(s, quote=False)
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1" width="800">', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = s.replace("[확인]", f'<strong style="color:{ORANGE}">[확인]</strong>')
    return s


def convert(md, includes):
    out, lines, i = [], md.splitlines(), 0
    title = ""
    while i < len(lines):
        ln = lines[i].rstrip()
        m = re.fullmatch(r"\{\{(.+?)\}\}", ln.strip())
        if m and m.group(1) in includes:
            out.append(includes[m.group(1)])
        elif ln.startswith("#"):
            lvl = min(len(ln) - len(ln.lstrip("#")) + 1, 4)  # # → h2 (컨플루언스 페이지 제목과 겹치지 않게)
            text = ln.lstrip("#").strip()
            title = title or text
            out.append(f"<h{lvl}>{inline(text)}</h{lvl}>")
        elif ln.startswith(">"):
            text = ln.lstrip("> ").strip()
            out.append(f'<p><strong style="color:{RED}">{inline(text).replace("<strong>", "").replace("</strong>", "")}</strong></p>')
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            out.append("<table>")
            for r, cells in enumerate(rows):
                tag = "th" if r == 0 else "td"
                out.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
            out.append("</table>")
            continue
        elif re.match(r"^(\d+\.|-)\s", ln):
            ordered = ln[0].isdigit()
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>")
            while i < len(lines) and re.match(r"^(\d+\.|-)\s", lines[i]):
                out.append(f"<li>{inline(re.sub(r'^(\d+\.|-)\s+', '', lines[i]))}</li>")
                i += 1
            out.append(f"</{tag}>")
            continue
        elif ln.strip() == "---":
            out.append("<hr>")
        elif ln.strip():
            para = [ln]
            while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(r"^(#|>|\||\d+\.\s|-\s|---|\{\{)", lines[i + 1]):
                i += 1
                para.append(lines[i].rstrip())
            out.append("<p>" + "<br>".join(inline(p) for p in para) + "</p>")
        i += 1
    body = "\n".join(out)
    return (f'<!DOCTYPE html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n<title>{H.escape(title)}</title>\n'
            f"</head>\n<body>\n{body}\n</body>\n</html>\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--include", action="append", default=[], help="이름=파일.html")
    a = ap.parse_args()
    md_path = Path(a.md)
    includes = {}
    for inc in a.include:
        k, v = inc.split("=", 1)
        includes[k] = Path(v).read_text(encoding="utf-8")
    Path(a.out).write_text(convert(md_path.read_text(encoding="utf-8"), includes), encoding="utf-8")
    print(f"저장: {a.out}")


if __name__ == "__main__":
    main()
