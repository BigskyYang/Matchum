import { describe, expect, it } from 'vitest'
import supplementProducts from '../data/supplementProducts.json'
import { PRODUCT_NUTRIENTS, TARGETS } from '../data/supplementInfo.js'
import { supplementInfo, targetsFor } from './supplements.js'

// 테스트용 가짜 제품 목록 (실제 제품 아님)
const item = (name, target = '일반') => ({ name, maker: '테스트제조', reportNo: name, target, function: '테스트 문구' })
const DATA = {
  source: '테스트',
  nutrients: {
    vitamin_c: [item('C1'), item('C2', '여성'), item('C3', '남성'), item('C4'), item('C5'), item('C6', '시니어')],
    vitamin_b: [item('B1')],
    calcium: [],
  },
  multivitamin: { balanced: [item('M1'), item('M2', '남성')], fatigue: [] },
}
const WOMAN_30 = { sex: 2, age: 30 }

describe('건강기능식품 정보 (supplementInfo)', () => {
  it('성별·나이에 맞는 대상만 (어린이·임산부 대상은 목록에 없다)', () => {
    expect(targetsFor(2, 30)).toEqual(['일반', '여성'])
    expect(targetsFor(1, 55)).toEqual(['일반', '남성', '시니어'])
  })

  it('영양소마다 내 대상 제품을 앞에서부터 3개까지', () => {
    const { nutrients } = supplementInfo(DATA, ['vitamin_c'], WOMAN_30)
    expect(nutrients[0].products.map((p) => p.name)).toEqual(['C1', 'C2', 'C4'])
    const man = supplementInfo(DATA, ['vitamin_c'], { sex: 1, age: 60 }).nutrients[0]
    expect(man.products.map((p) => p.name)).toEqual(['C1', 'C3', 'C4'])
  })

  it('비타민 B1·B2는 비타민 B군 하나로, 부족 영양소 순서대로', () => {
    const { nutrients } = supplementInfo(DATA, ['vitamin_b2', 'calcium', 'vitamin_b1', 'vitamin_c'], WOMAN_30)
    expect(nutrients.map((n) => n.key)).toEqual(['vitamin_b', 'calcium', 'vitamin_c'])
    expect(nutrients[1].products).toEqual([])
  })

  it('비타민 A·E는 제품 정보 없음, 단백질·칼륨·인은 음식으로만', () => {
    const info = supplementInfo(DATA, ['vitamin_a', 'vitamin_e', 'protein', 'potassium', 'vitamin_c'], WOMAN_30)
    expect(info.nutrients.map((n) => n.key)).toEqual(['vitamin_c'])
    expect(info.foodOnly).toEqual(['단백질', '칼륨'])
  })

  it('종합비타민은 균형형만, 내 대상에 맞게', () => {
    expect(supplementInfo(DATA, [], WOMAN_30).multivitamins.map((p) => p.name)).toEqual(['M1'])
  })

  it('제품 목록이 비어 있으면 ready = false', () => {
    expect(supplementInfo(DATA, [], WOMAN_30).ready).toBe(true)
    expect(supplementInfo({ nutrients: {}, multivitamin: { balanced: [] } }, ['vitamin_c'], WOMAN_30).ready).toBe(false)
  })
})

// 제품 목록 파일(scripts/build_supplement_products.py가 만든다) 형식 점검
describe('제품 목록 supplementProducts.json', () => {
  const keys = PRODUCT_NUTRIENTS.map((n) => n.key)
  const all = [...Object.values(supplementProducts.nutrients).flat(), ...Object.values(supplementProducts.multivitamin).flat()]

  it('영양소 키는 supplementInfo.js에 있는 것만', () => {
    for (const k of Object.keys(supplementProducts.nutrients)) expect(keys).toContain(k)
  })

  it('제품마다 이름·제조사·신고번호·기능성 원문이 있고, 대상은 일반·남성·여성·시니어', () => {
    for (const p of all) {
      for (const f of ['name', 'maker', 'reportNo', 'function']) expect(p[f]).toEqual(expect.any(String))
      expect(TARGETS).toContain(p.target)
    }
  })

  it('가격·판매처·점수·순위는 넣지 않는다 (준혁님 기준 v3 6절)', () => {
    const allowed = ['name', 'maker', 'reportNo', 'target', 'perDay', 'amount', 'dvPct', 'function', 'caution']
    for (const p of all) for (const f of Object.keys(p)) expect(allowed).toContain(f)
  })
})
