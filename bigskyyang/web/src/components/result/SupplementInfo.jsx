// '나의 영양소 부족 위험' 카드 맨 아래의 건강기능식품 안내 (데이터는 lib/supplements.js의 supplementTargets)
//   제품 표시는 팀 합의 전이라 보여 주지 않는다. 재준님 모델의 '살펴볼 영양소' 중 준혁님 제품 분류로 넘기는 영양소만 한 줄로
//   (위 목록과 같은 영양소라 칸을 따로 만들지 않고 이 카드에 붙인다)
//   제품 목록을 다시 붙일 때 쓸 코드: lib/supplements.js supplementInfo, data/supplementProducts.json, scripts/build_supplement_products.py

// 마지막 글자에 받침이 있으면 '은', 없으면 '는'
const eunNeun = (word) => {
  const code = word.charCodeAt(word.length - 1) - 0xac00
  return code >= 0 && code <= 11171 && code % 28 === 0 ? '는' : '은'
}

function Names({ names }) {
  const text = names.join('·')
  return (
    <>
      <b>{text}</b>
      {eunNeun(text)}
    </>
  )
}

export default function SupplementInfo({ info }) {
  if (!info || (!info.nutrients.length && !info.foodOnly.length)) return null
  const { nutrients, foodOnly } = info

  return (
    <div className="mt-4 rounded-card bg-lavender/50 px-4 py-3 text-sm leading-relaxed">
      <p className="font-bold">💊 건강기능식품 정보</p>
      {nutrients.length > 0 && (
        <p className="mt-1">
          이 중 <Names names={nutrients.map((n) => n.label)} /> 건강기능식품 정보를 찾아볼 수 있어요. 제품 정보는 준비하고
          있어요.
        </p>
      )}
      {foodOnly.length > 0 && (
        <p className="mt-1">
          <Names names={foodOnly} /> 건강기능식품보다 음식으로 챙겨 주세요.
        </p>
      )}
      <p className="mt-1.5 text-xs text-ink-soft">건강기능식품은 질병의 예방 및 치료를 위한 의약품이 아닙니다.</p>
    </div>
  )
}
