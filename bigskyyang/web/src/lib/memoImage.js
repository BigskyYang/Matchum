// 약사 상담용 메모 이미지: 휴대폰에서 canvas로 바로 그린다 (서버로 보내지 않는다)
//   담는 것: 성별·나이대, 결과에서 '부족하기 쉬워요'로 나온 영양소, 먹고 있는 제품, 고민 중인 제품,
//           함께 먹을 때 하루 합계와 상한, 물어보고 싶은 것(직접 적은 글), 만든 날짜
//   폭 1080px, 높이는 내용만큼. 글이 길면 줄을 바꾼다
const W = 1080
const PAD = 72
const C = { bg: '#fff8f1', card: '#ffffff', ink: '#3d3333', soft: '#6b5d59', faint: '#766864', over: '#a8425a', line: '#ece4de', accent: '#e2647c' }
const SANS = "'Pretendard Variable', Pretendard, 'Apple SD Gothic Neo', sans-serif"
const DISPLAY = "'Jua', 'Pretendard Variable', sans-serif"

// 글자 단위로 폭에 맞춰 줄을 나눈다 (한국어는 띄어쓰기 없이 길어지는 제품명이 많아 글자 단위)
export function wrapText(measure, text, width) {
  const lines = []
  let line = ''
  for (const ch of text) {
    if (line && measure(line + ch) > width) {
      lines.push(line.trimEnd())
      line = ch === ' ' ? '' : ch
    } else line += ch
  }
  if (line) lines.push(line)
  return lines
}

// memo: { dateLabel, who, watch: [이름], mine: [{ name, maker? }], picks: [{ name, maker }], manualCount, totals, question }
export async function drawMemoImage(memo, { serviceName = 'NBTI 유형 검사' } = {}) {
  await Promise.all([document.fonts.load(`64px ${DISPLAY}`), document.fonts.load(`700 36px ${SANS}`)]).catch(() => {})
  const canvas = document.createElement('canvas')
  canvas.width = W
  canvas.height = 4000
  const ctx = canvas.getContext('2d')
  ctx.textBaseline = 'top'
  const inner = W - PAD * 2 - 80
  const ops = []
  let y = 0
  const text = (str, { size = 34, weight = 400, color = C.ink, font = SANS, gap = 12, indent = 0, lineH = 1.4 } = {}) => {
    ctx.font = `${weight} ${size}px ${font}`
    for (const line of wrapText((t) => ctx.measureText(t).width, str, inner - indent)) {
      const at = y
      ops.push(() => {
        ctx.font = `${weight} ${size}px ${font}`
        ctx.fillStyle = color
        ctx.fillText(line, PAD + 40 + indent, at)
      })
      y += size * lineH
    }
    y += gap
  }
  const heading = (str) => {
    y += 28
    text(str, { size: 38, weight: 700, color: C.ink, gap: 16 })
  }
  const bullet = (str, sub) => {
    const at = y
    ops.push(() => {
      ctx.fillStyle = C.accent
      ctx.beginPath()
      ctx.arc(PAD + 52, at + 22, 7, 0, Math.PI * 2)
      ctx.fill()
    })
    text(str, { size: 34, weight: 600, indent: 32, gap: sub ? 2 : 12 })
    if (sub) text(sub, { size: 28, color: C.soft, indent: 32, gap: 14 })
  }

  y = PAD + 40
  text('약사 상담 메모', { size: 64, font: DISPLAY, gap: 8 })
  text(`${memo.who} · ${memo.dateLabel}`, { size: 30, color: C.soft, gap: 8 })

  if (memo.watch.length) {
    heading('결과에서 부족하기 쉽다고 나온 영양소')
    text(memo.watch.join(' · '), { size: 34 })
  }
  heading('지금 먹고 있는 건강기능식품')
  if (memo.mine.length) for (const p of memo.mine) bullet(p.name, p.maker ?? '목록에 없어 이름만 적었어요')
  else text('없어요', { color: C.soft })
  if (memo.picks.length) {
    heading('먹어 볼까 고민 중인 제품')
    for (const p of memo.picks) bullet(p.name, p.maker)
  }
  if (memo.totals.length) {
    heading('함께 먹으면 하루에 (상한섭취량)')
    for (const t of memo.totals) {
      const row = `${t.label}  ${t.total.toLocaleString('ko-KR')} ${t.unit}${t.ul ? ` (상한 ${t.ul.toLocaleString('ko-KR')} ${t.unit})` : ''}${t.over ? '  넘어요' : ''}`
      text(row, { size: 32, weight: t.over ? 700 : 400, color: t.over ? C.over : C.ink, gap: 6 })
    }
    if (memo.manualCount) text(`이름만 적은 제품 ${memo.manualCount}개는 함량을 몰라 합계에 넣지 않았어요.`, { size: 26, color: C.faint, gap: 6 })
  }
  if (memo.question) {
    heading('물어보고 싶은 것')
    text(memo.question, { size: 34 })
  }
  y += 24
  text(`${serviceName} 결과를 바탕으로 만든 참고용 메모예요. 진단이나 처방이 아니에요.`, { size: 26, color: C.faint, gap: 0 })
  const cardBottom = y + 40

  const H = Math.ceil(cardBottom + PAD)
  const out = document.createElement('canvas')
  out.width = W
  out.height = H
  const o = out.getContext('2d')
  o.fillStyle = C.bg
  o.fillRect(0, 0, W, H)
  o.shadowColor = 'rgba(226, 100, 124, 0.14)'
  o.shadowBlur = 40
  o.shadowOffsetY = 12
  o.fillStyle = C.card
  o.beginPath()
  o.roundRect(PAD, PAD, W - PAD * 2, cardBottom - PAD, 48)
  o.fill()
  o.shadowColor = 'transparent'
  // 글은 큰 canvas에 그린 뒤 옮긴다 (높이를 미리 알 수 없어서)
  ctx.clearRect(0, 0, W, canvas.height)
  ops.forEach((op) => op())
  o.drawImage(canvas, 0, 0)
  return new Promise((resolve, reject) => out.toBlob((b) => (b ? resolve(b) : reject(new Error('이미지를 만들지 못했어요'))), 'image/png'))
}
