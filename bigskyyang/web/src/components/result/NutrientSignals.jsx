import { useState } from 'react'
import { BASIS_TEXT, NUTRIENT_LEVELS, NUTRIENT_TAGS } from '../../data/nutrientGuide.js'

// 영양소 신호등: 영양소 15개를 칸으로 보여 주고, 테두리 색으로 부족·주의·충분을 나타낸다.
// 칸을 누르면 아래에 그 영양소의 역할·대표 음식 카드를 보여 준다 (처음에는 가장 부족한 영양소)
const TONE = {
  poor: { border: 'border-primary-strong', chip: 'bg-primary-soft text-primary-shade' },
  fair: { border: 'border-[#f2c14e]', chip: 'bg-butter text-ink' },
  good: { border: 'border-mint-strong', chip: 'bg-mint text-ink' },
}

const ofTen = (p) => Math.round(p * 10)

export default function NutrientSignals({ items, sexLabel, ageLabel }) {
  const [selected, setSelected] = useState(items[0]?.key)
  const current = items.find((n) => n.key === selected) ?? items[0]

  return (
    <div>
      <p className="text-sm leading-relaxed text-ink-soft">
        나와 같은 유형·{sexLabel}·{ageLabel} 중 기준보다 적게 먹는 사람이 얼마나 되는지로 나눴어요. 영양소를 눌러 보세요.
      </p>

      <ul className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-xs font-semibold text-ink-soft" aria-label="신호등 기준">
        {NUTRIENT_LEVELS.map((l, i) => (
          <li key={l.key} className="flex items-center gap-1.5">
            <span aria-hidden="true" className={`inline-block size-3 rounded-full border-2 bg-white ${TONE[l.tone].border}`} />
            {l.label}
            <span className="font-normal text-ink-faint">
              {i === 0 ? `10명 중 ${ofTen(l.min)}명 이상` : `${ofTen(l.min)}~${ofTen(NUTRIENT_LEVELS[i - 1].min) - 1}명`}
            </span>
          </li>
        ))}
      </ul>

      <ul className="mt-3 grid grid-cols-3 gap-2">
        {items.map((n) => {
          const on = n.key === current.key
          return (
            <li key={n.key}>
              <button
                type="button"
                aria-pressed={on}
                onClick={() => setSelected(n.key)}
                className={`flex w-full flex-col items-center rounded-card border-2 px-1 py-2.5 text-center transition-transform active:scale-95 ${TONE[n.level.tone].border} ${on ? 'bg-white shadow-soft' : 'bg-cream'}`}
              >
                <span aria-hidden="true" className="text-2xl">
                  {n.icon}
                </span>
                <span className="mt-1 text-[0.8rem] leading-tight font-bold">{n.label}</span>
                <span className="mt-0.5 text-[0.7rem] text-ink-soft">
                  {n.level.label} · {n.of10}/10
                </span>
              </button>
            </li>
          )
        })}
      </ul>

      {current && (
        <section
          aria-live="polite"
          className={`mt-4 rounded-card border-2 bg-white px-4 py-4 shadow-soft ${TONE[current.level.tone].border}`}
        >
          <div className="flex items-center gap-2">
            <span aria-hidden="true" className="text-3xl">
              {current.icon}
            </span>
            <h3 className="text-lg font-extrabold">{current.label}</h3>
            <span className={`ml-auto shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${TONE[current.level.tone].chip}`}>
              {current.level.label}
            </span>
          </div>
          <p className="mt-3 text-sm leading-relaxed">
            나와 비슷한 사람 <b>10명 중 {current.of10}명</b>이 {BASIS_TEXT[current.basis]}보다 적게 먹어요.
          </p>
          {NUTRIENT_TAGS[current.tag] && (
            <p className="mt-2 inline-block rounded-full bg-lavender px-2.5 py-1 text-xs font-bold">{NUTRIENT_TAGS[current.tag]}</p>
          )}
          <p className="mt-3 text-sm leading-relaxed text-ink-soft">
            <b className="text-ink">하는 일</b> {current.role}
          </p>
          <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">
            <b className="text-ink">이런 음식에 많아요</b> {current.foods.join(' · ')}
          </p>
          {current.basis === 'AI' && (
            <p className="mt-2 text-xs leading-relaxed text-ink-faint">
              충분섭취량은 필요량을 정하기 어려운 영양소에 쓰는 넉넉한 기준이라, 이보다 적다고 꼭 부족하다는 뜻은 아니에요.
            </p>
          )}
        </section>
      )}

      <p className="mt-3 text-[0.7rem] leading-relaxed text-ink-faint">
        국민건강영양조사 2022–2024의 하루 식사 기록(음식만, 영양제 제외)을 2025 한국인 영양소 섭취기준과 비교한 같은 조건
        사람들의 비율이에요. 개인의 영양 상태를 진단한 결과가 아니에요.
      </p>
    </div>
  )
}
