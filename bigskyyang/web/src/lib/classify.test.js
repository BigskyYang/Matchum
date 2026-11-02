import { describe, expect, it } from 'vitest'
import { encode, toVector } from './encode.js'
import { classify, model } from './classify.js'
import { SAMPLE } from './fixtures.js'
import { MAIN_TYPES } from '../data/types.js'

// 각 세부 유형의 중심(원래 단위로 되돌린 값)은 그 유형으로 판정되어야 한다.
// K-Means 영역은 볼록하므로 소속 데이터 평균인 중심은 항상 자기 영역 안에 있다.
const parentOf = (leaf) => Object.keys(model.children).find((k) => leaf in model.children[k].centers)

describe('classify', () => {
  it.each(model.leaves)('%s 중심은 자기 유형으로 판정된다', (leaf) => {
    const node = model.children[parentOf(leaf)]
    const raw = node.centers[leaf].map((z, i) => z * node.std[i] + node.mean[i])
    const result = classify(raw)
    expect(result.leaf).toBe(leaf)
    expect(result.path[0]).toBe(result.main)
  })

  it('설문 응답 → 변수 변환 → 유형 판정까지 이어진다', () => {
    const { features } = encode(SAMPLE)
    const { leaf, mainId } = classify(toVector(features, model.features))
    expect(model.leaves).toContain(leaf)
    expect(MAIN_TYPES[mainId]).toBeDefined()
  })

  it('군집 번호가 바뀌어도 유형 ID로 같은 유형을 찾는다', () => {
    // export_model.py가 번호가 바뀐 것을 찾아 이전 ID를 물려준 상황을 흉내 낸다
    const swapped = { ...model, typeIds: { ...model.typeIds, Group_0: 'Group_1', Group_1: 'Group_0' } }
    const leaf = model.leaves.find((l) => l.startsWith('Group_1-'))
    const node = model.children[parentOf(leaf)]
    const raw = node.centers[leaf].map((z, i) => z * node.std[i] + node.mean[i])
    const result = classify(raw, swapped)
    expect(result.main).toBe('Group_1')
    expect(result.mainId).toBe('Group_0')
  })
})
