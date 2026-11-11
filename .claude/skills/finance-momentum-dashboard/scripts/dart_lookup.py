"""DART 기업개황에서 회사 이름으로 법인등록번호·업종·시장구분을 찾는다.

사용법:
  python dart_lookup.py --names "SK하이닉스,SK텔레콤,에스케이브로드밴드" --out companies.csv
  python dart_lookup.py --names-file names.txt --sector-map sectors.csv --out companies.csv

- names-file: 한 줄에 회사 하나. "회사명,사업군" 형식이면 사업군도 함께 기록한다.
- 결과 CSV 열: company,sector,crno,bizno,market,industry,dart_name,match,candidates
- match 열: exact(정확히 일치) / first(여러 후보 중 첫 번째) / none(못 찾음)
  exact가 아니면 사람이 후보를 보고 확인해야 한다.
"""
import argparse, csv, re, sys, time
import requests

BASE = "https://dart.fss.or.kr"


def clean(html):
    html = re.sub(r"<script[\s\S]*?</script>", " ", html)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def norm(s):
    return re.sub(r"[\s()（）㈜주식회사]", "", s or "").upper()


def search(sess, name):
    r = sess.post(f"{BASE}/dsae001/search.ax",
                  data={"textCrpNm": name, "currentPage": "1", "maxResults": "30"}, timeout=20)
    rows = []
    for tr in re.findall(r"<tr[\s\S]*?</tr>", r.text):
        code = re.search(r"\b(\d{8})\b", tr)
        text = clean(tr)
        if code and "일치하는" not in text:
            parts = text.split()
            # [시장구분약자] 회사명 [종목코드]
            nm = parts[1] if len(parts) > 1 else text
            rows.append({"code": code.group(1), "name": nm, "text": text})
    return rows


def detail(sess, code):
    t = clean(sess.get(f"{BASE}/dsae001/selectPopup.ax", params={"selectKey": code}, timeout=20).text)
    g = lambda p: (re.search(p, t) or [None, ""])[1]
    return {
        "dart_name": g(r"회사이름 (.+?) (?:정보 더보기|영문명|rss)"),
        "crno": g(r"법인등록번호 ([\d-]+)"),
        "bizno": g(r"사업자등록번호 ([\d-]+)"),
        "market": g(r"법인구분 (\S+)"),
        "industry": g(r"업종명 (.+?) 설립일"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", help="쉼표로 구분한 회사 이름")
    ap.add_argument("--names-file", help="한 줄에 '회사명' 또는 '회사명,사업군'")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    items = []
    if a.names:
        items += [(n.strip(), "") for n in a.names.split(",") if n.strip()]
    if a.names_file:
        for line in open(a.names_file, encoding="utf-8-sig"):
            p = [x.strip() for x in line.split(",")]
            if p and p[0]:
                items.append((p[0], p[1] if len(p) > 1 else ""))
    if not items:
        sys.exit("회사 이름이 없어요. --names 또는 --names-file을 주세요.")

    sess = requests.Session()
    sess.headers["User-Agent"] = "Mozilla/5.0"
    sess.get(f"{BASE}/dsae001/main.do", timeout=20)

    out = []
    for name, sector in items:
        cands = search(sess, name)
        exact = [c for c in cands if norm(c["name"]) == norm(name)]
        pick, match = (exact[0], "exact") if exact else ((cands[0], "first") if cands else (None, "none"))
        row = {"company": name, "sector": sector, "match": match,
               "candidates": " | ".join(c["text"] for c in cands[:6])}
        if pick:
            row.update(detail(sess, pick["code"]))
        out.append(row)
        print(f"{name:16s} {match:5s} {row.get('crno', ''):16s} {row.get('dart_name', '')}")
        time.sleep(0.3)

    cols = ["company", "sector", "crno", "bizno", "market", "industry", "dart_name", "match", "candidates"]
    with open(a.out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(out)
    bad = [r["company"] for r in out if r["match"] != "exact"]
    print(f"\n저장: {a.out} · {len(out)}곳 · 정확히 일치 {len(out) - len(bad)}곳")
    if bad:
        print("확인 필요:", ", ".join(bad))


if __name__ == "__main__":
    main()
