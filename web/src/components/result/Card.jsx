import Icon from '../Icon.jsx'

// 결과 화면 섹션 카드 (정보 카드). icon: components/Icon.jsx 아이콘 이름
export default function Card({ title, icon, children }) {
  return (
    <section className="rounded-card bg-white p-5 shadow-soft">
      <h2 className="flex items-center gap-2 font-display text-xl font-normal">
        {icon && <Icon name={icon} size={22} className="text-primary-shade" />}
        {title}
      </h2>
      <div className="mt-3">{children}</div>
    </section>
  )
}
