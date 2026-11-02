// 챙겨 먹으면 좋은 음식 타일
export default function FoodGrid({ foods }) {
  return (
    <ul className="grid grid-cols-3 gap-2.5">
      {foods.map((f) => (
        <li key={f.label} className="flex flex-col items-center rounded-card bg-cream px-1 py-3 text-center">
          <span aria-hidden="true" className="text-3xl">
            {f.emoji}
          </span>
          <span className="mt-1.5 text-sm leading-tight font-bold">{f.label}</span>
          <span className="mt-0.5 text-[0.7rem] text-ink-soft">{f.why}</span>
        </li>
      ))}
    </ul>
  )
}
