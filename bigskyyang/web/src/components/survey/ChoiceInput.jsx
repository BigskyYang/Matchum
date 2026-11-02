// 보기 선택. 누르면 onSelect가 바로 호출되고, 선택된 보기는 강조된다
export default function ChoiceInput({ options, value, onSelect }) {
  return (
    <ul className="flex flex-col gap-2.5">
      {options.map((opt) => {
        const selected = value === opt.value
        return (
          <li key={String(opt.value)}>
            <button
              type="button"
              onClick={() => onSelect(opt.value)}
              aria-pressed={selected}
              className={`w-full rounded-card px-5 py-4 text-left text-base font-medium transition-[background-color,box-shadow,scale] duration-100 select-none active:scale-[0.98] ${
                selected
                  ? 'bg-primary-soft text-ink shadow-soft ring-2 ring-primary-strong'
                  : 'bg-white text-ink shadow-soft'
              }`}
            >
              {opt.label}
            </button>
          </li>
        )
      })}
    </ul>
  )
}
