// output/nbti_12types.json만으로 JS에서 유형을 다시 배정해 Python 결과와 맞는지 확인한다 (웹에 옮길 계산과 같은 코드)
// 실행: node verify_12types.mjs   (data/web_check_12.csv는 05_jiyeon_improved.py가 만든다, git 제외)
import { readFileSync } from 'node:fs'

const model = JSON.parse(readFileSync(new URL('./output/nbti_12types.json', import.meta.url), 'utf8'))

const nearest = (v, centers) => {
  let best = null
  let bestDist = Infinity
  for (const [key, c] of centers) {
    const dist = c.reduce((s, x, i) => s + (v[i] - x) ** 2, 0)
    if (dist < bestDist) [best, bestDist] = [key, dist]
  }
  return best
}

// features: encode.js의 features 객체 (ML_*)
export function classify12(features, m = model) {
  const x = Object.fromEntries(m.inputs.map(({ name, clip }) => [name, Math.min(clip[1], Math.max(clip[0], features[name]))]))
  const scores = m.scores.map((s) => Object.entries(s.coef).reduce((sum, [n, c]) => sum + c * x[n], s.const))
  const pc = m.pca.components.map((row) => row.reduce((sum, c, i) => sum + c * (scores[i] - m.pca.mean[i]), 0))
  const macro = nearest(pc, m.macro.map((g) => [g.code, g.center]))
  const sub = m.sub[macro]
  const names = m.scores.map((s) => s.name)
  const v = sub.features.map((f, i) => (scores[names.indexOf(f)] - sub.mean[i]) / sub.std[i])
  const id = nearest(v, Object.entries(sub.centers))
  return { macro, id, type: m.types.find((t) => t.id === id) }
}

const [header, ...rows] = readFileSync(new URL('./data/web_check_12.csv', import.meta.url), 'utf8')
  .replace(/^﻿/, '').trim().split(/\r?\n/).map((l) => l.split(','))
const col = Object.fromEntries(header.map((h, i) => [h, i]))
let same = 0
for (const r of rows) {
  const f = Object.fromEntries(model.inputs.map(({ name }) => [name, Number(r[col[name]])]))
  if (classify12(f).id === r[col.expected]) same += 1
}
console.log(`JS 재배정 일치: ${same} / ${rows.length} (${((100 * same) / rows.length).toFixed(2)}%)`)
