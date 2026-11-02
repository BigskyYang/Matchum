import model from '../data/model.json'

// 3단계 K-Means와 같은 방식으로 유형을 판정한다.
// 단계마다 그 단계의 스케일러로 표준화한 뒤 가장 가까운 군집 중심을 고르고, 하위 단계가 있으면 내려간다.
// model.json은 bigskyyang/scripts/export_model.py가 만든다.
export function classify(vector, m = model) {
  const path = []
  let node = m.root
  while (node) {
    const z = vector.map((v, i) => (v - node.mean[i]) / node.std[i])
    let best = null
    let bestDist = Infinity
    for (const [label, center] of Object.entries(node.centers)) {
      const dist = center.reduce((sum, c, i) => sum + (z[i] - c) ** 2, 0)
      if (dist < bestDist) {
        best = label
        bestDist = dist
      }
    }
    path.push(best)
    node = m.children[best]
  }
  const main = path[0]
  const leaf = path[path.length - 1]
  return { main, leaf, path, mainId: typeId(main, m), leafId: typeId(leaf, m) }
}

// 군집 번호(Group_1 …) → 유형 ID. 군집화를 다시 돌려 번호가 바뀌어도 같은 유형은 같은 ID다.
// 유형 이름(types.js)과 영양소 결과표(nutrientProfiles.json)는 이 ID로 찾는다.
export const typeId = (label, m = model) => m.typeIds?.[label] ?? label

// 대분류 군집 번호 목록
export const mainLabels = (m = model) => Object.keys(m.root.centers)

export { model }
