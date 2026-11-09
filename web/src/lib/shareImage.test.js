import { describe, expect, it } from 'vitest'
import { GROUP_COLORS, fitFontSize, wrapPills } from './shareImage.js'
import { MAIN_CODES } from './classify.js'

// 공유 이미지 배치 계산 (canvas 그리기 자체는 브라우저에서 확인)
const measure = (text, size = 10) => text.length * size

describe('공유 이미지 배치', () => {
  it('유형 이름은 폭에 맞게 글씨를 줄인다 (최소 크기 아래로는 안 줄인다)', () => {
    expect(fitFontSize(measure, '열글자열글자열글자열', 800, 104, 56)).toBe(80)
    expect(fitFontSize(measure, '짧은이름', 800, 104, 56)).toBe(104)
    expect(fitFontSize(measure, '아주아주아주아주아주아주아주아주긴이름', 800, 104, 56)).toBe(56)
  })

  it('해시태그는 폭을 넘기면 다음 줄로', () => {
    const rows = wrapPills((t) => t.length * 50, ['#스트레스많음', '#운동부족', '#끼니패스', '#아침패스'], 880, 16)
    expect(rows.flat()).toEqual(['#스트레스많음', '#운동부족', '#끼니패스', '#아침패스'])
    for (const row of rows) expect(row.reduce((w, t) => w + t.length * 50, 0) + 16 * (row.length - 1)).toBeLessThanOrEqual(880)
  })

  it('대분류마다 색이 있다', () => {
    for (const code of MAIN_CODES) expect(GROUP_COLORS[code]).toHaveLength(3)
  })
})
