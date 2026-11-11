"""전기 대비 비교표 만들기.

사용:
  python compare_periods.py --prev 지난기간.csv --curr 이번기간.csv --key 지역 \
    --ratio "전환율=유효신청/상담:%" --ratio "건당비용=집행액/유효신청:원" \
    --unit 집행액:원 --unit 유효신청:건 --unit 상담:건 \
    --prev-label 7월 --curr-label 8월 --out-dir _work

- CSV 첫 열(또는 --key)이 구분, 나머지는 숫자 열.
- '합계' 행이 있으면 그 값을 쓰고, 없으면 더한다.
- 비율은 분자 합계 ÷ 분모 합계. 비율 열이 CSV에 이미 있으면 그 값을 그대로 쓴다(지역 행).
  합계 행 비율은 합계 행에 값이 있으면 그 값, 없으면 분자 합계 ÷ 분모 합계.
결과: 비교표.md, 비교표.html, 변화요약.json
"""
import argparse
import json
import math
from pathlib import Path

import pandas as pd

TOTAL = "합계"


def read(path, key):
    df = pd.read_csv(path, encoding="utf-8-sig")
    key = key or df.columns[0]
    df[key] = df[key].astype(str).str.strip()
    for c in df.columns:
        if c != key:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", "").str.replace("%", "").str.strip(),
                                  errors="coerce")
    return df.set_index(key), key


def parse_ratio(s):
    name, rest = s.split("=", 1)
    expr, unit = (rest.split(":", 1) + [""])[:2]
    num, den = expr.split("/")
    return name.strip(), num.strip(), den.strip(), unit.strip()


def add_total_and_ratios(df, ratios):
    raw_cols = [c for c in df.columns if c not in {r[0] for r in ratios}]
    if TOTAL not in df.index:
        df.loc[TOTAL] = df[raw_cols].sum(min_count=1)
    for name, num, den, unit in ratios:
        if name not in df.columns:
            df[name] = math.nan
        for idx in df.index:
            if pd.isna(df.at[idx, name]) and num in df.columns and den in df.columns:
                n, d = df.at[idx, num], df.at[idx, den]
                if pd.notna(n) and pd.notna(d) and d != 0:
                    v = n / d
                    df.at[idx, name] = v * 100 if unit == "%" else v
    return df


def fmt(v, unit):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "자료 없음"
    if unit == "%":
        return f"{v:.1f}%"
    return f"{round(v):,}{unit}"


def fmt_diff(d, unit):
    if d is None or (isinstance(d, float) and math.isnan(d)):
        return "—"
    if unit == "%":
        if round(d, 1) == 0:
            return "– 0.0%p"
        return f"{'▲ +' if d > 0 else '▼ −'}{abs(d):.1f}%p"
    r = round(d)
    if r == 0:
        return f"– 0{unit}"
    return f"{'▲ +' if r > 0 else '▼ −'}{abs(r):,}{unit}"


def fmt_pct(p):
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "—"
    return f"{'+' if p > 0 else ('−' if p < 0 else '')}{abs(p):.1f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prev", required=True)
    ap.add_argument("--curr", required=True)
    ap.add_argument("--key")
    ap.add_argument("--ratio", action="append", default=[])
    ap.add_argument("--unit", action="append", default=[], help="열이름:단위")
    ap.add_argument("--metrics", help="표에 넣을 지표 순서 (쉼표 구분). 생략하면 모든 열")
    ap.add_argument("--prev-label", default="지난 기간")
    ap.add_argument("--curr-label", default="이번 기간")
    ap.add_argument("--out-dir", default=".")
    a = ap.parse_args()

    ratios = [parse_ratio(r) for r in a.ratio]
    units = dict(u.split(":", 1) for u in a.unit)
    units.update({r[0]: r[3] for r in ratios})

    prev, key = read(a.prev, a.key)
    curr, _ = read(a.curr, key)
    prev = add_total_and_ratios(prev, ratios)
    curr = add_total_and_ratios(curr, ratios)

    keys = [k for k in curr.index if k != TOTAL] + [k for k in prev.index if k not in curr.index and k != TOTAL]
    keys.append(TOTAL)
    metrics = a.metrics.split(",") if a.metrics else list(dict.fromkeys(list(curr.columns) + list(prev.columns)))

    md, html, changes = [], [], []
    for m in metrics:
        u = units.get(m, "")
        rows = []
        for k in keys:
            pv = prev.at[k, m] if (k in prev.index and m in prev.columns) else math.nan
            cv = curr.at[k, m] if (k in curr.index and m in curr.columns) else math.nan
            d = cv - pv if pd.notna(pv) and pd.notna(cv) else math.nan
            p = (d / pv * 100) if pd.notna(d) and pv not in (0,) and u != "%" else math.nan
            rows.append((k, pv, cv, d, p))
            if pd.notna(d):
                changes.append({"구분": k, "지표": m, "단위": u, a.prev_label: None if pd.isna(pv) else float(pv),
                                a.curr_label: float(cv), "증감": float(d),
                                "증감률(%)": None if pd.isna(p) else round(float(p), 1)})
        head = [key, a.prev_label, a.curr_label, "증감", "증감률" if u != "%" else "비고"]
        md.append(f"### {m}" + (f" ({u})" if u else ""))
        md.append("| " + " | ".join(head) + " |")
        md.append("|" + "---|" * len(head))
        html.append(f"<h3>{m}" + (f" ({u})" if u else "") + "</h3>\n<table>")
        html.append("<tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr>")
        for k, pv, cv, d, p in rows:
            cells = [k, fmt(pv, u), fmt(cv, u), fmt_diff(d, u), fmt_pct(p) if u != "%" else ""]
            if k == TOTAL:
                md.append("| " + " | ".join(f"**{c}**" if c else "" for c in cells) + " |")
                html.append("<tr>" + "".join(f"<td><strong>{c}</strong></td>" for c in cells) + "</tr>")
            else:
                md.append("| " + " | ".join(cells) + " |")
                html.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
        md.append("")
        html.append("</table>")

    # 변화요약: 합계 먼저, 그다음 구분별 변화가 큰 순 (비율은 %p 절대값, 나머지는 증감률 절대값)
    def score(c):
        if c["단위"] == "%":
            return abs(c["증감"]) * 5  # 1%p ≈ 5% 변화로 환산해 함께 정렬
        return abs(c["증감률(%)"] or 0)
    total = [c for c in changes if c["구분"] == TOTAL]
    rest = sorted([c for c in changes if c["구분"] != TOTAL], key=score, reverse=True)

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "비교표.md").write_text("\n".join(md), encoding="utf-8")
    (out / "비교표.html").write_text("\n".join(html), encoding="utf-8")
    (out / "변화요약.json").write_text(json.dumps({"합계": total, "변화큰순": rest}, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    print(f"저장: {out/'비교표.md'}, {out/'비교표.html'}, {out/'변화요약.json'}")
    print("변화 큰 순 상위 5:")
    for c in rest[:5]:
        print(f"  {c['구분']} {c['지표']}: {fmt(c[a.prev_label], c['단위'])} → {fmt(c[a.curr_label], c['단위'])} "
              f"({fmt_diff(c['증감'], c['단위'])})")


if __name__ == "__main__":
    main()
