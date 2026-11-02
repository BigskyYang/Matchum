// 받침 여부에 따라 조사 고르기: josa('담백형', '은', '는') → '은'
const josa = (word, withFinal, withoutFinal) => {
  const code = word.charCodeAt(word.length - 1) - 0xac00
  return code >= 0 && code <= 11171 && code % 28 ? withFinal : withoutFinal
}

// 같이 다니면 좋은 유형
export default function PartnerCard({ me, partner, helps }) {
  const helpText = helps.map((a) => `‘${a.label}’`).join('·')
  return (
    <div>
      <div className="flex items-center justify-center gap-3">
        <TypeBadge emoji={me.emoji} name={me.name} caption="나" />
        <span aria-hidden="true" className="text-2xl text-primary-strong">
          ♥
        </span>
        <TypeBadge emoji={partner.emoji} name={partner.name} caption="짝꿍" highlight />
      </div>
      <p className="mt-4 text-center text-sm leading-relaxed text-ink-soft">
        {helps.length ? (
          <>
            <b className="text-ink">{partner.name}</b>
            {josa(partner.name, '은', '는')} 내가 약한 {helpText}
            {josa(helps[helps.length - 1].label, '을', '를')} 잘 챙기는 유형이에요.
            <br />
            함께 다니면 좋은 습관이 옮아요!
          </>
        ) : (
          <>
            <b className="text-ink">{partner.name}</b>
            {josa(partner.name, '과', '와')} 함께라면 지금의 좋은 습관을 오래 지킬 수 있어요!
          </>
        )}
      </p>
      {helps.length > 0 && (
        <ul className="mt-3 flex justify-center gap-2">
          {helps.map((a) => (
            <li key={a.key} className="rounded-full bg-mint px-3 py-1 text-xs font-bold">
              {a.icon} {a.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function TypeBadge({ emoji, name, caption, highlight = false }) {
  return (
    <div
      className={`flex w-32 flex-col items-center rounded-card px-2 py-3 text-center ${highlight ? 'bg-primary-soft' : 'bg-cream'}`}
    >
      <span className="text-[0.7rem] font-bold text-ink-soft">{caption}</span>
      <span aria-hidden="true" className="mt-1 text-3xl">
        {emoji}
      </span>
      <span className="mt-1 text-sm leading-tight font-bold">{name}</span>
    </div>
  )
}
