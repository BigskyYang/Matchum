import { levelOf } from '../../lib/profile.js'
import Icon from '../Icon.jsx'

// 생활습관 신호등: 2열 타일의 위쪽은 아이콘·상태, 아래쪽은 항목 이름
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
          <li key={h.key} className={`flex flex-col gap-2 rounded-card px-3 py-2.5 ${tone.tile}`}>
            <span className="flex items-center justify-between gap-1">
              <Icon name={h.icon} size={24} className="shrink-0" />
              <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-bold ${tone.chip}`}>{level.label}</span>
            </span>
            <span className="text-sm leading-tight font-bold">{h.label}</span>
          </li>
        )
      })}
    </ul>
  )
}
