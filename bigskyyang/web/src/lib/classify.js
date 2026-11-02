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
  return { main: path[0], leaf: path[path.length - 1], path }
}

export { model }
