import { describe, expect, it } from 'vitest'
import { model } from './classify.js'
import averages from '../data/habitAverages.json'
import { encode } from './encode.js'
import { SAMPLE } from './fixtures.js'
import { TYPE_AXES, hashtags, levelOf, partnerTypes, scores } from './profile.js'

const LEAF_SCORES = averages.types
const GOOD = 0.75

describe('levelOf', () => {
  it('점수를 신호등 단계로 나눈다', () => {
    expect(levelOf(1).tone).toBe('good')
    expect(levelOf(0.5).tone).toBe('fair')
    expect(levelOf(0).tone).toBe('poor')
  })
})

describe('hashtags', () => {
  it.each(model.types.map((t) => [t.id, t]))('%s 해시태그는 1~4개이고 겹치지 않는다', (_, type) => {
    const tags = hashtags(type)
    expect(tags.length).toBeGreaterThan(0)
    expect(tags.length).toBeLessThanOrEqual(4)
    expect(new Set(tags).size).toBe(tags.length)
  })

  it.each(model.types.map((t) => [t.id, t]))('%s #아침패스와 #끼니패스는 함께 붙지 않는다', (_, type) => {
    const tags = hashtags(type)
    expect(tags.includes('#아침패스') && tags.includes('#끼니패스')).toBe(false)
  })

  it('아침만 거르면 #아침패스, 점심·저녁도 거르면 #끼니패스', () => {
    const base = { breakfast: -0.9, meal_score: -0.9 }
    expect(hashtags({ z: { ...base, lunch: 0, dinner: 0 } })).toEqual(['#아침패스'])
    expect(hashtags({ z: { ...base, lunch: -0.4, dinner: 0 } })).toEqual(['#끼니패스'])
  })
})

describe('partnerTypes (짝꿍 유형 2개)', () => {
  it.each(Object.keys(LEAF_SCORES))('%s 유형: 두 짝꿍은 내 유형이 아니고 서로 다르다', (leaf) => {
    const { fill, together } = partnerTypes(LEAF_SCORES[leaf], leaf, LEAF_SCORES, TYPE_AXES)
    expect([fill.id, together.id]).not.toContain(leaf)
    expect(fill.id).not.toBe(together.id)
  })

  const mine = scores(encode(SAMPLE).features, TYPE_AXES)
  const { fill, together } = partnerTypes(mine, 'N2', LEAF_SCORES, TYPE_AXES)

  it('채워 주는 짝꿍의 이유 영역은 그 유형이 나보다 점수가 높은 영역이다', () => {
    for (const axis of fill.axes) {
      const i = TYPE_AXES.indexOf(axis)
      expect(LEAF_SCORES[fill.id][i]).toBeGreaterThan(mine[i])
    }
  })

  it('같이 크는 짝꿍의 이유 영역은 나와 그 유형 모두 좋아요(0.75)에 못 미치는 영역이다', () => {
    for (const axis of together.axes) {
      const i = TYPE_AXES.indexOf(axis)
      expect(mine[i]).toBeLessThan(GOOD)
      expect(LEAF_SCORES[together.id][i]).toBeLessThan(GOOD)
    }
  })
})
