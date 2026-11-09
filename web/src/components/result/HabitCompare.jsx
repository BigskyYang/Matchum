import { levelOf } from '../../lib/profile.js'
import { compareHabits } from '../../lib/result.js'
import Icon from '../Icon.jsx'

// 나 vs 우리 유형 평균 vs 성인 전체 평균 (생활습관 영역마다 한 줄)
//   한 줄 = 왼쪽 '노력 필요' ~ 오른쪽 '좋아요' 막대 위에 점 세 개. 점수는 lib/profile.js와 같은 0~1 점수
//   위에는 유형 평균보다 차이가 큰 습관만 칩으로 (글로 늘어놓지 않는다)
// habits: [{ key, icon, label, score, typeAvg, allAvg }], code: 대분류 코드 (유형 평균 점 색)
const RING = { N: 'border-group-n', O: 'border-group-o', S: 'border-group-s', A: 'border-group-a' }

const Me = () => <span className="block size-3.5 rounded-full bg-primary-strong ring-2 ring-white" />
const TypeAvg = ({ code }) => <span className={`block size-3.5 rounded-full border-[3px] bg-white ${RING[code]}`} />
const AllAvg = () => <span className="block h-4 w-1 rounded-full bg-ink-faint" />

function Mark({ value, children, z }) {
  return (
    <span className={`absolute top-1/2 -translate-x-1/2 -translate-y-1/2 ${z}`} style={{ left: `${value * 100}%` }}>
      {children}
    </span>
  )
}

function Chips({ title, items, tone }) {
  if (!items.length) return null
  return (
    <p className="flex flex-wrap items-center gap-1.5 text-sm">
      <span className="font-bold">{title}</span>
      {items.map((h) => (
        <span key={h.key} className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-bold ${tone}`}>
          <Icon name={h.icon} size={14} />
          {h.label}
        </span>
      ))}
    </p>
  )
}

export default function HabitCompare({ habits, code }) {
  const { ahead, behind } = compareHabits(habits)
  return (
    <div>
      <div className="flex flex-col gap-1.5">
        <Chips title="내 유형보다 잘 챙겨요" items={ahead} tone="bg-mint text-mint-strong" />
        <Chips title="내 유형보다 아쉬워요" items={behind} tone="bg-primary-soft text-primary-shade" />
        {!ahead.length && !behind.length && <p className="text-sm font-bold">우리 유형 평균과 비슷한 생활습관이에요.</p>}
      </div>

      <ul aria-hidden="true" className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-soft">
        <li className="flex items-center gap-1.5">
          <Me /> 나
        </li>
        <li className="flex items-center gap-1.5">
          <TypeAvg code={code} /> 우리 유형 평균
        </li>
        <li className="flex items-center gap-1.5">
          <AllAvg /> 성인 전체 평균
        </li>
      </ul>

      <ul className="mt-3 flex flex-col gap-2.5">
        {habits.map((h) => (
          <li key={h.key} className="flex items-center gap-2">
            <span className="flex w-24 shrink-0 items-center gap-1.5 text-sm font-bold">
              <Icon name={h.icon} size={18} />
              {h.label}
            </span>
            <span className="sr-only">
              나 {levelOf(h.score).label}, 우리 유형 평균 {levelOf(h.typeAvg).label}, 성인 전체 평균 {levelOf(h.allAvg).label}
            </span>
            <span aria-hidden="true" className="relative mx-2 h-6 flex-1">
              <span className="absolute inset-x-0 top-1/2 h-1.5 -translate-y-1/2 rounded-full bg-gradient-to-r from-primary-soft via-butter to-mint" />
              <Mark value={h.allAvg} z="z-0">
                <AllAvg />
              </Mark>
              <Mark value={h.typeAvg} z="z-10">
                <TypeAvg code={code} />
              </Mark>
              <Mark value={h.score} z="z-20">
                <Me />
              </Mark>
            </span>
          </li>
        ))}
      </ul>
      <p aria-hidden="true" className="mt-1 flex justify-between pl-28 text-xs text-ink-faint">
        <span>노력 필요</span>
        <span>좋아요</span>
      </p>
    </div>
  )
}
