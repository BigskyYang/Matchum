// 보기 선택. 누르면 onSelect가 바로 호출되고, 선택된 보기는 강조된다
// layout: 'list' 한 줄에 하나 | 'grid' 2열 | 'row' 한 줄에 모두 | 'cards' 좌우 큰 카드 2개 (보기에 emoji가 있으면 위에 크게). 지정하지 않으면 보기가 5개 이상일 때 2열로 놓아
// 휴대폰 한 화면에 들어가게 한다 (스크롤하지 않게)
const LAYOUT = {
  list: 'flex flex-col gap-2.5',
  grid: 'grid grid-cols-2 gap-2',
  row: 'flex gap-1.5',
  cards: 'grid grid-cols-2 gap-3',
}
const BUTTON = {
  list: 'px-5 py-4 text-left text-base',
  grid: 'h-full px-3 py-3.5 text-left text-base leading-snug',
  row: 'px-1 py-4 text-center text-base',
  cards: 'flex h-full flex-col items-center gap-2 px-3 py-7 text-center text-lg font-bold',
}

const layoutOf = (options, layout) => layout ?? (options.length >= 5 ? 'grid' : 'list')

export default function ChoiceInput({ options, value, onSelect, layout }) {
  const kind = layoutOf(options, layout)
  return (
    <ul className={LAYOUT[kind]}>
      {options.map((opt) => {
        const selected = value === opt.value
        return (
          <li key={String(opt.value)} className={kind === 'row' ? 'min-w-0 flex-1' : undefined}>
            <button
              type="button"
              onClick={() => onSelect(opt.value)}
              aria-pressed={selected}
              className={`w-full rounded-card font-medium transition-[background-color,box-shadow,scale] duration-100 select-none active:scale-[0.98] ${BUTTON[kind]} ${
                selected
                  ? 'bg-primary-soft text-ink shadow-soft ring-2 ring-primary-strong'
                  : 'bg-white text-ink shadow-soft'
              }`}
            >
              {opt.emoji && (
                <span aria-hidden="true" className="text-5xl leading-none">
                  {opt.emoji}
                </span>
              )}
              {opt.label}
            </button>
          </li>
        )
      })}
    </ul>
  )
}
