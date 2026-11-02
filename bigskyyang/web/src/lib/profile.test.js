import { describe, expect, it } from 'vitest'
import { mainLabels, model } from './classify.js'
import { encode } from './encode.js'
import { SAMPLE } from './fixtures.js'
import { SCORE_AXES, bestPartner, groupScores, hashtags, levelOf, scores } from './profile.js'

const MAINS = mainLabels()

describe('levelOf', () => {
  it('점수를 신호등 단계로 나눈다', () => {
    expect(levelOf(1).tone).toBe('good')
    expect(levelOf(0.5).tone).toBe('fair')
    expect(levelOf(0).tone).toBe('poor')
  })
})

describe('hashtags', () => {
  it.each(model.leaves)('%s 해시태그는 4개 이하이고 겹치지 않는다', (leaf) => {
    const tags = hashtags(model, leaf)
    expect(tags.length).toBeLessThanOrEqual(4)
    expect(new Set(tags).size).toBe(tags.length)
  })
})

describe('bestPartner', () => {
  it.each(MAINS)('%s 유형의 짝꿍은 다른 대분류 유형이다', (main) => {
    const partner = bestPartner(model, groupScores(model, main), main, MAINS)
    expect(partner.label).not.toBe(main)
    expect(MAINS).toContain(partner.label)
  })

  it('이유로 드는 영역은 짝꿍 유형이 나보다 점수가 높은 영역이다', () => {
    const mine = scores(encode(SAMPLE).features)
    const partner = bestPartner(model, mine, 'Group_1', MAINS)
    const theirs = groupScores(model, partner.label)
    for (const axis of partner.helps) {
      const i = SCORE_AXES.indexOf(axis)
      expect(theirs[i]).toBeGreaterThan(mine[i])
    }
  })
})
