import { useState } from 'react'
import { BASIS_TEXT } from '../../data/nutrientGuide.js'

// 유형 화면의 '부족할 수 있는 영양소' ((나)안, 데이터는 lib/nutrition.js의 typeNutrients)
//   1줄: 대부분의 사람에게 부족한 공통 영양소, 2줄: 내 유형에서 살펴볼 것 (테두리 색 = 부족·주의)
// 영양소를 누르면 아래에 역할·대표 음식 카드를 보여 준다 (처음에는 2줄 첫 항목, 없으면 열지 않음)
const BORDER = { poor: 'border-primary-strong', fair: 'border-[#f2c14e]', common: 'border-ink-faint/40' }
const CHIP = { poor: 'bg-primary-soft text-primary-shade', fair: 'bg-butter text-ink' }

function NutrientButton({ n, tone, on, onClick, children }) {
  return (
    <button
      type="button"
      aria-pressed={on}
      onClick={onClick}
      className={`flex items-center gap-1.5 rounded-full border-2 px-3 py-1.5 text-sm font-bold transition-transform active:scale-95 ${BORDER[tone]} ${on ? 'bg-white shadow-soft' : 'bg-cream'}`}
    >
      <span aria-hidden="true">{n.icon}</span>
      {n.label}
      {children}
    </button>
  )
}

export default function TypeNutrients({ common, picks, emptyText, sexLabel, ageLabel }) {
  const [selected, setSelected] = useState(picks[0]?.key ?? null)
  const toggle = (key) => setSelected((cur) => (cur === key ? null : key))
  const pick = picks.find((n) => n.key === selected)
  const current = pick ?? common.find((n) => n.key === selected)

  return (
    <div>
      <h3 className="text-sm font-bold">🔸 대부분의 사람에게 부족해요</h3>
      <ul className="mt-2 flex flex-wrap gap-1.5">
        {common.map((n) => (
          <li key={n.key}>
            <NutrientButton n={n} tone="common" on={n.key === selected} onClick={() => toggle(n.key)} />
          </li>
        ))}
      </ul>

      <h3 className="mt-5 text-sm font-bold">🔹 내 유형에서 살펴볼 것</h3>
      {picks.length ? (
        <ul className="mt-2 flex flex-wrap gap-1.5">
          {picks.map((n) => (
            <li key={n.key}>
              <NutrientButton n={n} tone={n.level.tone} on={n.key === selected} onClick={() => toggle(n.key)}>
                <span className="text-xs font-semibold text-ink-soft">{n.of10}/10</span>
              </NutrientButton>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-ink-soft">{emptyText} 👍</p>
      )}

      {current && (
        <section
          aria-live="polite"
          className={`mt-4 rounded-card border-2 bg-white px-4 py-4 shadow-soft ${BORDER[pick ? pick.level.tone : 'common']}`}
        >
          <div className="flex items-center gap-2">
            <span aria-hidden="true" className="text-3xl">
              {current.icon}
            </span>
            <h4 className="text-lg font-extrabold">{current.label}</h4>
            {pick && (
              <span className={`ml-auto shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${CHIP[pick.level.tone]}`}>
                {pick.level.label}
              </span>
            )}
          </div>
          <p className="mt-3 text-sm leading-relaxed">
            나와 같은 유형·{sexLabel}·{ageLabel} <b>10명 중 {current.of10}명</b>이 {BASIS_TEXT[current.basis]}보다 적게 먹어요
            {pick ? ` (같은 성별·나이 평균은 10명 중 ${pick.peerOf10}명)` : '. 유형과 상관없이 대부분의 사람에게 부족한 영양소예요'}.
          </p>
          {pick?.text && <p className="mt-2 inline-block rounded-full bg-lavender px-2.5 py-1 text-xs font-bold">{pick.text}</p>}
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
        국민건강영양조사 2022–2024의 하루 식사 기록(음식만, 영양제 제외)을 2025 한국인 영양소 섭취기준과 비교한, 나와 비슷한
        사람들의 경향이에요. 나의 영양 상태를 진단한 결과가 아니에요.
      </p>
    </div>
  )
}
