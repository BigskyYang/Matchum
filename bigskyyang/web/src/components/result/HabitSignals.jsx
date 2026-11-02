import { levelOf } from '../../lib/profile.js'

// 생활습관 신호등: 영역마다 내 점수 막대 + 같은 유형 평균 눈금 + 좋아요/보통/노력 필요
const TONE = {
  good: { bar: 'bg-mint-strong', chip: 'bg-mint text-ink' },
  fair: { bar: 'bg-[#f2c14e]', chip: 'bg-butter text-ink' },
  poor: { bar: 'bg-primary-strong', chip: 'bg-primary-soft text-primary-shade' },
}

export default function HabitSignals({ axes, mine, group }) {
  return (
    <div>
      <ul className="space-y-3">
        {axes.map((axis, i) => {
          const level = levelOf(mine[i])
          const tone = TONE[level.tone]
          return (
            <li key={axis.key} className="flex items-center gap-3">
              <span aria-hidden="true" className="w-6 text-center text-xl">
                {axis.icon}
              </span>
              <span className="w-[4.5rem] shrink-0 text-sm font-semibold">{axis.label}</span>
              <div className="relative h-3 flex-1 rounded-full bg-cream">
                <div className={`h-full rounded-full ${tone.bar}`} style={{ width: `${Math.max(4, mine[i] * 100)}%` }} />
                {/* 같은 유형 평균 */}
                <div
                  aria-hidden="true"
                  className="absolute -top-1 h-5 w-0.5 rounded-full bg-ink/50"
                  style={{ left: `calc(${group[i] * 100}% - 1px)` }}
                />
              </div>
              <span className={`w-[4.25rem] shrink-0 rounded-full py-1 text-center text-xs font-bold ${tone.chip}`}>
                {level.label}
              </span>
            </li>
          )
        })}
      </ul>
      <p className="mt-4 flex items-center justify-center gap-1.5 text-xs text-ink-faint">
        <span aria-hidden="true" className="inline-block h-3 w-0.5 rounded-full bg-ink/50" />
        같은 유형 평균
      </p>
    </div>
  )
}
