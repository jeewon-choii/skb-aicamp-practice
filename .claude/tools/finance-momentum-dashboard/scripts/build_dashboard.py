"""표준 재무표(CSV/XLSX)로 재무 개선 모멘텀을 계산하고 HTML 대시보드를 만든다.

사용법:
  python build_dashboard.py --input fin_long.csv --unit 원 \
      --title "SK 계열사 재무 개선 모멘텀" --source "공공데이터포털 금융위원회_기업 재무정보 API" \
      --out 결과/대시보드.html

표준 재무표 열 (references/data-format.md 참고):
  필수: company, year, sales, op_income, net_income, total_debt, total_equity
  선택: sector, basis(연결/별도), total_assets, market, industry, crno, api_debt_ratio
--unit: 입력 금액 단위 (원/천원/백만원/억원). 대시보드는 억원으로 표시한다.
"""
import argparse, csv, json, math, sys
from collections import defaultdict
from pathlib import Path

UNIT = {"원": 1e-8, "천원": 1e-5, "백만원": 1e-2, "억원": 1.0}
NUM = ["sales", "op_income", "net_income", "total_assets", "total_debt", "total_equity"]
CHECKS = ["매출 증가", "영업이익 증가", "영업이익률 상승", "순이익 증가", "부채비율 하락"]
HERE = Path(__file__).resolve().parent


def read_rows(path):
    p = Path(path)
    if p.suffix.lower() in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook
        ws = load_workbook(p, data_only=True, read_only=True).active
        it = ws.iter_rows(values_only=True)
        hdr = [str(h).strip() if h is not None else "" for h in next(it)]
        return [dict(zip(hdr, r)) for r in it if any(v not in (None, "") for v in r)]
    for enc in ("utf-8-sig", "cp949"):
        try:
            return list(csv.DictReader(open(p, encoding=enc)))
        except UnicodeDecodeError:
            continue
    sys.exit(f"{p.name}: 인코딩을 읽지 못했어요.")


def num(v):
    if v is None or str(v).strip() in ("", "-"):
        return None
    s = str(v).replace(",", "").strip()
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    return float(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", nargs="+", required=True)
    ap.add_argument("--unit", default="원", choices=UNIT)
    ap.add_argument("--title", default="재무 개선 모멘텀")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--source", default="")
    ap.add_argument("--note", action="append", default=[], help="대시보드 하단에 덧붙일 설명 (여러 번 가능)")
    ap.add_argument("--excluded", default="", help="'회사:사유;회사:사유' 형식")
    ap.add_argument("--prefer", default="연결", choices=["연결", "별도"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    k = UNIT[a.unit]

    raw = [r for f in a.input for r in read_rows(f)]
    miss = [c for c in ["company", "year", "sales", "op_income", "net_income", "total_debt", "total_equity"]
            if raw and c not in raw[0]]
    if miss:
        sys.exit(f"표준 재무표에 없는 열: {', '.join(miss)}  (references/data-format.md 참고)")

    by = defaultdict(dict)    # company -> (year,basis) -> row
    meta = {}
    dup = []
    for r in raw:
        c = str(r["company"]).strip(); y = str(r["year"]).strip()[:4]
        b = (str(r.get("basis") or "").strip() or a.prefer)
        if (y, b) in by[c]:
            dup.append(f"{c} {y} {b}")
        by[c][(y, b)] = r
        m = meta.setdefault(c, {})
        for f in ["sector", "market", "industry", "crno"]:
            if r.get(f) and not m.get(f):
                m[f] = str(r[f]).strip()
    if dup:
        sys.exit("같은 회사·연도·기준 행이 두 번 이상 있어요: " + ", ".join(dup[:10]))

    all_years = sorted({y for c in by for (y, _) in by[c]})
    companies, warnings = [], []
    for c, recs in by.items():
        def ys(b): return sorted(y for (y, bb) in recs if bb == b)
        other = "별도" if a.prefer == "연결" else "연결"
        cand = sorted([(a.prefer, ys(a.prefer)), (other, ys(other))], key=lambda t: (-len(t[1]), t[0] != a.prefer))
        basis, years = cand[0]
        if len(years) < 2:
            warnings.append(f"{c}: 같은 기준의 연도가 2개 미만이라 제외"); continue
        yd = {}
        for y in years:
            r = recs[(y, basis)]
            v = {f: (num(r.get(f)) * k if num(r.get(f)) is not None else None) for f in NUM}
            if None in (v["sales"], v["op_income"], v["net_income"], v["total_debt"], v["total_equity"]):
                warnings.append(f"{c} {y}: 빈 값이 있어 이 연도 제외"); continue
            eq = v["total_equity"]
            dr = v["total_debt"] / eq * 100 if eq > 0 else None
            api = num(r.get("api_debt_ratio"))
            if api is not None and dr is not None and abs(api - dr) > 0.1:
                warnings.append(f"{c} {y}: 부채비율 계산 {dr:.1f}% vs 원본 {api:.1f}%")
            yd[y] = dict(sales=v["sales"], op=v["op_income"], net=v["net_income"], assets=v["total_assets"],
                         debt=v["total_debt"], equity=eq,
                         margin=(v["op_income"] / v["sales"] * 100 if v["sales"] else None), debtRatio=dr)
        ys_ok = sorted(yd)
        if len(ys_ok) < 2:
            warnings.append(f"{c}: 쓸 수 있는 연도가 2개 미만이라 제외"); continue
        scores = {}
        for p, q in zip(ys_ok, ys_ok[1:]):
            A, B = yd[p], yd[q]
            chk = {
                "매출 증가": B["sales"] > A["sales"],
                "영업이익 증가": B["op"] > A["op"],
                "영업이익률 상승": A["margin"] is not None and B["margin"] is not None and B["margin"] > A["margin"],
                "순이익 증가": B["net"] > A["net"],
                "부채비율 하락": A["debtRatio"] is not None and B["debtRatio"] is not None and B["debtRatio"] < A["debtRatio"],
            }
            scores[q] = {"score": sum(chk.values()), "checks": chk}
        m = meta.get(c, {})
        companies.append(dict(name=c, sector=m.get("sector") or "기타", market=m.get("market", ""),
                              industry=m.get("industry", ""), crno=m.get("crno", ""), basis=basis,
                              years=yd, scores=scores, records=len(recs)))

    if not companies:
        sys.exit("대시보드에 넣을 회사가 없어요. 경고: " + "; ".join(warnings))
    last = max(max(c["years"]) for c in companies)
    excluded = [{"name": x.split(":")[0].strip(), "reason": x.split(":", 1)[1].strip() if ":" in x else ""}
                for x in a.excluded.split(";") if x.strip()]
    G = {"meta": {"title": a.title, "subtitle": a.subtitle, "source": a.source, "unit_in": a.unit,
                  "lastYear": last, "years": all_years, "rawRows": len(raw), "prefer": a.prefer,
                  "notes": a.note},
         "companies": companies, "excluded": excluded}

    tpl = (HERE.parent / "assets" / "template.html").read_text(encoding="utf-8")
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(tpl.replace("__TITLE__", a.title).replace("__DATA__", json.dumps(G, ensure_ascii=False)),
                   encoding="utf-8")
    out.with_suffix(".data.json").write_text(json.dumps(G, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- 요약 출력 (채팅 보고용) ----
    print(f"저장: {out}")
    print(f"입력 원본 {len(raw)}행 · 회사 {len(by)}곳 → 대시보드 {len(companies)}곳 · 최근 연도 {last}")
    cats = {"개선(4~5)": 0, "혼조(2~3)": 0, "악화(0~1)": 0}
    for c in sorted(companies, key=lambda c: (-int(max(c["years"]) == last), -c["scores"][max(c["scores"])]["score"])):
        ly = max(c["scores"]); s = c["scores"][ly]["score"]
        if ly == last:
            cats["개선(4~5)" if s >= 4 else "혼조(2~3)" if s >= 2 else "악화(0~1)"] += 1
        print(f"  {c['name']:16s} {c['basis']} {ly} {s}점")
    print("분포(최근 연도 있는 회사):", cats)
    if warnings:
        print("확인 필요:"); [print("  -", w) for w in warnings]


if __name__ == "__main__":
    main()
