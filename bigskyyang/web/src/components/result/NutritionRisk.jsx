// 개인 결과의 '나의 영양소 부족 위험' (데이터는 lib/result.js의 buildPersonalResult → nutrition)
//   두 기준(생활습관·평소 식사)을 평균하지 않고 나란히 보여 준다 (재준님 원칙)
//   살펴볼 영양소(최대 5개)만 펼쳐 두고, 나머지는 접어 둔다. 평소 식사 모델이 다루지 않는 영양소는 그 칸을 비운다
const BAND = {
  High: { label: '높은 편', cls: 'bg-primary-soft text-primary-shade' },
  Mid: { label: '보통', cls: 'bg-butter text-ink' },
  Low: { label: '낮은 편', cls: 'bg-mint text-ink' },
}

function Signal({ name, band }) {
  return (
    <span className="flex items-center gap-1 text-[0.7rem] text-ink-soft">
      {name}
      <span className={`rounded-full px-2 py-0.5 font-bold ${BAND[band].cls}`}>{BAND[band].label}</span>
    </span>
  )
}

function Row({ n, showHabitual, detail = false }) {
  return (
    <li className={`rounded-card px-3.5 py-3 ${detail ? 'border-2 border-primary bg-white' : 'bg-cream'}`}>
      <p className="flex items-center gap-2 font-bold">
        <span aria-hidden="true" className="text-xl">
          {n.icon}
        </span>
        {n.label}
      </p>
      <p className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1">
        <Signal name="생활습관" band={n.lifestyle} />
        {showHabitual && n.habitual && <Signal name="평소 식사" band={n.habitual} />}
      </p>
      {detail && (
        <>
          {n.mixed && (
            <p className="mt-1.5 text-xs text-ink-soft">두 기준의 결과가 엇갈려요. 평소 식사 기준이 더 정확한 편이라 이쪽을 따랐어요.</p>
          )}
          <p className="mt-1.5 text-xs leading-relaxed text-ink-soft">{n.guide}</p>
        </>
      )}
    </li>
  )
}

export default function NutritionRisk({ nutrition, ffqAsked }) {
  if (!nutrition) return <p className="text-sm text-ink-soft">계산하고 있어요…</p>
  const { watch, rest, habitualAvailable } = nutrition

  return (
    <div>
      <p className="text-sm leading-relaxed text-ink-soft">
        내 응답으로 영양소마다 섭취가 부족할 위험을 예측했어요. 나와 비슷한 사람들 사이에서 높은 편인지 낮은 편인지예요.
      </p>

      <h3 className="mt-4 text-sm font-bold">🔺 살펴볼 영양소</h3>
      {watch.length ? (
        <ul className="mt-2 space-y-2">
          {watch.map((n) => (
            <Row key={n.key} n={n} showHabitual={habitualAvailable} detail />
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-ink-soft">부족 위험이 높은 편인 영양소는 없어요 👍</p>
      )}

      {rest.length > 0 && (
        <details className="mt-3">
          <summary className="cursor-pointer text-sm font-semibold text-ink-soft">나머지 영양소 {rest.length}개 보기</summary>
          <ul className="mt-2 space-y-1.5">
            {rest.map((n) => (
              <Row key={n.key} n={n} showHabitual={habitualAvailable} />
            ))}
          </ul>
        </details>
      )}

      <ul className="mt-4 space-y-1 text-[0.7rem] leading-relaxed text-ink-faint">
        <li>· 생활습관 기준: 운동·수면·식사 습관 응답만으로 예측해 정확도가 높지 않아요. 참고로만 봐 주세요.</li>
        {habitualAvailable ? (
          <li>· 평소 식사 기준: 고기·생선·달걀·콩·유제품을 먹는 횟수로 예측해 생활습관 기준보다 정확한 편이에요.</li>
        ) : (
          <li>
            · 평소 식사 기준은 19~64세에서만 검증돼
            {ffqAsked ? ' 이번에는 계산하지 않았어요.' : ', 65세 이상은 생활습관 기준으로만 알려 드려요.'}
          </li>
        )}
        <li>
          · 국민건강영양조사 자료로 학습한 예측이에요. 위험이 '높은 편'이어도 부족하다고 진단한 결과가 아니고, 필요한 양을 알려
          주지 않아요.
        </li>
      </ul>
    </div>
  )
}
