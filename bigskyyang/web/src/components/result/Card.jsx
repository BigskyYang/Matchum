// 결과 화면 섹션 카드
export default function Card({ title, icon, children }) {
  return (
    <section className="rounded-card bg-white p-5 shadow-soft">
      <h2 className="flex items-center gap-2 text-lg font-bold">
        {icon && <span aria-hidden="true">{icon}</span>}
        {title}
      </h2>
      <div className="mt-3">{children}</div>
    </section>
  )
}

// 칩 목록. 비어 있으면 placeholder 문구를 보여준다
export function Chips({ items, empty }) {
  if (!items?.length) return <p className="text-sm leading-relaxed text-ink-faint">{empty}</p>
  return (
    <ul className="flex flex-wrap gap-2">
      {items.map((item) => (
        <li key={item} className="rounded-full bg-butter px-3 py-1.5 text-sm font-semibold">
          {item}
        </li>
      ))}
    </ul>
  )
}
