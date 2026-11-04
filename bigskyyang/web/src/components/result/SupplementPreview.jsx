import { Link } from 'react-router-dom'
import { productCount, productSections, targetsFor } from '../../lib/supplements.js'
import { useCatalog } from '../../lib/useCatalog.js'

// 개인 결과 '내가 챙겨야 할 영양소' 카드 아래: 왜 추천하는지 한 줄 + 도움이 될 수 있는 건강기능식품이 몇 개 있는지
//   모든 제품을 보고 고르는 것은 건강기능식품 화면(/supplements)에서 한다
//   supplements: lib/supplements.js supplementTargets 결과, watch: 재준님 모델의 살펴볼 영양소
const SOURCE = { habitual: '평소 식사 응답', lifestyle: '생활습관 응답' }

// '마그네슘이' / '비타민 B1·B2가'
const iGa = (word) => {
  const code = word.charCodeAt(word.length - 1) - 0xac00
  const last = word[word.length - 1]
  const final = code >= 0 && code <= 11171 ? code % 28 !== 0 : /[136780LMNR]$/i.test(last)
  return final ? '이' : '가'
}

// 이름이 카드 제목과 같으면 생략 (비타민 B군만 어느 비타민인지 적는다)
function reasonOf(n, watch) {
  const rows = watch.filter((w) => n.from.includes(w.key))
  if (n.key !== 'vitamin_b') return `부족하기 쉬워요 · ${SOURCE[rows[0].source]}`
  const names = `비타민 ${rows.map((w) => w.label.replace('비타민 ', '')).join('·')}`
  return `${names}${iGa(names)} 부족하기 쉬워요`
}

export default function SupplementPreview({ supplements, watch, sex, age }) {
  const catalog = useCatalog()
  if (!supplements?.nutrients.length) return null
  const targets = targetsFor(sex, age)

  return (
    <div className="mt-5 border-t-2 border-cream pt-4">
      <h3 className="text-sm font-bold">💊 도움이 될 수 있는 건강기능식품</h3>
      <ul className="mt-2 space-y-2">
        {supplements.nutrients.map((n) => {
          const count = catalog && productCount(catalog, n.key, targets)
          const first = catalog && productSections(catalog, n.key, targets).flatMap((s) => s.items)[0]
          return (
            <li key={n.key}>
              <Link
                to={`/supplements?n=${n.key}`}
                className="flex items-center gap-3 rounded-card bg-lavender/50 px-3.5 py-3 active:scale-[0.98]"
              >
                <span aria-hidden="true" className="text-2xl">
                  {n.icon}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block font-bold">{n.label}</span>
                  <span className="block text-xs text-ink-soft">{reasonOf(n, watch)}</span>
                  {first && <span className="mt-0.5 block truncate text-xs text-ink-soft">예: {first.name}</span>}
                </span>
                <span className="shrink-0 text-sm font-bold text-primary-shade">{count == null ? '…' : `${count}개 ›`}</span>
              </Link>
            </li>
          )
        })}
      </ul>
      <Link
        to="/supplements"
        className="mt-3 block rounded-button bg-white py-3.5 text-center font-bold shadow-soft active:scale-[0.98]"
      >
        제품 모두 보고 고르기
      </Link>
    </div>
  )
}
