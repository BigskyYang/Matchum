// 대사질환 진단 여부에 답한 사람에게 보여주는 식생활 주의점 (결과 해석용, 의료 조언 아님)
const NOTES = [
  { key: 'hypertension', icon: '🩺', label: '고혈압', text: '국물·젓갈·가공식품을 줄여 나트륨을 덜 드세요.' },
  { key: 'diabetes', icon: '🍬', label: '당뇨병', text: '단 음료·간식을 줄이고 잡곡·채소 위주로 드세요.' },
  { key: 'dyslipidemia', icon: '🍳', label: '이상지질혈증', text: '튀김·기름진 고기를 줄이고 생선·채소를 늘려 보세요.' },
]

export default function MetabolicCard({ optional }) {
  const notes = NOTES.filter((n) => optional[n.key])
  return (
    <div>
      <ul className="space-y-2.5">
        {notes.map((n) => (
          <li key={n.key} className="flex gap-3 rounded-card bg-cream px-3.5 py-3">
            <span aria-hidden="true" className="text-2xl">
              {n.icon}
            </span>
            <p className="text-sm leading-relaxed">
              <b>{n.label}</b>
              <br />
              <span className="text-ink-soft">{n.text}</span>
            </p>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs leading-relaxed text-ink-soft">
        치료 중이라면 식단과 건강기능식품은 반드시 담당 의사·약사와 먼저 상의하세요. 복용 중인 약과 영향을 주고받을 수 있어요.
      </p>
    </div>
  )
}
