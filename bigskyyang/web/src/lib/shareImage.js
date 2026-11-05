// 유형 결과 공유 이미지: 휴대폰에서 canvas로 바로 그린다 (서버·외부 라이브러리 없음)
//   story: 1080×1920 (인스타 스토리 등), square: 1080×1080 (카카오톡·피드)
//   검사 결과 첫 화면과 같은 구성: '나의 NBTI 유형은', 마스코트, 대분류 칩, 유형 이름, 해시태그 + 서비스 이름과 '너는 무슨 유형이야? · 주소'
//   (개인 응답·건강 정보·조사 비율은 넣지 않는다)
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
  tagInk: '#a8425a',
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

  // 검사 결과 첫 화면과 같은 구성: '나의 NBTI 유형은' → 마스코트 → 대분류 칩 → 유형 이름 → 해시태그
  //   크기를 먼저 정하고, 아래 서비스 이름 위 공간의 가운데에 놓는다
  const S = story
    ? { label: 46, m: 640, chipH: 76, chipFont: 42, name: 112, tagFont: 40, tagH: 74, padX: 32, gap: [48, 40, 40, 56] }
    : { label: 36, m: 400, chipH: 62, chipFont: 34, name: 84, tagFont: 32, tagH: 58, padX: 24, gap: [28, 22, 26, 36] }
  const maxW = W - 160
  const nameSize = fitFontSize(
    (t, size) => {
      ctx.font = `${size}px ${DISPLAY}`
      return ctx.measureText(t).width
    },
    r.name,
    maxW,
    S.name,
    56,
  )
  ctx.font = `700 ${S.tagFont}px ${SANS}`
  const pill = (t) => ctx.measureText(t).width + S.padX * 2
  const rows = wrapPills(pill, r.tags, maxW, 16)
  const tagsH = rows.length ? rows.length * S.tagH + (rows.length - 1) * 16 : 0
  const contentH = S.label + S.gap[0] + S.m + S.gap[1] + S.chipH + S.gap[2] + nameSize + (rows.length ? S.gap[3] + tagsH : 0)
  const areaBottom = H - (story ? 260 : 170)
  let y = Math.max(story ? 120 : 50, (areaBottom - contentH) / 2)

  // 나의 NBTI 유형은
  ctx.font = `600 ${S.label}px ${SANS}`
  ctx.fillStyle = C.soft
  ctx.fillText('나의 NBTI 유형은', W / 2, y + S.label / 2)
  y += S.label + S.gap[0]

  // 마스코트
  if (mascot) ctx.drawImage(mascot, (W - S.m) / 2, y, S.m, S.m)
  y += S.m + S.gap[1]

  // 대분류 칩
  ctx.font = `700 ${S.chipFont}px ${SANS}`
  const chipText = r.mainType.name
  const chipW = ctx.measureText(chipText).width + S.chipH * 1.45
  const cy = y + S.chipH / 2
  roundRect(ctx, (W - chipW) / 2, y, chipW, S.chipH, S.chipH / 2, chipBg)
  ctx.fillStyle = dot
  ctx.beginPath()
  ctx.arc((W - chipW) / 2 + S.chipH * 0.55, cy, S.chipH * 0.15, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = chipInk
  ctx.fillText(chipText, W / 2 + S.chipH * 0.2, cy + 2)
  y += S.chipH + S.gap[2]

  // 유형 이름
  ctx.font = `${nameSize}px ${DISPLAY}`
  ctx.fillStyle = C.ink
  ctx.fillText(r.name, W / 2, y + nameSize / 2)
  y += nameSize + S.gap[3]

  // 해시태그 (흰 알약, 첫 화면과 같은 색)
  ctx.font = `700 ${S.tagFont}px ${SANS}`
  for (const row of rows) {
    const widths = row.map(pill)
    let x = (W - (widths.reduce((a, b) => a + b, 0) + 16 * (row.length - 1))) / 2
    row.forEach((t, i) => {
      ctx.shadowColor = 'rgba(226, 100, 124, 0.14)'
      ctx.shadowBlur = 24
      ctx.shadowOffsetY = 6
      roundRect(ctx, x, y, widths[i], S.tagH, S.tagH / 2, C.card)
      ctx.shadowColor = 'transparent'
      ctx.fillStyle = C.tagInk
      ctx.fillText(t, x + widths[i] / 2, y + S.tagH / 2 + 2)
      x += widths[i] + 16
    })
    y += S.tagH + 16
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
