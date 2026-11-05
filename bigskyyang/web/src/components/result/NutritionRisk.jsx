import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'
import { PRODUCT_NUTRIENTS } from '../../data/supplementInfo.js'
import BottomSheet from '../BottomSheet.jsx'
import Icon from '../Icon.jsx'
import Mascot from '../Mascot.jsx'
import NutrientArt from '../NutrientArt.jsx'
import { BAND_CLS, bandLabel } from '../../data/bands.js'

// 개인 결과의 '내가 챙겨야 할 영양소' (데이터는 lib/result.js의 buildPersonalResult → nutrition)
//   재준님 화면 규칙 (Jaejun/nutrition_final_feedback_applied/config/display_policy.json)
//   - 영양소마다 등급 하나: 평소 식사 기준이 있으면 그것, 없으면 생활습관 기준 (두 확률은 평균하지 않는다)
//   - 확률 숫자는 보여 주지 않고 세 단계만. 재준님 등급(High·Mid·Low = 부족 위험 높은 편·보통·낮은 편)을
//     판정처럼 보이지 않게 경향으로 쓴다: 부족하기 쉬워요 · 보통 · 잘 챙기는 편 (나트륨은 많이 먹을 위험이라 따로)
//   화면에는 '높은 편' 영양소 칩만 두고, 누르면 아래에서 올라오는 창에 기준·음식·건강기능식품 안내를 보여 준다
//   근거·정확도·진단 아님 안내는 화면 맨 아래 '어떻게 만들었나요?'(AboutLink)에 모았다
const SOURCE = { habitual: '평소 식사 응답으로 예측했어요', lifestyle: '생활습관 응답으로 예측했어요' }

function Badge({ n }) {
  return <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${BAND_CLS[n.band]}`}>{bandLabel(n, n.band)}</span>
}

// 영양소 하나의 자세한 내용
function RiskSheet({ n, onClose }) {
  return (
    <BottomSheet
      title={
        <>
          <NutrientArt n={n} className="size-6" />
          {n.label}
        </>
      }
      aside={<Badge n={n} />}
      onClose={onClose}
    >
      <p className="text-sm text-ink-soft">
        {SOURCE[n.source]}
        {n.differ && ` (생활습관 응답으로는 '${bandLabel(n, n.lifestyle)}')`}
      </p>
      {n.role && <p className="mt-3 leading-relaxed">{n.role}</p>}
      {n.foods?.length > 0 && (
        <div className="mt-4">
          <p className="text-sm font-bold">이런 음식에 많아요</p>
          <ul className="mt-2 grid grid-cols-3 gap-2">
            {n.foods.map((f) => (
              <li key={f} className="rounded-card bg-cream px-2 py-3 text-center text-sm font-bold">
                {f}
              </li>
            ))}
          </ul>
        </div>
      )}
      {n.tip && <p className="mt-4 rounded-card bg-cream px-4 py-3 text-sm leading-relaxed">{n.tip}</p>}
      {n.supplement === 'product' && (
        <Link
          to={`/supplements?n=${PRODUCT_NUTRIENTS.find((x) => x.from.includes(n.key)).key}`}
          className="mt-4 flex items-center justify-between rounded-card bg-lavender/60 px-4 py-3 text-sm font-bold"
        >
          <span className="flex items-center gap-1.5">
            <Icon name="pill" size={18} />
            도움이 될 수 있는 건강기능식품 보기
          </span>
          <span aria-hidden="true">›</span>
        </Link>
      )}
      {n.supplement === 'food' && (
        <p className="mt-4 rounded-card bg-lavender/60 px-4 py-3 text-sm leading-relaxed">
          건강기능식품보다 음식으로 챙기는 영양소예요.
        </p>
      )}
    </BottomSheet>
  )
}

// 나머지 영양소 (보통·잘 챙기는 편, 또는 5개를 넘은 부족하기 쉬운 영양소)
function RestSheet({ rest, onPick, onClose }) {
  return (
    <BottomSheet title="나머지 영양소" onClose={onClose}>
      <ul className="grid grid-cols-2 gap-1.5">
        {rest.map((n) => (
          <li key={n.key}>
            <button
              type="button"
              onClick={() => onPick(n)}
              className="flex h-full w-full flex-col items-start gap-1.5 rounded-card bg-cream px-3 py-2.5 text-left active:scale-[0.98]"
            >
              <span className="flex items-start gap-1.5 text-sm leading-tight font-bold">
                <NutrientArt n={n} className="size-6" />
                {n.label}
              </span>
              <Badge n={n} />
            </button>
          </li>
        ))}
      </ul>
    </BottomSheet>
  )
}

export default function NutritionRisk({ nutrition, ffqAsked }) {
  const [open, setOpen] = useState(null) // 영양소 또는 'rest'
  const close = useCallback(() => setOpen(null), [])
  if (!nutrition) {
    return (
      <p className="flex items-center gap-3 text-sm text-ink-soft">
        <Mascot name="rest" fallback="default" size="xs" />
        계산하고 있어요…
      </p>
    )
  }
  const { watch, rest, habitualAvailable } = nutrition

  return (
    <div>
      {watch.length ? (
        <>
          <ul className="flex flex-wrap gap-2">
            {watch.map((n) => (
              <li key={n.key}>
                <button
                  type="button"
                  onClick={() => setOpen(n)}
                  className="flex items-center gap-1.5 rounded-full bg-primary-soft px-3.5 py-2.5 font-bold text-primary-shade active:scale-95"
                >
                  <NutrientArt n={n} className="size-6" />
                  {n.label}
                  <span aria-hidden="true">›</span>
                </button>
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p className="flex items-center gap-3 text-sm text-ink-soft">
          <Mascot name="cheer" fallback="happy" size="xs" />
          특히 부족하기 쉬운 영양소는 없어요. 지금처럼 골고루 드세요.
        </p>
      )}

      {rest.length > 0 && (
        <button type="button" onClick={() => setOpen('rest')} className="mt-2 py-3 text-sm font-semibold text-ink-soft">
          나머지 영양소 {rest.length}개 보기 ›
        </button>
      )}

      {!habitualAvailable && (
        <p className="text-xs text-ink-faint">
          {ffqAsked ? '평소 식사 응답이 부족해 생활습관 응답으로만 예측했어요.' : '65세 이상은 생활습관 응답으로만 예측했어요.'}
        </p>
      )}

      {open === 'rest' && <RestSheet rest={rest} onPick={setOpen} onClose={close} />}
      {open && open !== 'rest' && <RiskSheet n={open} onClose={close} />}
    </div>
  )
}
