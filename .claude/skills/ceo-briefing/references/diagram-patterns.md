# 도식 고르는 법

보고본에는 도식 **1개**를 넣는다. 원문 내용이 그 모양일 때만 고른다. 억지로 맞추지 않는다.

| 원문 내용 | 도식 | `type` |
|---|---|---|
| 단계·절차·원인→결과 | 흐름도 | `flow` |
| 기존안 vs 개선안, 전월 vs 이번 달, A안 vs B안 | 전후 비교 | `compare` |
| 일정·마일스톤·추진 경과 | 일정표 | `timeline` |
| 조직·사업 구성, 큰 과제 아래 세부 과제 | 구조도 | `structure` |

숫자 추이(월별 실적 등)는 도식보다 **숫자 표**가 정확하다. 차트가 꼭 필요하면 `dataviz` 스킬을 따른다.

## 공통 규칙
- 상자 하나에 글 **15자 안팎** + 보조 설명 20자 안팎. 길면 줄인다.
- 상자는 3~6개. 넘으면 묶거나 숫자 표로 옮긴다.
- 강조(`highlight: true`)는 CEO가 볼 곳 **1~2개**에만. 강조는 빨간 테두리와 `●` 표시가 함께 나온다(색만으로 구분하지 않음).
- `note`에 출처·기준일을 적는다.

## JSON 형식

### flow — 흐름도
```json
{
  "type": "flow",
  "title": "신규 요금제 출시 절차",
  "items": [
    {"label": "상품 기획", "sub": "10월 완료"},
    {"label": "요금 인가", "sub": "11/20 예정", "highlight": true},
    {"label": "출시", "sub": "12월 초"}
  ],
  "note": "출처: 상품기획팀 컨플루언스 (2026-11-05)"
}
```

### compare — 전후 비교
```json
{
  "type": "compare",
  "title": "고객센터 응대 방식 개선",
  "left_title": "현재",
  "right_title": "개선안",
  "rows": [
    {"label": "응대 시간", "left": "평균 6분", "right": "평균 4분", "highlight": true},
    {"label": "필요 인력", "left": "120명", "right": "110명"}
  ],
  "note": "출처: CS혁신팀"
}
```

### timeline — 일정표
`done: true`는 완료(✓), 아니면 예정(○)으로 표시된다.
```json
{
  "type": "timeline",
  "title": "추진 일정",
  "items": [
    {"date": "10/15", "label": "착수", "done": true},
    {"date": "11/20", "label": "중간 점검", "highlight": true},
    {"date": "12/10", "label": "최종 보고"}
  ]
}
```

### structure — 구조도
```json
{
  "type": "structure",
  "title": "AI 전환 과제 구성",
  "root": {"label": "AI 전환", "sub": "총 3개 과제"},
  "items": [
    {"label": "고객 상담", "sub": "챗봇 도입"},
    {"label": "망 운영", "sub": "장애 예측", "highlight": true},
    {"label": "사내 업무", "sub": "문서 자동화"}
  ]
}
```

## 실행
```
$PY $SK/scripts/make_diagram.py --spec diagram.json --out 도식.png
```
만든 뒤 Read로 PNG를 열어 글자가 잘리지 않았는지 확인한다.
