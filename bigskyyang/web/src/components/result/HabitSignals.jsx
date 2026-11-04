import { levelOf } from '../../lib/profile.js'

// 생활습관 신호등: 영역마다 작은 타일 (아이콘, 이름 아래 단계 배지). 2열로 놓아 짧게 보이게 한다
// habits: [{ key, icon, label, score(0~1) }]
const TONE = {
  good: { tile: 'bg-mint', chip: 'bg-white text-mint-strong' },
  fair: { tile: 'bg-butter', chip: 'bg-white text-ink' },
  poor: { tile: 'bg-primary-soft', chip: 'bg-white text-primary-shade' },
}

export default function HabitSignals({ habits }) {
  return (
    <ul className="grid grid-cols-2 gap-2">
      {habits.map((h) => {
        const level = levelOf(h.score)
        const tone = TONE[level.tone]
        return (
          <li key={h.key} className={`flex items-center gap-2.5 rounded-card px-3 py-2.5 ${tone.tile}`}>
            <span aria-hidden="true" className="text-2xl">
              {h.icon}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm leading-tight font-bold">{h.label}</span>
              <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-bold ${tone.chip}`}>{level.label}</span>
            </span>
          </li>
        )
      })}
    </ul>
  )
}
