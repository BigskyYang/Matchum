// 개인 결과의 '건강기능식품 정보' (데이터는 lib/supplements.js의 supplementTargets)
//   제품 표시는 팀 합의 전이라 보여 주지 않는다. 지금은 재준님 모델 결과 중 준혁님 제품 분류로 넘기는 값
//   ('살펴볼 영양소' 가운데 제품 분류 11종에 있는 영양소)만 보여 준다
//   제품 목록을 다시 붙일 때 쓸 코드: lib/supplements.js supplementInfo, data/supplementProducts.json, scripts/build_supplement_products.py

// 마지막 글자에 받침이 있으면 '은', 없으면 '는'
const eunNeun = (word) => {
  const code = word.charCodeAt(word.length - 1) - 0xac00
  return code >= 0 && code <= 11171 && code % 28 === 0 ? '는' : '은'
}

export default function SupplementInfo({ info }) {
  if (!info) return <p className="text-sm text-ink-soft">계산하고 있어요…</p>
  const { nutrients, foodOnly } = info

  if (!nutrients.length && !foodOnly.length) {
    return (
      <p className="text-sm leading-relaxed text-ink-soft">
        부족 위험이 높은 편인 영양소가 없어서 따로 살펴볼 건강기능식품 정보가 없어요. 지금처럼 골고루 드세요 👍
      </p>
    )
  }

  const foodText = foodOnly.join('·')
  return (
    <div>
      {nutrients.length > 0 && (
        <>
          <p className="text-sm leading-relaxed text-ink-soft">
            부족 위험이 &lsquo;높은 편&rsquo;인 영양소 중 건강기능식품 정보를 찾아볼 수 있는 영양소예요.
          </p>
          <ul className="mt-3 flex flex-wrap gap-2">
            {nutrients.map((n) => (
              <li key={n.key} className="flex items-center gap-1.5 rounded-full bg-cream px-3 py-1.5 text-sm font-bold">
                <span aria-hidden="true">{n.icon}</span>
                {n.label}
              </li>
            ))}
          </ul>
        </>
      )}
      {foodOnly.length > 0 && (
        <p className={`text-sm leading-relaxed text-ink-soft ${nutrients.length ? 'mt-3' : ''}`}>
          {foodText}
          {eunNeun(foodText)} 건강기능식품보다 음식으로 챙기는 영양소예요.
        </p>
      )}
      <p className="mt-4 rounded-card bg-butter/60 px-4 py-3 text-sm leading-relaxed">
        제품 정보는 준비하고 있어요. 그전까지는 위의 음식으로 먼저 챙겨 보세요.
      </p>
      <p className="mt-3 text-[0.7rem] leading-relaxed text-ink-faint">
        · 건강기능식품은 질병의 예방 및 치료를 위한 의약품이 아닙니다. 임신·수유 중이거나 질환·복용약이 있으면 의사·약사와
        먼저 상의하세요.
      </p>
    </div>
  )
}
