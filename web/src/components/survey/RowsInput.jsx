// 여러 줄을 한 화면에서 고르기 (예: 아침·점심·저녁 × 주 몇 회). 응답은 { 줄 id: 값 }
export default function RowsInput({ rows, options, value, onChange }) {
  return (
    <div className="space-y-4">
      {rows.map((row) => (
        <fieldset key={row.id}>
          <legend className="mb-1.5 text-sm font-bold text-ink-soft">{row.label}</legend>
          <div className="grid grid-cols-4 gap-1.5">
            {options.map((opt) => {
              const selected = value[row.id] === opt.value
              return (
                <button
                  key={String(opt.value)}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => onChange({ ...value, [row.id]: opt.value })}
                  className={`rounded-card px-1 py-3 text-center text-sm leading-tight font-semibold transition-[background-color,box-shadow,scale] duration-100 select-none active:scale-[0.97] ${
                    selected ? 'bg-primary-soft text-ink shadow-soft ring-2 ring-primary-strong' : 'bg-white text-ink shadow-soft'
                  }`}
                >
                  {opt.label}
                </button>
              )
            })}
          </div>
        </fieldset>
      ))}
    </div>
  )
}
