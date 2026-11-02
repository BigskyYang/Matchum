// 유형별 영양소 결과표(nutrientProfiles.json)에서 내 유형의 값을 찾아 화면용으로 정리한다
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
