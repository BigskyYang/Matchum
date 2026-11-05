import { describe, expect, it } from 'vitest'
import { TIPS } from '../data/tips.js'
import { SCORE_AXES } from '../lib/profile.js'
import { ICONS } from './icons.js'

// 데이터 파일에 적은 아이콘 이름이 모두 아이콘 세트에 있는지 (없으면 화면에 빈칸이 생긴다)
describe('아이콘 이름', () => {
  it('생활습관 영역·미션의 아이콘이 모두 있다', () => {
    const names = [...SCORE_AXES.map((a) => a.icon), ...TIPS.filter((t) => t.mission).map((t) => t.mission.icon)]
    for (const n of names) expect(ICONS[n], n).toBeDefined()
  })
})
