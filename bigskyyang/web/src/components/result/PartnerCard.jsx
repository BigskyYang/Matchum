import Mascot from '../Mascot.jsx'

// 같이 다니면 좋은 유형 2개를 나란히 (데이터는 lib/profile.js의 partnerTypes)
//   채워 주는 짝꿍: 내가 약한 습관을 잘 챙기는 유형
//   같이 크는 짝꿍: 나처럼 약한 습관이 있어 함께 바꿔 보기 좋은 유형 (내 유형 제외)
function Partner({ caption, p, text }) {
  return (
    <li className="flex flex-col items-center rounded-card bg-cream px-2 pt-3 pb-4 text-center">
      <span className="rounded-full bg-white px-2.5 py-0.5 text-[0.7rem] font-bold text-primary-strong">{caption}</span>
      <Mascot name={`type_${p.id}`} size="sm" className="mt-2" />
      <p className="mt-1 text-[0.7rem] font-semibold text-ink-soft">
        <span aria-hidden="true">{p.main.emoji} </span>
        {p.main.name}
      </p>
      <p className="mt-0.5 text-sm leading-tight font-bold">{p.name}</p>
      {p.axes.length > 0 && (
        <ul className="mt-2 flex flex-wrap justify-center gap-1">
          {p.axes.map((a) => (
            <li key={a.key} className="rounded-full bg-white px-2 py-0.5 text-[0.7rem] font-bold">
              <span aria-hidden="true">{a.icon} </span>
              {a.label}
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-xs leading-relaxed whitespace-pre-line text-ink-soft">{text}</p>
    </li>
  )
}

export default function PartnerCard({ fill, together }) {
  return (
    <ul className="grid grid-cols-2 gap-2.5">
      <Partner
        caption="채워 주는 짝꿍"
        p={fill}
        text={fill.axes.length ? '내가 약한 습관을\n잘 챙기는 유형이에요' : '지금의 좋은 습관을\n함께 지켜 가요'}
      />
      <Partner
        caption="같이 크는 짝꿍"
        p={together}
        text={together.axes.length ? '나처럼 이 습관이 약해요.\n같이 바꿔 봐요' : '생활습관이\n나와 가장 비슷해요'}
      />
    </ul>
  )
}
