// 결과 화면 섹션 카드
export default function Card({ title, icon, children }) {
  return (
    <section className="rounded-card bg-white p-5 shadow-soft">
      <h2 className="flex items-center gap-2 text-xl font-bold">
        {icon && <span aria-hidden="true">{icon}</span>}
        {title}
      </h2>
      <div className="mt-3">{children}</div>
    </section>
  )
}

