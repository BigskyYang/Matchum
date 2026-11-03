import { describe, expect, it } from 'vitest'
import { MAIN_CODES, mainProfile, model, toFeatures } from './classify.js'
import { encode } from './encode.js'
import { SAMPLE } from './fixtures.js'
import { SCORE_AXES, bestPartner, groupScores, hashtags, levelOf, scores } from './profile.js'

const MAIN_SCORES = Object.fromEntries(MAIN_CODES.map((code) => [code, groupScores(toFeatures(mainProfile(code)))]))

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
})

describe('bestPartner', () => {
  it.each(MAIN_CODES)('%s 유형의 짝꿍은 다른 대분류 유형이다', (main) => {
    const partner = bestPartner(MAIN_SCORES[main], main, MAIN_SCORES)
    expect(partner.label).not.toBe(main)
    expect(MAIN_CODES).toContain(partner.label)
  })

  it('이유로 드는 영역은 짝꿍 유형이 나보다 점수가 높은 영역이다', () => {
    const mine = scores(encode(SAMPLE).features)
    const partner = bestPartner(mine, 'N', MAIN_SCORES)
    const theirs = MAIN_SCORES[partner.label]
    for (const axis of partner.helps) {
      const i = SCORE_AXES.indexOf(axis)
      expect(theirs[i]).toBeGreaterThan(mine[i])
    }
  })
})
