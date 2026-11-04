// 여러 개 고르기. 누를 때마다 넣었다 뺐다 하고, exclusive 보기('해당 없어요')는 그것만 남긴다
// 보기가 5개 이상이면 2열로 놓는다 (스크롤하지 않게)
export default function MultiInput({ options, value, onChange }) {
  const toggle = (opt) => {
    if (value.includes(opt.value)) return onChange(value.filter((v) => v !== opt.value))
    if (opt.exclusive) return onChange([opt.value])
    const exclusive = options.filter((o) => o.exclusive).map((o) => o.value)
    return onChange([...value.filter((v) => !exclusive.includes(v)), opt.value])
  }
  const grid = options.length >= 5

  return (
    <ul className={grid ? 'grid grid-cols-2 gap-2' : 'flex flex-col gap-2.5'}>
      {options.map((opt) => {
        const selected = value.includes(opt.value)
        return (
          <li key={opt.value} className={grid && opt.exclusive ? 'col-span-2' : undefined}>
            <button
              type="button"
              role="checkbox"
              aria-checked={selected}
              onClick={() => toggle(opt)}
              className={`flex h-full w-full items-center gap-2 rounded-card px-3.5 py-3.5 text-left leading-snug font-medium transition-[background-color,box-shadow,scale] duration-100 select-none active:scale-[0.98] ${
                grid ? 'text-[0.95rem]' : 'text-base'
              } ${selected ? 'bg-primary-soft text-ink shadow-soft ring-2 ring-primary-strong' : 'bg-white text-ink shadow-soft'}`}
            >
              <span
                aria-hidden="true"
                className={`flex size-5 shrink-0 items-center justify-center rounded-md border-2 text-xs font-bold ${
                  selected ? 'border-primary-strong bg-primary-strong text-white' : 'border-ink-faint/50'
                }`}
              >
                {selected ? '✓' : ''}
              </span>
              <span className="min-w-0 flex-1">{opt.label}</span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
