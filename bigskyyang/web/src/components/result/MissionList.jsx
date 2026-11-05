import Icon from '../Icon.jsx'

// '이번 주 해볼 것' 목록. 결과를 읽고 지나가는 화면이라 체크 기능 없이 짧게 보여 준다
export default function MissionList({ missions, empty = '지금의 생활습관을 꾸준히 유지해 보세요.' }) {
  if (!missions.length) return <p className="text-sm text-ink-faint">{empty}</p>
  return (
    <ul className="space-y-2">
      {missions.map((m) => (
        <li key={m.title} className="flex items-center gap-3 rounded-card bg-cream px-3.5 py-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-white text-primary-shade shadow-soft">
            <Icon name={m.icon} size={22} />
          </span>
          <span className="min-w-0 flex-1 font-bold">{m.title}</span>
        </li>
      ))}
    </ul>
  )
}
