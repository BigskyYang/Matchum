import { useState } from 'react'

// '오늘부터 해볼 미션' 카드. 누르면 체크 표시 (화면에서만, 저장하지 않음)
export default function MissionList({ missions }) {
  const [done, setDone] = useState([])
  if (!missions.length) {
    return <p className="text-sm text-ink-faint">지금의 생활습관을 꾸준히 유지해 보세요! 🎉</p>
  }
  const toggle = (title) => setDone((d) => (d.includes(title) ? d.filter((t) => t !== title) : [...d, title]))

  return (
    <ol className="space-y-2.5">
      {missions.map((m, i) => {
        const checked = done.includes(m.title)
        return (
          <li key={m.title}>
            <button
              type="button"
              onClick={() => toggle(m.title)}
              aria-pressed={checked}
              className={`flex w-full items-center gap-3 rounded-card p-3.5 text-left transition-colors ${
                checked ? 'bg-mint' : 'bg-cream'
              }`}
            >
              <span
                aria-hidden="true"
                className="flex size-11 shrink-0 items-center justify-center rounded-full bg-white text-2xl shadow-soft"
              >
                {m.icon}
              </span>
              <span className="flex-1">
                <span className="block text-xs font-bold text-primary-strong">미션 {i + 1}</span>
                <span className={`block font-bold ${checked ? 'line-through opacity-60' : ''}`}>{m.title}</span>
                <span className="block text-xs leading-relaxed text-ink-soft">{m.detail}</span>
              </span>
              <span
                aria-hidden="true"
                className={`flex size-6 shrink-0 items-center justify-center rounded-full border-2 text-sm font-bold ${
                  checked ? 'border-mint-strong bg-mint-strong text-white' : 'border-ink-faint/50'
                }`}
              >
                {checked ? '✓' : ''}
              </span>
            </button>
          </li>
        )
      })}
    </ol>
  )
}
