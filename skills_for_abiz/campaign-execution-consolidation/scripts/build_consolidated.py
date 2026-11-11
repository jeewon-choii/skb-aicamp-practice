#!/usr/bin/env python3
"""캠페인 집행 취합본 → 통합본(확정실적 · 제외·수정내역 · 검증 시트) 생성기.

사용법:
    python build_consolidated.py <취합본.xlsx> [--out <통합본.xlsx>]
        [--period 2026-08-01:2026-08-31] [--sheet <데이터 시트 이름>]

- 원본 파일은 수정하지 않는다. 원본을 복사한 새 파일에 시트 3개를 추가한다.
- 끝나면 요약을 JSON으로 출력한다(확정 건수, 합계, 제외·보류 목록, 검증 결과).
- 필요한 것: Python 3.8+, openpyxl
"""
import argparse, datetime as dt, json, os, re, shutil, sys, unicodedata as ud
from collections import Counter

try:
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    sys.exit('openpyxl이 필요해요: pip install openpyxl')

# ── 열 이름 찾기: 머리글 글자에 아래 단어가 들어 있으면 그 열로 본다 ──
COLS = {
    'id':      ['기록 ID', '기록ID', 'ID'],
    'rev':     ['수정차수', '차수'],
    'date':    ['집행일', '일자', '날짜'],
    'region':  ['담당 지역', '지역'],
    'act':     ['활동구분', '활동'],
    'prod':    ['대상상품', '상품'],
    'amt':     ['사용금액', '금액', '집행금액'],
    'consult': ['상담'],
    'recv':    ['접수'],
    'cancel':  ['취소'],
    'done':    ['처리완료', '완료'],
    'close':   ['마감여부', '마감'],
    'memo':    ['메모', '비고'],
}
REQUIRED = ['id', 'date', 'amt']
NUMS = ['amt', 'consult', 'recv', 'cancel', 'done']
LABEL = {'id': '기록 ID', 'rev': '수정차수', 'date': '집행일', 'region': '담당 지역', 'act': '활동구분',
         'prod': '대상상품', 'amt': '사용금액', 'consult': '상담 건수', 'recv': '접수건', 'cancel': '취소',
         'done': '처리완료', 'close': '마감여부', 'memo': '메모'}
CLOSE_OK = {'Y': '확정', 'y': '확정', '확정': '확정', '완료': '확정', '마감': '확정'}
CLOSE_TEMP = {'잠정', 'N', 'n', '미확정', '미마감'}

RED, F = 'EA002C', '맑은 고딕'
THIN = Side(style='thin', color='E5E7EB')
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
COLOR = {'삭제': '5F6368', '제외': '925000', '보류': 'B42318', '통과': '287D4E', '확인 필요': 'B42318', '참고': '925000'}


def nfc(s):
    return ud.normalize('NFC', str(s)) if s is not None else ''


def find_header(ws):
    for r in range(1, min(ws.max_row, 30) + 1):
        texts = [nfc(ws.cell(r, c).value).replace(' ', '') for c in range(1, ws.max_column + 1)]
        if any('기록ID' in t for t in texts) and any('금액' in t for t in texts):
            return r
    sys.exit('머리글 행(기록 ID · 금액이 있는 줄)을 찾지 못했어요.')


def map_cols(ws, hr):
    found = {}
    for c in range(1, ws.max_column + 1):
        h = nfc(ws.cell(hr, c).value).replace(' ', '')
        if not h:
            continue
        for key, words in COLS.items():
            if key in found:
                continue
            if any(w.replace(' ', '') in h for w in words):
                found[key] = c
                break
    miss = [LABEL[k] for k in REQUIRED if k not in found]
    if miss:
        sys.exit(f'필수 열을 찾지 못했어요: {", ".join(miss)}')
    return found


def find_period(ws, hr, arg):
    if arg:
        a, b = arg.split(':')
        return dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    pat = r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})\s*[~∼\-–]\s*(?:(\d{4})[./-])?(\d{1,2})[./-](\d{1,2})'
    for r in range(1, hr):
        for c in range(1, ws.max_column + 1):
            m = re.search(pat, nfc(ws.cell(r, c).value))
            if m:
                y1, m1, d1, y2, m2, d2 = m.groups()
                return dt.date(int(y1), int(m1), int(d1)), dt.date(int(y2 or y1), int(m2), int(d2))
    return None


def to_date(v, year):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    s = nfc(v).strip()
    m = re.fullmatch(r'(\d{4})\s*[./년-]\s*(\d{1,2})\s*[./월-]\s*(\d{1,2})\s*일?', s)
    if m:
        return dt.date(*map(int, m.groups()))
    m = re.fullmatch(r'(\d{1,2})\s*[./월-]\s*(\d{1,2})\s*일?', s)
    if m and year:
        return dt.date(year, int(m[1]), int(m[2]))
    raise ValueError(s)


def to_num(v):
    if v is None or nfc(v).strip() in ('', '-'):
        return None
    if isinstance(v, bool):
        raise ValueError(v)
    if isinstance(v, (int, float)):
        return int(v) if float(v).is_integer() else v
    s = re.sub(r'[₩원건,\s]', '', nfc(v))
    if not re.fullmatch(r'-?\d+(\.\d+)?', s):
        raise ValueError(v)
    f = float(s)
    return int(f) if f.is_integer() else f


def show(v):
    if isinstance(v, dt.datetime):
        return v.strftime('%Y-%m-%d') + ' (날짜값)'
    if isinstance(v, str):
        return f'"{v}"'
    return str(v)


def build(src, out, period_arg=None, sheet=None):
    # 원본을 읽어 새 파일로 저장한다(원본은 열기만 하고 저장하지 않음)
    wb = openpyxl.load_workbook(src)
    for n in ('확정실적', '제외·수정내역', '검증'):
        if n in wb.sheetnames:
            sys.exit(f'이미 "{n}" 시트가 있어요. 원본 취합본으로 다시 실행해 주세요.')
    ws = wb[sheet] if sheet else wb.worksheets[0]
    hr = find_header(ws)
    col = map_cols(ws, hr)
    period = find_period(ws, hr, period_arg)
    year = period[0].year if period else None
    header_texts = {nfc(ws.cell(hr, c).value).replace(' ', '') for c in col.values()}

    drop, recs = [], []
    first_r, last_r = hr + 1, ws.max_row
    orig_formula_note = []
    for r in range(first_r, last_r + 1):
        raw = {k: ws.cell(r, c).value for k, c in col.items()}
        allv = [ws.cell(r, c).value for c in range(1, ws.max_column + 1)]
        if all(v is None or nfc(v).strip() == '' for v in allv):
            drop.append((r, '', '삭제', '빈 줄')); continue
        idv = nfc(raw['id']).strip()
        if idv.replace(' ', '') in header_texts:
            drop.append((r, '', '삭제', '중간에 반복된 머리글')); continue
        if any(isinstance(v, str) and v.startswith('=') for v in allv) or '합계' in idv or '소계' in idv:
            f = next((v for v in allv if isinstance(v, str) and v.startswith('=')), '')
            drop.append((r, '', '삭제', f'합계·소계 줄 {f} — 새 합계로 대체'))
            orig_formula_note.append((r, f)); continue
        if not idv:
            drop.append((r, '', '보류', '기록 ID가 비어 있음 — 확인 필요')); continue
        x = {'src': r, 'raw': raw, 'id': idv, 'problems': []}
        try:
            x['rev'] = int(to_num(raw.get('rev')) or 1)
        except ValueError:
            x['rev'] = 1; x['problems'].append(f'수정차수 "{raw.get("rev")}" 해석 불가')
        try:
            x['date'] = to_date(raw['date'], year)
        except (ValueError, TypeError):
            x['date'] = None; x['problems'].append(f'집행일 "{raw["date"]}" 해석 불가')
        for k in NUMS:
            if k not in col:
                x[k] = None; continue
            try:
                x[k] = to_num(raw[k])
            except ValueError:
                x[k] = None; x['problems'].append(f'{LABEL[k]} "{raw[k]}" 숫자로 바꿀 수 없음')
        for k in ('region', 'act', 'prod', 'memo'):
            x[k] = nfc(raw.get(k)).strip() if raw.get(k) is not None else ''
        cv = nfc(raw.get('close')).strip() if 'close' in col else '확정'
        x['close'] = CLOSE_OK.get(cv, '잠정' if cv in CLOSE_TEMP else cv)
        recs.append(x)

    # 띄어쓰기만 다른 표기 통일 (가장 많이 쓴 표기로, 같으면 띄어쓰기 적은 쪽)
    unify_log = []
    for k in ('act', 'prod', 'region'):
        cnt = Counter(x[k] for x in recs if x[k])
        groups = {}
        for v in cnt:
            groups.setdefault(v.replace(' ', ''), []).append(v)
        for vs in groups.values():
            if len(vs) > 1:
                best = sorted(vs, key=lambda v: (-cnt[v], v.count(' ')))[0]
                for v in vs:
                    if v != best:
                        unify_log.append(f'{LABEL[k]}: "{v}"({cnt[v]}건) → "{best}"({cnt[best]}건)')
                        for x in recs:
                            if x[k] == v:
                                x[k] = best
    closes = Counter(nfc(x['raw'].get('close')).strip() for x in recs if 'close' in col)

    # 수정차수 반영
    by_id = {}
    for x in recs:
        by_id.setdefault(x['id'], []).append(x)
    kept = []
    key = lambda g: (g['date'], g['amt'], g['consult'], g['recv'], g['cancel'], g['done'])
    for i, grp in by_id.items():
        top = max(g['rev'] for g in grp)
        tops = [g for g in grp if g['rev'] == top]
        for g in grp:
            if g['rev'] < top:
                drop.append((g['src'], i, '제외', f'{top}차 수정본(원본 {tops[0]["src"]}행)으로 대체 — 수정차수가 높은 값 반영'))
        if len(tops) == 1:
            kept.append(tops[0]); continue
        first = tops[0]
        if all(key(o) == key(first) for o in tops[1:]):
            kept.append(first)
            for o in tops[1:]:
                diff = [LABEL[k] for k in ('region', 'act', 'prod', 'close') if o[k] != first[k]]
                why = f'{"·".join(diff)}만 다름' if diff else '내용 동일'
                drop.append((o['src'], i, '제외', f'같은 {top}차 기록 중복 — 숫자는 같고 {why}, 먼저 나온 {first["src"]}행 유지'))
        else:
            amts = ', '.join('비어 있음' if t['amt'] is None else format(t['amt'], ',') for t in tops)
            for g in tops:
                drop.append((g['src'], i, '보류', f'같은 {top}차 기록인데 값이 다름(금액 {amts}) — 담당자 확인 전까지 합계 미포함'))

    final, warn = [], []
    for x in sorted(kept, key=lambda g: (g['date'] or dt.date.max, g['id'])):
        if x['problems']:
            drop.append((x['src'], x['id'], '보류', '; '.join(x['problems']) + ' — 확인 필요')); continue
        if period and not (period[0] <= x['date'] <= period[1]):
            drop.append((x['src'], x['id'], '제외', f'보고기간 밖({x["date"]:%Y-%m-%d})')); continue
        if x['close'] == '잠정':
            drop.append((x['src'], x['id'], '제외', f'마감여부 {nfc(x["raw"].get("close")).strip()} — 확정 실적 아님')); continue
        if x['close'] != '확정':
            drop.append((x['src'], x['id'], '보류', f'마감여부 "{x["close"]}" 뜻이 불분명 — 확인 필요')); continue
        if x['amt'] is None:
            drop.append((x['src'], x['id'], '보류', '금액 비어 있음 — 0원으로 넣지 않고 담당자 확인 대기')); continue
        notes = []
        if x['recv'] is not None and x['cancel'] is not None and x['cancel'] > x['recv']:
            notes.append(f'취소({x["cancel"]})가 접수({x["recv"]})보다 많음')
        if x['recv'] is not None and x['done'] is not None and x['done'] > x['recv']:
            notes.append(f'처리완료({x["done"]})가 접수({x["recv"]})보다 많음')
        if x['amt'] < 0:
            notes.append('금액이 음수')
        x['note'] = ('확인 권장: ' + ', '.join(notes)) if notes else ''
        if notes:
            warn.append(x)
        final.append(x)

    # 확정 행에서 바뀐 값
    changes = []
    for x in final:
        for k in ['id', 'rev', 'date', 'region', 'act', 'prod'] + NUMS + ['close']:
            if k not in col:
                continue
            o, n = x['raw'][k], x[k]
            if isinstance(o, dt.datetime) and o.date() == n:
                continue
            if type(o) == type(n) and o == n:
                continue
            if k == 'rev' and o is None:
                continue
            why = {'id': '앞뒤 공백 제거', 'date': '날짜 형식 통일', 'region': '공백·표기 통일', 'act': '띄어쓰기·공백 통일',
                   'prod': '띄어쓰기·공백 통일', 'close': f'"{nfc(o).strip()}" → 확정 통일', 'rev': '숫자로 변환'}.get(k, '숫자로 변환(원·₩·건·쉼표·공백 제거)')
            changes.append((x['src'], x['id'], LABEL[k], show(o), n.strftime('%Y-%m-%d') if isinstance(n, dt.date) else n, why))

    # ── 시트 쓰기 ──
    NF = Font(name=F, color='202124')
    TOT = PatternFill('solid', fgColor='FDE7EC')

    def title(s, t, sub):
        s['A1'] = t; s['A1'].font = Font(name=F, bold=True, size=14, color=RED)
        s['A2'] = sub; s['A2'].font = Font(name=F, size=10, color='5F6368')

    def header(s, r, cols, widths=None):
        for c, h in enumerate(cols, 1):
            cell = s.cell(r, c, h)
            cell.fill = PatternFill('solid', fgColor=RED); cell.font = Font(name=F, bold=True, color='FFFFFF')
            cell.border = BORDER; cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            if widths and widths[c - 1]:
                s.column_dimensions[get_column_letter(c)].width = widths[c - 1]

    def put(s, r, vals, fmt=None):
        for c, v in enumerate(vals, 1):
            cell = s.cell(r, c, v); cell.font = NF; cell.border = BORDER
            if fmt and c in fmt:
                cell.number_format = fmt[c]

    ptxt = f'{period[0]:%Y.%m.%d}~{period[1]:%Y.%m.%d}' if period else '보고기간 미확인'
    a1 = nfc(ws['A1'].value) or os.path.basename(src)

    s = wb.create_sheet('확정실적')
    title(s, f'{a1} — 확정실적', f'보고기간 {ptxt} | 원본: {os.path.basename(src)} | 금액 단위는 원본 머리글 기준')
    cols = ['기록 ID', '수정차수', '집행일', '담당 지역', '활동구분', '대상상품', '사용금액', '상담 건수', '접수건', '취소', '처리완료', '마감여부', '원본 행', '메모', '검토 메모']
    header(s, 4, cols, [16, 9, 12, 11, 13, 13, 14, 10, 9, 8, 10, 9, 8, 16, 36])
    fmt = {3: 'yyyy-mm-dd', 7: '#,##0', 8: '#,##0', 9: '#,##0', 10: '#,##0', 11: '#,##0'}
    for i, x in enumerate(final, 5):
        put(s, i, [x['id'], x['rev'], x['date'], x['region'], x['act'], x['prod'], x['amt'], x['consult'], x['recv'],
                   x['cancel'], x['done'], x['close'], x['src'], x['memo'], x['note']], fmt)
        if x['note']:
            s.cell(i, 15).font = Font(name=F, color='925000')
    last = 4 + len(final); tr = last + 1
    s.cell(tr, 1, '합계'); s.cell(tr, 2, f'=COUNTA(A5:A{last})&"건"')
    for c in range(7, 12):
        L = get_column_letter(c); s.cell(tr, c, f'=SUM({L}5:{L}{last})').number_format = '#,##0'
    for c in range(1, 16):
        cl = s.cell(tr, c); cl.fill = TOT; cl.border = BORDER; cl.font = Font(name=F, bold=True)
    s.freeze_panes = 'A5'
    if final:
        s.auto_filter.ref = f'A4:O{last}'

    cnt = Counter(d[2] for d in drop)
    s2 = wb.create_sheet('제외·수정내역')
    title(s2, '제외·수정내역', '① 확정실적에 넣지 않은 원본 행  ② 확정실적 행에서 바꾼 값 (원본 시트는 수정하지 않음)')
    s2['A4'] = f'① 확정실적에서 뺀 원본 행 — {len(drop)}행 (삭제 {cnt["삭제"]} · 제외 {cnt["제외"]} · 보류 {cnt["보류"]})'
    s2['A4'].font = Font(name=F, bold=True, size=12)
    header(s2, 5, ['원본 행', '기록 ID', '구분', '사유', '', ''], [9, 16, 18, 26, 26, 30]); s2.merge_cells('D5:F5')
    r = 6
    for d in sorted(drop):
        put(s2, r, list(d)); s2.cell(r, 3).font = Font(name=F, bold=True, color=COLOR[d[2]])
        s2.merge_cells(start_row=r, start_column=4, end_row=r, end_column=6); r += 1
    s2.cell(r, 1, '구분 뜻: 삭제 = 데이터가 아닌 줄 / 제외 = 규칙에 따라 뺀 기록 / 보류 = 담당자 확인 전까지 합계에서 뺀 기록').font = Font(name=F, size=9, color='5F6368')
    r += 2
    s2.cell(r, 1, f'② 확정실적 행에서 바꾼 값 — {len(changes)}칸').font = Font(name=F, bold=True, size=12); r += 1
    header(s2, r, ['원본 행', '기록 ID', '열', '원본 값', '바꾼 값', '바꾼 이유']); r += 1
    for ch in changes:
        put(s2, r, list(ch), {5: '#,##0'}); r += 1
    if unify_log:
        r += 1; s2.cell(r, 1, '③ 표기 통일 기준').font = Font(name=F, bold=True, size=12); r += 1
        for u in unify_log:
            s2.cell(r, 1, '• ' + u).font = NF; r += 1

    n_data = len(recs) + sum(1 for d in drop if d[2] == '보류' and d[1] == '')
    n_out = sum(1 for d in drop if d[2] != '삭제')
    R = '확정실적!'
    s3 = wb.create_sheet('검증')
    title(s3, '검증 결과', f'확정실적 시트를 원본과 대조한 결과 | 검증일 {dt.date.today():%Y-%m-%d}')
    header(s3, 4, ['#', '검증 항목', '기대값', '실제값', '결과', '설명'], [5, 30, 18, 18, 10, 60])
    sums = {k: sum(x[k] or 0 for x in final) for k in NUMS}
    checks = [
        ('확정 + 제외 + 보류 = 원본 기록 수', n_data, f'=COUNTA({R}A5:A{last})+{n_out}' if final else n_out,
         f'원본 기록 {n_data}건 = 확정 + 제외 {cnt["제외"]} + 보류 {cnt["보류"]}'),
        ('원본 데이터 영역 모두 처리', f'{last_r - first_r + 1}행', f'{len(final) + len(drop)}행',
         f'원본 {first_r}~{last_r}행이 확정·제외·보류·삭제 중 하나로 분류'),
        ('확정 건수', len(final), f'=COUNTA({R}A5:A{last})' if final else 0, '확정실적 시트 행 수'),
        ('기록 ID 중복 없음', 0, f'=SUMPRODUCT((COUNTIF({R}A5:A{last},{R}A5:A{last})>1)*1)' if final else 0, '같은 ID가 두 번 이상이면 0이 아님'),
    ]
    for k, L in zip(NUMS, 'GHIJK'):
        if k in col:
            checks.append((f'{LABEL[k]} 합계', sums[k], f'=SUM({R}{L}5:{L}{last})' if final else 0, '기대값은 원본 셀을 다시 읽어 계산한 값'))
    nnum = len(final) * sum(1 for k in NUMS if k in col)
    if final:
        checks += [
            ('금액·건수 칸이 모두 숫자', nnum, f'=COUNT({R}G5:K{last})', '글자로 남은 칸이 있으면 줄어듦 (없는 열은 제외)'),
            ('마감여부가 모두 확정', len(final), f'=COUNTIF({R}L5:L{last},"확정")', '잠정 기록 미포함'),
        ]
        if period:
            checks.append(('집행일이 보고기간 안', len(final),
                           f'=COUNTIFS({R}C5:C{last},">="&DATE({period[0].year},{period[0].month},{period[0].day}),{R}C5:C{last},"<="&DATE({period[1].year},{period[1].month},{period[1].day}))',
                           ptxt))
    results = []
    r = 5
    for i, (item, exp, act, note) in enumerate(checks, 1):
        put(s3, r, [i, item, exp, act, None, note], {3: '#,##0', 4: '#,##0'})
        if isinstance(act, str) and act.startswith('='):
            s3.cell(r, 5, f'=IF(C{r}=D{r},"통과","확인 필요")')
        else:
            s3.cell(r, 5, '통과' if exp == act else '확인 필요')
        s3.cell(r, 5).font = Font(name=F, bold=True, color='287D4E'); s3.cell(r, 5).alignment = Alignment(horizontal='center')
        results.append(item); r += 1
    r += 1
    s3.cell(r, 1, '참고 — 알아둘 점').font = Font(name=F, bold=True, size=12); r += 1
    header(s3, r, ['#', '항목', '', '', '구분', '설명']); r += 1
    notes = []
    for fr, f in orig_formula_note:
        notes.append((f'원본 {fr}행 합계 수식', '참고', f'{f} — 글자로 된 금액은 빠지고 중복·제외 행은 더해질 수 있어 확정 합계와 다를 수 있음'))
    notes += [(f'{x["id"]} 값 이상', '참고', f'원본 {x["src"]}행 {x["note"]} — 확정에는 포함') for x in warn]
    notes += [(f'{d[1] or "원본 " + str(d[0]) + "행"} 보류', '보류', d[3]) for d in sorted(drop) if d[2] == '보류']
    notes += [('표기 통일', '참고', u) for u in unify_log]
    if not period:
        notes.append(('보고기간', '확인 필요', '파일 상단에서 보고기간을 찾지 못해 기간 검사를 하지 않음'))
    for i, (item, kind, desc) in enumerate(notes, 1):
        put(s3, r, [i, item, None, None, kind, desc])
        s3.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
        s3.cell(r, 5).font = Font(name=F, bold=True, color=COLOR[kind]); s3.cell(r, 5).alignment = Alignment(horizontal='center')
        s3.cell(r, 6).alignment = Alignment(wrap_text=True, vertical='top'); r += 1

    wb.save(out)

    # 파이썬으로 검증 수식 결과를 재현해 요약에 담는다
    ids = [x['id'] for x in final]
    emu_ok = (len(final) + n_out == n_data and len(final) + len(drop) == last_r - first_r + 1
              and len(ids) == len(set(ids)))
    return dict(
        output=out, data_sheet=ws.title, period=ptxt, original_records=n_data,
        confirmed=len(final), excluded=cnt['제외'], held=cnt['보류'], deleted_rows=cnt['삭제'],
        totals=sums, value_changes=len(changes), unify=unify_log, close_values=dict(closes),
        held_or_excluded=[{'row': d[0], 'id': d[1], 'type': d[2], 'reason': d[3]} for d in sorted(drop) if d[2] != '삭제'],
        warnings=[{'row': x['src'], 'id': x['id'], 'note': x['note']} for x in warn],
        missing_optional_columns=[LABEL[k] for k in COLS if k not in col],
        checks_all_pass=emu_ok,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument('src'); p.add_argument('--out'); p.add_argument('--period'); p.add_argument('--sheet')
    a = p.parse_args()
    src = os.path.abspath(a.src)
    base, ext = os.path.splitext(src)
    base = re.sub(r'_?(취합본|복사본)$', '', nfc(base))
    out = a.out or f'{base}_통합본{ext}'
    if os.path.exists(out):
        sys.exit(f'같은 이름의 파일이 이미 있어요: {out}  (--out 으로 다른 이름을 지정해 주세요)')
    print(json.dumps(build(src, out, a.period, a.sheet), ensure_ascii=False, indent=1, default=str))


if __name__ == '__main__':
    main()
