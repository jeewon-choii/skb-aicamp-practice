// 7월 고객 캠페인 CEO 보고 PPT 생성 스크립트 (교육용 실습 자료)
// 사용: node build.js <원본폴더> <출력파일>
const path = require("path");
const pptxgen = require("pptxgenjs");

const SRC_DIR = process.argv[2];
const OUT = process.argv[3];

const FONT = "Apple SD Gothic Neo";
const RED = "EA002C", ORANGE = "F47725", TXT = "202124", TXT2 = "5F6368";
const BG = "FFFFFF", BG2 = "F7F8FA", LINE = "E5E7EB";
const GOOD = "287D4E", BAD = "B42318";
const RED_TINT = "FDECEF";

const SRC_NOTE = "출처: 운영기획팀 「7월 고객 캠페인 월간보고」(2026.08.04) · 교육용 실습 자료(가상 데이터)";
const CHECK_NOTE = "* 담당자 확인 전 수치(원본 [확인] 표시)";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.title = "7월 고객 캠페인 결과 — CEO 보고";
pres.author = "SKB AI Camp";
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };

const W = 13.333, MX = 0.6, CW = W - 2 * MX;

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: BG },
  objects: [
    { text: { text: "SKB AI Camp · 교육용 실습 자료", options: { x: MX, y: 7.0, w: 6, h: 0.3, fontFace: FONT, fontSize: 10, color: TXT2, margin: 0 } } },
  ],
  slideNumber: { x: W - MX - 0.6, y: 7.0, w: 0.6, h: 0.3, fontFace: FONT, fontSize: 10, color: TXT2, align: "right" },
});

function title(slide, text) {
  slide.addText(text, {
    x: MX, y: 0.4, w: CW, h: 1.0, fontFace: FONT, fontSize: 32, bold: true, color: TXT,
    valign: "top", margin: 0, isTextBox: true, objectName: "Title",
  });
}
function note(slide, text, y = 6.55) {
  slide.addText(text, { x: MX, y, w: CW, h: 0.35, fontFace: FONT, fontSize: 11, color: TXT2, margin: 0, isTextBox: true, objectName: "Source" });
}

// ---------- 1. 표지 ----------
{
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("SK브로드밴드 · SKB AI Camp", { x: MX, y: 1.5, w: 7, h: 0.5, fontFace: FONT, fontSize: 20, bold: true, color: RED, margin: 0, isTextBox: true });
  s.addText("7월 고객 캠페인 결과", { x: MX, y: 2.2, w: 7.2, h: 1.1, fontFace: FONT, fontSize: 48, bold: true, color: TXT, margin: 0, isTextBox: true });
  s.addText("CEO 보고 · 보고(인지) 사항", { x: MX, y: 3.35, w: 7.2, h: 0.6, fontFace: FONT, fontSize: 26, color: TXT2, margin: 0, isTextBox: true });
  s.addText([
    { text: "보고 범위: 7월 1일~31일, 8월 3일 18:00 마감 확정분", options: { breakLine: true } },
    { text: "5개 지역 · 3개 활동(온라인안내·현장상담·기존고객안내)" },
  ], { x: MX, y: 4.4, w: 7.2, h: 0.9, fontFace: FONT, fontSize: 16, color: TXT2, margin: 0, paraSpaceAfter: 4, isTextBox: true });
  // 오른쪽 핵심 숫자 카드
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 8.4, y: 1.5, w: 4.3, h: 3.8, fill: { color: BG2 }, line: { color: LINE, width: 1 }, rectRadius: 0.15, objectName: "KeyCard" });
  s.addText("7월 유효신청", { x: 8.7, y: 1.9, w: 3.7, h: 0.5, fontFace: FONT, fontSize: 20, color: TXT2, margin: 0, isTextBox: true });
  s.addText("7,520건", { x: 8.7, y: 2.45, w: 3.7, h: 1.1, fontFace: FONT, fontSize: 60, bold: true, color: RED, margin: 0, isTextBox: true });
  s.addText([
    { text: "목표 7,950건의 94.6%*", options: { breakLine: true } },
    { text: "예산 86.6% 집행" },
  ], { x: 8.7, y: 3.75, w: 3.7, h: 1.2, fontFace: FONT, fontSize: 20, color: TXT, margin: 0, paraSpaceAfter: 6, isTextBox: true });
  s.addText([
    { text: SRC_NOTE, options: { breakLine: true } },
    { text: CHECK_NOTE },
  ], { x: MX, y: 6.3, w: CW, h: 0.7, fontFace: FONT, fontSize: 11, color: TXT2, margin: 0, isTextBox: true });
}

// ---------- 2. 한 줄 결론 + 핵심 숫자 ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "7월 유효신청 7,520건(목표의 94.6%*), 예산 86.6% 집행 — 영남 비용 점검 필요*");
  const cards = [
    { label: "유효신청", value: "7,520건", sub: "목표 7,950건 대비\n▼ 430건 (94.6%)*", color: RED },
    { label: "집행액", value: "6,060만 원", sub: "승인예산 7,000만 원\n집행률 86.6%", color: ORANGE },
    { label: "신청전환율", value: "21.4%", sub: "상담 35,150건 기준", color: TXT },
    { label: "건당비용(전체)", value: "8,059원*", sub: "6,060만 원 ÷ 7,520건", color: TXT },
  ];
  const gap = 0.3, cw = (CW - gap * 3) / 4, cy = 1.75, ch = 2.6;
  cards.forEach((c, i) => {
    const x = MX + i * (cw + gap);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: cy, w: cw, h: ch, fill: { color: BG2 }, line: { color: LINE, width: 1 }, rectRadius: 0.12, objectName: `StatCard${i + 1}` });
    s.addText(c.label, { x: x + 0.25, y: cy + 0.25, w: cw - 0.5, h: 0.4, fontFace: FONT, fontSize: 18, color: TXT2, margin: 0, isTextBox: true });
    s.addText(c.value, { x: x + 0.25, y: cy + 0.7, w: cw - 0.5, h: 0.8, fontFace: FONT, fontSize: 36, bold: true, color: c.color, margin: 0, isTextBox: true });
    s.addText(c.sub, { x: x + 0.25, y: cy + 1.6, w: cw - 0.5, h: 0.85, fontFace: FONT, fontSize: 16, color: TXT, margin: 0, valign: "top", isTextBox: true });
  });
  // 지역 포인트 2개
  const py = 4.7, ph = 1.5, pw = (CW - gap) / 2;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: py, w: pw, h: ph, fill: { color: BG2 }, line: { color: LINE, width: 1 }, rectRadius: 0.12, objectName: "PointGood" });
  s.addText([
    { text: "▲ 충청 — 전환율 25.2%", options: { bold: true, color: GOOD, fontSize: 22, breakLine: true } },
    { text: "5개 지역 중 가장 높음 → 상담 방식 확산 검토", options: { color: TXT, fontSize: 16 } },
  ], { x: MX + 0.3, y: py + 0.2, w: pw - 0.6, h: ph - 0.4, fontFace: FONT, margin: 0, valign: "middle", paraSpaceAfter: 6, isTextBox: true });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX + pw + gap, y: py, w: pw, h: ph, fill: { color: RED_TINT }, line: { color: RED, width: 1.5 }, rectRadius: 0.12, objectName: "PointBad" });
  s.addText([
    { text: "● 영남 — 건당비용 10,395원", options: { bold: true, color: RED, fontSize: 22, breakLine: true } },
    { text: "5개 지역 중 가장 높음 → 채널 구성·비용 점검", options: { color: TXT, fontSize: 16 } },
  ], { x: MX + pw + gap + 0.3, y: py + 0.2, w: pw - 0.6, h: ph - 0.4, fontFace: FONT, margin: 0, valign: "middle", paraSpaceAfter: 6, isTextBox: true });
  note(s, SRC_NOTE + "   " + CHECK_NOTE);
}

// ---------- 3. 도식 ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "8월 검토 3가지 — 영남 비용 점검에 주목");
  const iw = 11.6, ih = iw * 738 / 1600;
  s.addImage({
    path: path.join(SRC_DIR, "도식.png"), x: (W - iw) / 2, y: 1.4, w: iw, h: ih,
    altText: "7월 유효신청 7,520건(목표 7,950건의 94.6%, 예산 86.6% 집행)에서 8월 검토 3가지로 이어지는 도식: A. 충청 방식 확산(전환율 25.2%, 최고), B. 영남 비용 점검(건당비용 10,395원, 최고, 주목), C. 8월 신규 비용(별도 승인 후 집행, 금액 미정)",
    objectName: "Diagram",
  });
}

// ---------- 4. 지역별 ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "충청은 전환율 25.2%로 최고, 영남은 건당비용 10,395원으로 최고");
  const H = { bold: true, color: TXT, fill: { color: BG2 }, align: "center", valign: "middle" };
  const c = (t, o = {}) => ({ text: t, options: Object.assign({ align: "right", valign: "middle", color: TXT }, o) });
  const l = (t, o = {}) => ({ text: t, options: Object.assign({ align: "left", valign: "middle", color: TXT, bold: true }, o) });
  const rows = [
    ["지역", "집행액", "유효신청", "목표 달성률*", "전환율", "건당비용"].map(t => ({ text: t, options: H })),
    [l("수도권"), c("1,650만 원"), c("2,080건"), c("94.5%"), c("19.8%"), c("7,933원")],
    [l("충청"), c("1,020만 원"), c("1,610건"), c("97.6%"), c("▲ 25.2% 최고", { bold: true, color: GOOD }), c("6,335원")],
    [l("호남"), c("970만 원"), c("1,300건"), c("89.7%"), c("22.2%"), c("7,462원")],
    [l("영남", { fill: { color: RED_TINT } }), c("1,580만 원", { fill: { color: RED_TINT } }), c("1,520건", { fill: { color: RED_TINT } }), c("98.1%", { fill: { color: RED_TINT } }), c("18.8%", { fill: { color: RED_TINT } }), c("● 10,395원 최고", { bold: true, color: RED, fill: { color: RED_TINT } })],
    [l("강원·제주"), c("840만 원"), c("1,010건"), c("91.8%"), c("23.5%"), c("8,317원")],
    [l("합계", { fill: { color: BG2 } }), ...["6,060만 원", "7,520건", "94.6%", "21.4%", "8,059원"].map(t => c(t, { bold: true, fill: { color: BG2 } }))],
  ];
  s.addTable(rows, {
    x: MX, y: 1.6, w: CW, colW: [1.9, 2.1, 1.8, 2.0, 2.2, 2.133],
    rowH: 0.6, fontFace: FONT, fontSize: 18, border: { type: "solid", pt: 1, color: LINE }, margin: [0, 0.15, 0, 0.15],
    objectName: "RegionTable",
  });
  s.addText([
    { text: "집행액은 부가세 제외 · 유효신청 = 신청 − 취소 · 합계 비율은 지역 합계로 계산(단순 평균 아님)", options: { breakLine: true } },
    { text: SRC_NOTE + "   " + CHECK_NOTE },
  ], { x: MX, y: 6.05, w: CW, h: 0.8, fontFace: FONT, fontSize: 11, color: TXT2, margin: 0, paraSpaceAfter: 4, isTextBox: true });
}

// ---------- 5. 결정·다음 할 일 ----------
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "지금 결정할 사항은 없습니다 — 8월 신규 비용은 별도 승인 요청 예정");
  // 왼쪽: 결정 사항
  const ly = 1.75, lh = 4.4, lw = 4.0;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: ly, w: lw, h: lh, fill: { color: BG2 }, line: { color: LINE, width: 1 }, rectRadius: 0.12, objectName: "DecisionCard" });
  s.addText("CEO 결정 사항", { x: MX + 0.3, y: ly + 0.3, w: lw - 0.6, h: 0.45, fontFace: FONT, fontSize: 18, color: TXT2, margin: 0, isTextBox: true });
  s.addText("없음", { x: MX + 0.3, y: ly + 0.85, w: lw - 0.6, h: 1.0, fontFace: FONT, fontSize: 54, bold: true, color: TXT, margin: 0, isTextBox: true });
  s.addText([
    { text: "이번 보고는 보고(인지) 사항입니다.", options: { breakLine: true } },
    { text: "8월 신규 활동·콘텐츠 제작비는 별도로 승인을 요청할 예정입니다(금액 미정*)." },
  ], { x: MX + 0.3, y: ly + 2.0, w: lw - 0.6, h: 2.2, fontFace: FONT, fontSize: 16, color: TXT, margin: 0, valign: "top", paraSpaceAfter: 8, isTextBox: true });

  // 오른쪽: 다음 할 일 3가지
  const rx = MX + lw + 0.4, rw = CW - lw - 0.4;
  s.addText("다음 할 일", { x: rx, y: ly, w: rw, h: 0.45, fontFace: FONT, fontSize: 20, bold: true, color: TXT, margin: 0, isTextBox: true });
  const items = [
    { k: "A", t: "충청 상담 방식", d: "다른 지역에 적용할 수 있는지 확인", hi: false },
    { k: "B", t: "영남 채널 구성·비용 점검 ← 주목", d: "온라인·현장·기존고객 안내 구성과 건당비용 점검", hi: true },
    { k: "C", t: "8월 신규 활동·콘텐츠 제작비", d: "별도 승인 후 집행", hi: false },
  ];
  const ih = 1.1, ig = 0.25;
  items.forEach((it, i) => {
    const y = ly + 0.65 + i * (ih + ig);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: rx, y, w: rw, h: ih, fill: { color: it.hi ? RED_TINT : BG2 }, line: { color: it.hi ? RED : LINE, width: it.hi ? 1.5 : 1 }, rectRadius: 0.1, objectName: `Next${it.k}` });
    s.addShape(pres.shapes.OVAL, { x: rx + 0.25, y: y + (ih - 0.6) / 2, w: 0.6, h: 0.6, fill: { color: it.hi ? RED : TXT2 }, line: { type: "none" }, objectName: `NextBadge${it.k}` });
    s.addText(it.k, { x: rx + 0.25, y: y + (ih - 0.6) / 2, w: 0.6, h: 0.6, fontFace: FONT, fontSize: 20, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText([
      { text: it.t, options: { bold: true, fontSize: 20, color: it.hi ? RED : TXT, breakLine: true } },
      { text: it.d, options: { fontSize: 16, color: TXT } },
    ], { x: rx + 1.1, y: y + 0.1, w: rw - 1.3, h: ih - 0.2, fontFace: FONT, margin: 0, valign: "middle", paraSpaceAfter: 2, isTextBox: true });
  });
  note(s, SRC_NOTE + "   * 원본 [확인] 표시 6건은 담당자 확인 전");
}

pres.writeFile({ fileName: OUT }).then(f => console.log("saved:", f));
