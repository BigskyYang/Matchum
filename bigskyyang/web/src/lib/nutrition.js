// 유형 화면 '부족할 수 있는 영양소': 유환님 (나)안 결과(nutrientCells.json)에서 내 유형·성별·연령대 칸을 찾는다
// 1줄·2줄에 어떤 영양소를 둘지는 유환님 코드(Yuhwan/영양분석/13_유형화면_나안.py)가 정하고, 웹은 그대로 보여 준다
import { NUTRIENT_GUIDE, nutrientLevelOf } from '../data/nutrientGuide.js'

const GUIDE = Object.fromEntries(NUTRIENT_GUIDE.map((n) => [n.key, n]))
// 판정 문구를 화면에서 바꿔 쓸 것 ('흔함'은 유형이 아니라 성별·나이대 때문에 많이 부족한 영양소라 '챙겨야 할'로 쓴다)
const TEXT = { 흔함: '같은 성별·나이대가 챙겨야 할 영양소예요' }

export const ageGroup = (age) => (age < 30 ? '19-29' : age < 50 ? '30-49' : age < 65 ? '50-64' : age < 75 ? '65-74' : '75+')

// { common: 1줄 공통 영양소, picks: 2줄 내 유형에서 살펴볼 것 }. 영양소 이름·역할·음식을 붙인다. 칸이 없으면 null
export function typeNutrients(cells, type, sex, age) {
  const cell = cells.types?.[type]?.[String(sex)]?.[ageGroup(age)]
  if (!cell) return null
  return {
    common: cell.line1.map((x) => ({ ...GUIDE[x.key], ...x })),
    picks: cell.line2.map((x) => ({ ...GUIDE[x.key], ...x, ...(TEXT[x.tag] && { text: TEXT[x.tag] }), level: nutrientLevelOf(x.of10 / 10) })),
  }
}
