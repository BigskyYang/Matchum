// 유형 결과 공유 이미지: 휴대폰에서 canvas로 바로 그린다 (서버·외부 라이브러리 없음)
//   story: 1080×1920 (인스타 스토리 등), square: 1080×1080 (카카오톡·피드)
//   담는 것: 대분류 색 칩, 유형 마스코트, 유형 이름, 해시태그, '조사 자료에서 성인 100명 중 약 N명', 서비스 이름과 주소 (개인 응답·건강 정보는 넣지 않는다)
//   색은 디자인 시안 A안(index.css 토큰)과 같은 값
export const FORMATS = {
  story: { width: 1080, height: 1920, label: '스토리 (9:16)' },
  square: { width: 1080, height: 1080, label: '정사각형 (1:1)' },
}

const C = {
  bg: '#fff8f1',
  card: '#ffffff',
  ink: '#3d3333',
  soft: '#6b5d59',
  tagBg: '#fce3e8',
  tagInk: '#a8425a',
  dotOff: '#ece4de',
}
// 대분류 4색: [점, 칩 바탕, 칩 글씨]
export const GROUP_COLORS = {
  N: ['#7db38a', '#e3f1e6', '#2f6b3d'],
  O: ['#6f93c7', '#e3ecf8', '#2f5a96'],
  S: ['#a28ae0', '#ece6fb', '#5a45a8'],
  A: ['#f2a23b', '#fdeed6', '#8a5300'],
}
const DISPLAY = "'Jua', 'Pretendard Variable', sans-serif"
const SANS = "'Pretendard Variable', Pretendard, 'Apple SD Gothic Neo', sans-serif"

// 글씨가 width 안에 들어가는 가장 큰 크기 (max부터 4px씩 줄인다)
export function fitFontSize(measure, text, width, max, min) {
  for (let size = max; size > min; size -= 4) if (measure(text, size) <= width) return size
  return min
}

// 해시태그를 maxWidth 안에서 줄 단위로 나눈다. measure(text) = 알약 하나의 폭
export function wrapPills(measure, items, maxWidth, gap) {
  const rows = []
  let row = []
  let w = 0
  for (const t of items) {
    const tw = measure(t)
    if (row.length && w + gap + tw > maxWidth) {
      rows.push(row)
      row = []
      w = 0
    }
    w += (row.length ? gap : 0) + tw
    row.push(t)
  }
  if (row.length) rows.push(row)
  return rows
}

function roundRect(ctx, x, y, w, h, r, fill) {
  ctx.beginPath()
  ctx.roundRect(x, y, w, h, r)
  ctx.fillStyle = fill
  ctx.fill()
}

const loadImage = (src) =>
  new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.onerror = reject
    img.src = src
  })

// r: lib/result.js buildTypeResult 결과. 반환: PNG Blob
export async function drawShareImage(r, format = 'story', { host = window.location.host, serviceName = 'NBTI 유형 검사' } = {}) {
  const { width: W, height: H } = FORMATS[format]
  const story = format === 'story'
  const [dot, chipBg, chipInk] = GROUP_COLORS[r.leafId[0]]
  await Promise.all([document.fonts.load(`96px ${DISPLAY}`), document.fonts.load(`700 40px ${SANS}`)]).catch(() => {})
  const mascot = await loadImage(`/mascot/type_${r.leafId}.png`).catch(() => null)

  const canvas = document.createElement('canvas')
  canvas.width = W
  canvas.height = H
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = C.bg
  ctx.fillRect(0, 0, W, H)
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'

  // 위아래 장식: 대분류 색의 큰 원 두 개 (살짝만)
  ctx.globalAlpha = 0.18
  ctx.fillStyle = dot
  ctx.beginPath()
  ctx.arc(W * 0.92, story ? 180 : 90, story ? 260 : 170, 0, Math.PI * 2)
  ctx.arc(W * 0.06, H - (story ? 220 : 120), story ? 220 : 140, 0, Math.PI * 2)
  ctx.fill()
  ctx.globalAlpha = 1

  const cardX = 90
  const cardW = W - cardX * 2
  const cardY = story ? 240 : 70
  const cardH = story ? 1080 : 800
  ctx.shadowColor = 'rgba(226, 100, 124, 0.16)'
  ctx.shadowBlur = 48
  ctx.shadowOffsetY = 16
  roundRect(ctx, cardX, cardY, cardW, cardH, 64, C.card)
  ctx.shadowColor = 'transparent'

  if (story) {
    ctx.font = `600 44px ${SANS}`
    ctx.fillStyle = C.soft
    ctx.fillText('나의 NBTI 유형은', W / 2, 165)
  }

  // 대분류 칩
  let y = cardY + (story ? 100 : 70)
  ctx.font = `700 ${story ? 40 : 34}px ${SANS}`
  const chipText = r.mainType.name
  const chipW = ctx.measureText(chipText).width + (story ? 110 : 96)
  const chipH = story ? 72 : 62
  roundRect(ctx, (W - chipW) / 2, y - chipH / 2, chipW, chipH, chipH / 2, chipBg)
  ctx.fillStyle = dot
  ctx.beginPath()
  ctx.arc((W - chipW) / 2 + (story ? 40 : 34), y, story ? 11 : 9, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = chipInk
  ctx.fillText(chipText, W / 2 + (story ? 16 : 14), y + 2)

  // 마스코트
  const m = story ? 500 : 340
  y += chipH / 2 + (story ? 20 : 10)
  if (mascot) ctx.drawImage(mascot, (W - m) / 2, y, m, m)
  y += m + (story ? 70 : 40)

  // 유형 이름
  const nameSize = fitFontSize(
    (t, s) => {
      ctx.font = `${s}px ${DISPLAY}`
      return ctx.measureText(t).width
    },
    r.name,
    cardW - 100,
    story ? 104 : 84,
    56,
  )
  ctx.font = `${nameSize}px ${DISPLAY}`
  ctx.fillStyle = C.ink
  ctx.fillText(r.name, W / 2, y)
  y += nameSize * 0.6 + (story ? 60 : 44)

  // 해시태그
  const tagFont = `700 ${story ? 38 : 32}px ${SANS}`
  const padX = story ? 30 : 24
  const tagH = story ? 70 : 58
  ctx.font = tagFont
  const rows = wrapPills((t) => ctx.measureText(t).width + padX * 2, r.tags, cardW - 100, 16)
  for (const row of rows) {
    const widths = row.map((t) => ctx.measureText(t).width + padX * 2)
    let x = (W - (widths.reduce((a, b) => a + b, 0) + 16 * (row.length - 1))) / 2
    row.forEach((t, i) => {
      roundRect(ctx, x, y - tagH / 2, widths[i], tagH, tagH / 2, C.tagBg)
      ctx.fillStyle = C.tagInk
      ctx.fillText(t, x + widths[i] / 2, y + 2)
      x += widths[i] + 16
    })
    y += tagH + 16
  }

  // 100명 중 N명 (스토리만: 점 그래프)
  const share = Math.round(r.sharePct)
  if (story) {
    let yy = cardY + cardH + 100
    ctx.font = `${72}px ${DISPLAY}`
    ctx.fillStyle = C.ink
    ctx.fillText(`조사 자료에서 성인 100명 중 약 ${share}명`, W / 2, yy)
    yy += 80
    const size = 26
    const gap = 14
    const gridW = 20 * size + 19 * gap
    for (let i = 0; i < 100; i++) {
      const cx = (W - gridW) / 2 + (i % 20) * (size + gap) + size / 2
      const cy = yy + Math.floor(i / 20) * (size + gap)
      ctx.fillStyle = i < share ? dot : C.dotOff
      ctx.beginPath()
      ctx.arc(cx, cy, size / 2, 0, Math.PI * 2)
      ctx.fill()
    }
  } else {
    ctx.font = `600 36px ${SANS}`
    ctx.fillStyle = C.soft
    // 태그 줄 수에 따라 바로 아래에 둔다 (태그가 두 줄이어도 겹치지 않게)
    ctx.fillText(`조사 자료에서 성인 100명 중 약 ${share}명이 이 유형이에요`, W / 2, Math.min(y - tagH / 2 + 40, cardY + cardH - 50))
  }

  // 서비스 이름·주소
  const fy = H - (story ? 150 : 90)
  ctx.font = `${story ? 56 : 44}px ${DISPLAY}`
  ctx.fillStyle = C.ink
  ctx.fillText(serviceName, W / 2, fy)
  ctx.font = `500 ${story ? 34 : 30}px ${SANS}`
  ctx.fillStyle = C.soft
  ctx.fillText(`너는 무슨 유형이야? · ${host}`, W / 2, fy + (story ? 64 : 50))

  return new Promise((resolve, reject) => canvas.toBlob((b) => (b ? resolve(b) : reject(new Error('이미지를 만들지 못했어요'))), 'image/png'))
}
