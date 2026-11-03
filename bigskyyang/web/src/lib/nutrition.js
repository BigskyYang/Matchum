// 유형 화면 '부족할 수 있는 영양소': 유환님 12유형 결과표(nutrientCells.json)에서 내 유형·성별·연령대 칸을 찾는다
import { NUTRIENT_GUIDE, TYPE_RULE, nutrientLevelOf } from '../data/nutrientGuide.js'

export const ageGroup = (age) => (age < 30 ? '19-29' : age < 50 ? '30-49' : age < 65 ? '50-64' : age < 75 ? '65-74' : '75+')

// { common: 공통 영양소, picks: 내 유형에서 살펴볼 것 (부족한 사람이 많은 순) }. 칸이 없으면 null
// picks 항목: of10 = 이 유형 10명 중 몇 명, peerOf10 = 같은 성별·연령대 전체 10명 중 몇 명
export function typeNutrients(cells, type, sex, age, rule = TYPE_RULE) {
  const cell = cells.types?.[type]?.[String(sex)]?.[ageGroup(age)]
  if (!cell) return null
  const isCommon = (n) => cells.common.includes(n.key)
  const picks = NUTRIENT_GUIDE.filter((n) => !isCommon(n) && cell[n.key])
    .map((n) => ({ ...n, ...cell[n.key] }))
    .filter((n) => n.p >= rule.minP && (n.p >= rule.highP || n.vs >= rule.ratio))
    .map((n) => {
      const of10 = Math.round(n.p * 10)
      return { ...n, of10, peerOf10: Math.round((n.p / n.vs) * 10), level: nutrientLevelOf(of10 / 10) }
    })
    .sort((a, b) => b.p - a.p)
  return { common: NUTRIENT_GUIDE.filter(isCommon), picks }
}
