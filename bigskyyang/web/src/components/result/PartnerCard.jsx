import { useState } from 'react'
import BottomSheet from '../BottomSheet.jsx'
import Mascot from '../Mascot.jsx'

// 같이 다니면 좋은 유형 2개를 나란히 (데이터는 lib/profile.js의 partnerTypes)
//   채워 주는 짝꿍: 내가 약한 습관을 잘 챙기는 유형
//   같이 크는 짝꿍: 나처럼 약한 습관이 있어 함께 바꿔 보기 좋은 유형 (내 유형 제외)
//   카드를 누르면 그 유형 설명과 고른 이유를 아래에서 올라오는 창으로 보여 준다
const KIND = {
  fill: {
    caption: '채워 주는 짝꿍',
    short: '내가 약한 습관을\n잘 챙겨요',
    why: (axes) => `이 유형은 ${axes} 점수가 나보다 높아요. 함께 있으면 좋은 습관이 옮아요.`,
    none: '지금의 좋은 습관을 함께 지켜 가기 좋은 유형이에요.',
  },
  together: {
    caption: '같이 크는 짝꿍',
    short: '나처럼 이 습관이\n약해요',
    why: (axes) => `나와 이 유형 모두 ${axes} 점수가 아직 '좋아요'에 못 미쳐요. 같은 목표로 같이 바꿔 봐요.`,
    none: '생활습관이 나와 가장 비슷한 유형이에요.',
  },
}
const axesText = (axes) => axes.map((a) => `‘${a.label}’`).join('·')

function Partner({ kind, p, onOpen }) {
  return (
    <li>
      <button
        type="button"
        onClick={onOpen}
        className="flex h-full w-full flex-col items-center rounded-card bg-cream px-2 pt-3 pb-4 text-center active:scale-[0.98]"
      >
        <span className="rounded-full bg-white px-2.5 py-0.5 text-xs font-bold text-primary-shade">{KIND[kind].caption}</span>
        <Mascot name={`type_${p.id}`} size="sm" className="mt-2" />
        <span className="mt-1 text-sm leading-tight font-bold">{p.name}</span>
        {p.axes.length > 0 && (
          <span className="mt-2 flex flex-wrap justify-center gap-1">
            {p.axes.map((a) => (
              <span key={a.key} className="rounded-full bg-white px-2 py-0.5 text-xs font-bold">
                <span aria-hidden="true">{a.icon} </span>
                {a.label}
              </span>
            ))}
          </span>
        )}
        <span className="mt-2 text-xs leading-relaxed whitespace-pre-line text-ink-soft">
          {p.axes.length ? KIND[kind].short : KIND[kind].none}
        </span>
      </button>
    </li>
  )
}

export default function PartnerCard({ fill, together }) {
  const [open, setOpen] = useState(null)
  const p = open && { fill, together }[open]

  return (
    <>
      <ul className="grid grid-cols-2 gap-2.5">
        <Partner kind="fill" p={fill} onOpen={() => setOpen('fill')} />
        <Partner kind="together" p={together} onOpen={() => setOpen('together')} />
      </ul>
      {p && (
        <BottomSheet title={p.name} onClose={() => setOpen(null)}>
          <div className="flex flex-col items-center text-center">
            <Mascot name={`type_${p.id}`} />
            <p className="mt-1 text-sm font-bold text-ink-soft">
              <span aria-hidden="true">{p.main.emoji} </span>
              {p.main.name} · {KIND[open].caption}
            </p>
            <p className="mt-3 leading-relaxed whitespace-pre-line">{p.summary}</p>
            <p className="mt-4 w-full rounded-card bg-cream px-4 py-3 text-sm leading-relaxed">
              {p.axes.length ? KIND[open].why(axesText(p.axes)) : KIND[open].none}
            </p>
          </div>
        </BottomSheet>
      )}
    </>
  )
}
