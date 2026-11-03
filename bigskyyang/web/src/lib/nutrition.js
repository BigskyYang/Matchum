// 유형별 영양소 결과표(nutrientProfiles.json)에서 내 유형의 값을 찾아 화면용으로 정리한다
import { NUTRIENT_GUIDE, nutrientLevelOf } from '../data/nutrientGuide.js'
import { NUTRIENTS, RELIABLE_AUC } from '../data/nutrients.js'

const BAND_ORDER = { High: 0, Mid: 1, Low: 2 }

// 세부 유형 값이 있으면 그것을, 없으면 대분류 유형 값을 쓴다. 표가 비어 있으면 null
export function lookupProfile(profiles, leaf, main) {
  const hit = profiles.types?.[leaf] ?? profiles.types?.[main]
  return hit ? { ...hit, label: profiles.types[leaf] ? leaf : main } : null
}

// 위험이 높은 순서(High → Mid → Low, 같은 등급은 비율 높은 순)로 영양소 목록
export function rankNutrients(profile) {
  return NUTRIENTS.filter((n) => profile.nutrients[n.key])
    .map((n) => ({ ...n, ...profile.nutrients[n.key], reliable: n.auc >= RELIABLE_AUC }))
    .sort((a, b) => BAND_ORDER[a.band] - BAND_ORDER[b.band] || b.rate - a.rate)
}

// 위험이 '주의'인 영양소 중 건강기능식품 원료가 있는 것
export const supplementsFor = (ranked) => ranked.filter((n) => n.band === 'High' && n.supplement).map((n) => n.supplement)

// ── 영양소 신호등: 유환님 12유형 결과표(nutrientCells.json)에서 내 유형·성별·연령대 칸을 찾는다 ──
export const ageGroup = (age) => (age < 30 ? '19-29' : age < 50 ? '30-49' : age < 65 ? '50-64' : age < 75 ? '65-74' : '75+')

// 영양소 15개를 기준보다 적게 먹는 비율(p)이 높은 순으로. 칸이 없으면 빈 목록
// 화면에 '10명 중 N명'으로 보여 주므로, 단계도 반올림한 N명으로 정해 숫자와 단계가 어긋나지 않게 한다
export function nutrientSignals(cells, type, sex, age) {
  const cell = cells.types?.[type]?.[String(sex)]?.[ageGroup(age)]
  if (!cell) return []
  return NUTRIENT_GUIDE.filter((n) => cell[n.key])
    .map((n) => {
      const of10 = Math.round(cell[n.key].p * 10)
      return { ...n, ...cell[n.key], of10, level: nutrientLevelOf(of10 / 10) }
    })
    .sort((a, b) => b.p - a.p)
}
