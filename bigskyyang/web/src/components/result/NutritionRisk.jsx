// 개인 결과의 '나의 영양소 부족 위험' (데이터는 lib/result.js의 buildPersonalResult → nutrition)
//   재준님 화면 규칙 (Jaejun/nutrition_final_feedback_applied/config/display_policy.json)
//   - 영양소마다 등급 하나: 평소 식사 기준이 있으면 그것, 없으면 생활습관 기준 (두 확률은 평균하지 않는다)
//   - 확률 숫자는 보여 주지 않고 '높은 편·보통·낮은 편'만
//   - 두 기준이 다르면 생활습관 기준 등급을 작게 같이 적는다
//   살펴볼 영양소(최대 5개)는 한 묶음 목록으로 펼쳐 두고(모두 '높은 편'이라 등급 표시는 제목에 한 번만), 나머지는 접어 둔 2열 칸으로
const BAND = {
  High: { label: '높은 편', cls: 'bg-primary-soft text-primary-shade' },
  Mid: { label: '보통', cls: 'bg-butter text-ink' },
  Low: { label: '낮은 편', cls: 'bg-mint text-ink' },
}
const SOURCE = { habitual: '평소 식사 기준', lifestyle: '생활습관 기준' }

const sourceText = (n) => `${SOURCE[n.source]}${n.differ ? ` · 생활습관 기준으로는 '${BAND[n.lifestyle].label}'` : ''}`

function WatchRow({ n, showSource }) {
  return (
    <li className="flex items-start gap-3 px-3.5 py-3">
      <span aria-hidden="true" className="text-2xl leading-none">
        {n.icon}
      </span>
      <div className="min-w-0 flex-1">
        <p className="flex flex-wrap items-baseline gap-x-2">
          <b>{n.label}</b>
          {showSource && <span className="text-[0.7rem] text-ink-faint">{sourceText(n)}</span>}
        </p>
        <p className="mt-0.5 text-xs leading-relaxed text-ink-soft">{n.guide}</p>
      </div>
    </li>
  )
}

function RestItem({ n, showSource }) {
  return (
    <li className="rounded-card bg-cream px-3 py-2.5">
      <p className="flex items-start gap-1.5 text-sm leading-tight font-bold">
        <span aria-hidden="true">{n.icon}</span>
        <span className="min-w-0 flex-1">{n.label}</span>
      </p>
      <p className="mt-1 flex items-center gap-1.5">
        <span className={`rounded-full px-2 py-0.5 text-[0.7rem] font-bold ${BAND[n.band].cls}`}>{BAND[n.band].label}</span>
        {showSource && <span className="text-[0.65rem] text-ink-faint">{n.source === 'habitual' ? '평소 식사' : '생활습관'}</span>}
      </p>
    </li>
  )
}

export default function NutritionRisk({ nutrition, ffqAsked }) {
  if (!nutrition) return <p className="text-sm text-ink-soft">계산하고 있어요…</p>
  const { watch, rest, habitualAvailable } = nutrition

  return (
    <div>
      <p className="text-sm leading-relaxed text-ink-soft">
        내 응답으로 영양소마다 섭취가 부족할 위험을 예측했어요. 국민건강영양조사 참여자들과 비교해 높은 편인지 낮은 편인지예요.
      </p>

      {watch.length ? (
        <>
          <h3 className="mt-4 flex items-center gap-2 text-sm font-bold">
            🔺 살펴볼 영양소
            <span className={`rounded-full px-2 py-0.5 text-[0.7rem] ${BAND.High.cls}`}>부족 위험 높은 편 {watch.length}개</span>
          </h3>
          <ul className="mt-2 divide-y-2 divide-cream overflow-hidden rounded-card border-2 border-primary-soft bg-white">
            {watch.map((n) => (
              <WatchRow key={n.key} n={n} showSource={habitualAvailable} />
            ))}
          </ul>
        </>
      ) : (
        <p className="mt-4 text-sm text-ink-soft">부족 위험이 높은 편인 영양소는 없어요 👍</p>
      )}

      {rest.length > 0 && (
        <details className="mt-3">
          <summary className="cursor-pointer text-sm font-semibold text-ink-soft">나머지 영양소 {rest.length}개 보기</summary>
          <ul className="mt-2 grid grid-cols-2 gap-1.5">
            {rest.map((n) => (
              <RestItem key={n.key} n={n} showSource={habitualAvailable} />
            ))}
          </ul>
        </details>
      )}

      <ul className="mt-4 space-y-1 text-[0.7rem] leading-relaxed text-ink-faint">
        {habitualAvailable ? (
          <li>
            · 평소 식사 기준(고기·생선·달걀·콩·유제품을 먹는 횟수)이 있는 영양소는 그 결과를 보여 줘요. 생활습관 기준보다 정확한
            편이에요.
          </li>
        ) : (
          <li>
            · 평소 식사 기준은 19~64세에서만 검증돼
            {ffqAsked ? ' 이번에는 계산하지 않았어요.' : ', 65세 이상은 생활습관 기준으로만 알려 드려요.'}
          </li>
        )}
        <li>· 생활습관 기준은 운동·수면·식사 습관 응답만으로 예측해 정확도가 높지 않아요. 참고로만 봐 주세요.</li>
        <li>· 기준 자료 안에서의 상대 등급이에요. 부족을 진단한 결과가 아니고, 필요한 양을 알려 주지 않아요.</li>
      </ul>
    </div>
  )
}
