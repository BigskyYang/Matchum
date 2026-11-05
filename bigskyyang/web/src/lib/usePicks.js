import { useCallback, useEffect, useState } from 'react'
import { loadPicks, savePicks } from './storage.js'

// 건강기능식품 화면들이 같이 쓰는 상태 (이 휴대폰 sessionStorage에만): 고른 제품, 확인 답, 내가 먹는 제품
export function usePicks() {
  const [picks, setPicks] = useState(loadPicks)
  useEffect(() => savePicks(picks), [picks])
  const toggle = useCallback(
    (id) => setPicks((p) => ({ ...p, ids: p.ids.includes(id) ? p.ids.filter((x) => x !== id) : [...p.ids, id] })),
    [],
  )
  const setGate = useCallback((gate) => setPicks((p) => ({ ...p, gate })), [])
  // item: { id } (목록에 있는 제품) | { name } (이름만). 같은 것은 한 번만
  const addMine = useCallback(
    (item) =>
      setPicks((p) =>
        p.mine.some((m) => (item.id ? m.id === item.id : m.name === item.name)) ? p : { ...p, mine: [...p.mine, item] },
      ),
    [],
  )
  const removeMine = useCallback((i) => setPicks((p) => ({ ...p, mine: p.mine.filter((_, j) => j !== i) })), [])
  return { picks, toggle, setGate, addMine, removeMine }
}
