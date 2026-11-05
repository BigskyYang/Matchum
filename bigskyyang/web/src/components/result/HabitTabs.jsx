import { useId, useRef, useState } from 'react'
import HabitCompare from './HabitCompare.jsx'
import HabitSignals from './HabitSignals.jsx'

// 생활습관 카드의 탭: '내 신호등'(타일) / '평균과 비교'(나·우리 유형·전체 평균)
//   좌우 화살표로 탭을 옮길 수 있다 (WAI-ARIA 탭 패턴)
const TABS = [
  { key: 'mine', label: '내 신호등' },
  { key: 'compare', label: '평균과 비교' },
]

export default function HabitTabs({ habits, code }) {
  const [tab, setTab] = useState('mine')
  const id = useId()
  const refs = useRef([])

  const onKey = (e, i) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return
    const next = (i + (e.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length
    setTab(TABS[next].key)
    refs.current[next]?.focus()
  }

  return (
    <div>
      <div role="tablist" aria-label="생활습관 보기" className="mb-3 grid grid-cols-2 gap-1 rounded-button bg-cream p-1">
        {TABS.map((t, i) => (
          <button
            key={t.key}
            ref={(el) => (refs.current[i] = el)}
            type="button"
            role="tab"
            id={`${id}-${t.key}`}
            aria-selected={tab === t.key}
            aria-controls={`${id}-panel`}
            tabIndex={tab === t.key ? 0 : -1}
            onClick={() => setTab(t.key)}
            onKeyDown={(e) => onKey(e, i)}
            className={`rounded-button py-2 text-sm font-bold ${tab === t.key ? 'bg-white text-ink shadow-soft' : 'text-ink-soft'}`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" id={`${id}-panel`} aria-labelledby={`${id}-${tab}`}>
        {tab === 'mine' ? <HabitSignals habits={habits} /> : <HabitCompare habits={habits} code={code} />}
      </div>
    </div>
  )
}
