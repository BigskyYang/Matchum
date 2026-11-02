// PHQ-9 선택 문항에 답한 사람에게만 보여주는 간단한 마음 건강 안내.
// 진단이 아니라 선별용 점수이므로 단정하는 표현을 피하고, 도움받을 곳을 함께 안내한다.
const LEVELS = [
  { max: 4, emoji: '🌿', title: '마음이 비교적 편안한 편이에요', text: '지금처럼 충분히 쉬고 좋아하는 일을 할 시간을 챙겨 주세요.' },
  { max: 9, emoji: '🌤️', title: '조금 지쳐 있을 수 있어요', text: '잠과 식사를 규칙적으로 하고, 가벼운 산책이나 대화로 쉬어 가세요.' },
  { max: 14, emoji: '☁️', title: '마음 건강을 살펴볼 때예요', text: '이런 상태가 2주 이상 이어진다면 가까운 정신건강복지센터나 전문가와 이야기해 보세요.' },
  { max: 27, emoji: '🫂', title: '전문가의 도움을 받아 보세요', text: '혼자 견디기보다 정신건강의학과나 정신건강복지센터에서 상담을 받아 보시길 권해요.' },
]

export default function MindCard({ total, item9 }) {
  const level = LEVELS.find((l) => total <= l.max)
  return (
    <div>
      <div className="flex items-center gap-3">
        <span aria-hidden="true" className="text-4xl">
          {level.emoji}
        </span>
        <div>
          <p className="font-bold">{level.title}</p>
          <p className="text-xs text-ink-soft">PHQ-9 점수 {total}점 / 27점</p>
        </div>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-ink-soft">{level.text}</p>

      {item9 > 0 && (
        <div className="mt-4 rounded-card bg-primary-soft p-4 text-sm leading-relaxed">
          <p className="font-bold">힘든 생각이 든다면 혼자 견디지 마세요.</p>
          <p className="mt-1 text-ink-soft">지금 바로 이야기를 들어줄 곳이 있어요.</p>
        </div>
      )}

      <ul className="mt-4 space-y-1.5 text-sm">
        <li>
          📞 자살예방상담전화 <a href="tel:109" className="font-bold text-primary-strong underline">109</a> (24시간)
        </li>
        <li>
          📞 정신건강위기상담 <a href="tel:15770199" className="font-bold text-primary-strong underline">1577-0199</a>
        </li>
      </ul>
      <p className="mt-3 text-[0.7rem] leading-relaxed text-ink-faint">
        PHQ-9는 우울 증상을 가볍게 확인해 보는 선별 도구이며 진단이 아니에요.
      </p>
    </div>
  )
}
