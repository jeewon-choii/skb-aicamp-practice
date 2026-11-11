"""공공데이터포털 「금융위원회_기업 재무정보」 요약재무제표를 받아 표준 재무표(CSV)로 저장한다.

사용법:
  python fetch_fin_api.py --companies companies.csv --years 2023-2025 --out fin_long.csv

- companies.csv: company,crno 열 필수. sector,market,industry 열이 있으면 그대로 옮긴다.
- API 키: 환경변수 DATA_GO_KR_API_KEY (현재 폴더 또는 상위 폴더의 .env도 읽음)
- 결과: 표준 재무표(단위 원). 연결·별도 행을 모두 저장하고 basis 열로 구분한다.
"""
import argparse, csv, os, sys, time
from pathlib import Path
import requests

URL = "https://apis.data.go.kr/1160100/service/GetFinaStatInfoService_V2/getSummFinaStat_V2"
FIELDS = {"sales": "enpSaleAmt", "op_income": "enpBzopPft", "net_income": "enpCrtmNpf",
          "total_assets": "enpTastAmt", "total_debt": "enpTdbtAmt", "total_equity": "enpTcptAmt"}


def load_key():
    key = os.getenv("DATA_GO_KR_API_KEY", "").strip()
    if not key:
        try:
            from dotenv import load_dotenv
            for d in [Path.cwd(), *Path.cwd().parents]:
                if (d / ".env").exists():
                    load_dotenv(d / ".env"); break
            key = os.getenv("DATA_GO_KR_API_KEY", "").strip()
        except ImportError:
            pass
    if not key or not key.isascii():
        sys.exit("DATA_GO_KR_API_KEY가 없어요. .env 파일이나 환경변수에 키를 넣어주세요.")
    return key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--companies", required=True)
    ap.add_argument("--years", default="2023-2025", help="예: 2023-2025")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    y0, y1 = [int(x) for x in a.years.split("-")]
    key = load_key()

    comps = list(csv.DictReader(open(a.companies, encoding="utf-8-sig")))
    rows, total = [], 0
    for c in comps:
        crno = (c.get("crno") or "").replace("-", "").strip()
        if not crno:
            print(f"{c['company']}: 법인등록번호 없음 → 건너뜀"); continue
        got = 0
        for y in range(y0, y1 + 1):
            for attempt in range(3):
                try:
                    r = requests.get(URL, params=dict(serviceKey=key, pageNo=1, numOfRows=20, resultType="json",
                                                      crno=crno, bizYear=str(y)), timeout=30)
                    if "SERVICE_KEY" in r.text[:500]:
                        sys.exit("API 키가 이 서비스에 등록되지 않았어요. data.go.kr 활용신청 상태를 확인해주세요.")
                    items = r.json()["response"]["body"]["items"]
                    items = items.get("item", []) if isinstance(items, dict) else []
                    items = [items] if isinstance(items, dict) else items
                    break
                except (requests.RequestException, ValueError, KeyError):
                    time.sleep(2); items = None
            if items is None:
                print(f"{c['company']} {y}: 연결 실패"); continue
            for it in items:
                if it.get("curCd") and it["curCd"] != "KRW":
                    print(f"{c['company']} {y}: 통화 {it['curCd']} → 제외"); continue
                row = {"company": c["company"], "sector": c.get("sector", ""), "market": c.get("market", ""),
                       "industry": c.get("industry", ""), "crno": c.get("crno", ""),
                       "basis": "연결" if it["fnclDcd"] == "110" else "별도",
                       "year": it["bizYear"], "base_date": it["basDt"]}
                for k, f in FIELDS.items():
                    row[k] = it.get(f) or ""
                row["api_debt_ratio"] = it.get("fnclDebtRto", "")
                rows.append(row); got += 1
        total += got
        print(f"{c['company']:16s} {got}건")
    cols = ["company", "sector", "market", "industry", "crno", "basis", "year", "base_date",
            *FIELDS.keys(), "api_debt_ratio"]
    with open(a.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"\n저장: {a.out} · 회사 {len(comps)}곳 · 원본 {total}건 (단위: 원)")


if __name__ == "__main__":
    main()
