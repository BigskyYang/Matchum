import { useState } from 'react'
import { BANDS } from '../../data/nutrients.js'

// 내 유형의 영양소별 부족·과잉 위험. 처음엔 위에서부터 몇 개만, '전체 보기'로 14개 모두
const TONE = {
  poor: 'bg-primary-soft text-primary-shade',
  fair: 'bg-butter text-ink',
  good: 'bg-mint text-ink',
}
const PREVIEW = 5

export default function NutrientRisks({ ranked }) {
  const [all, setAll] = useState(false)
  const shown = all ? ranked : ranked.slice(0, PREVIEW)

  return (
    <div>
      <ul className="space-y-2.5">
        {shown.map((n) => {
          const band = BANDS[n.band]
          return (
            <li key={n.key} className="flex items-center gap-3 rounded-card bg-cream px-3.5 py-3">
              <span aria-hidden="true" className="text-2xl">
                {n.icon}
              </span>
              <div className="min-w-0 flex-1">
                <p className="flex items-center gap-1.5 font-bold">
                  {n.label}
                  {n.excess && <span className="text-xs font-semibold text-ink-soft">과잉</span>}
                  {!n.reliable && (
                    <span className="rounded-full bg-white px-1.5 py-0.5 text-[0.65rem] font-semibold text-ink-faint">참고</span>
                  )}
                </p>
                <p className="mt-0.5 text-xs text-ink-soft">
                  같은 유형의 {Math.round(n.rate * 100)}%가 {n.excess ? '많이 먹어요' : '부족해요'}
                </p>
                <p className="mt-0.5 truncate text-xs text-ink-faint">🍽 {n.foods.join(' · ')}</p>
              </div>
              <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${TONE[band.tone]}`}>{band.label}</span>
            </li>
          )
        })}
      </ul>
      {ranked.length > PREVIEW && (
        <button
          type="button"
          onClick={() => setAll((v) => !v)}
          className="mt-3 w-full rounded-button py-2.5 text-sm font-semibold text-ink-soft active:bg-cream"
        >
          {all ? '접기' : `전체 ${ranked.length}개 보기`}
        </button>
      )}
      <p className="mt-2 text-[0.7rem] leading-relaxed text-ink-faint">
        국민건강영양조사 24시간 회상 자료로 본 같은 유형의 섭취 경향이에요. ‘참고’ 표시는 예측 정확도가 상대적으로 낮은 항목이에요.
      </p>
    </div>
  )
}
