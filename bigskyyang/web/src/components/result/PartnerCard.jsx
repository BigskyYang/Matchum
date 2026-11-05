import { useState } from 'react'
import BottomSheet from '../BottomSheet.jsx'
import GroupChip from '../GroupChip.jsx'
import Icon from '../Icon.jsx'
import Mascot from '../Mascot.jsx'

// 같이 다니면 좋은 유형 2개를 나란히 (데이터는 lib/profile.js의 partnerTypes)
//   채워 줄 메이트: 내가 약한 습관을 잘 챙기는 유형
//   함께 바꿀 메이트: 나처럼 약한 습관이 있어 함께 바꿔 보기 좋은 유형 (내 유형 제외)
//   카드를 누르면 그 유형 설명과 고른 이유를 아래에서 올라오는 창으로 보여 준다
const KIND = {
  fill: {
    caption: '채워 줄 메이트',
    why: (axes) => `이 유형은 평균적으로 ${axes} 점수가 나보다 높아요.`,
    none: '비교한 항목에서 두드러진 점수 차이가 없어요.',
  },
  together: {
    caption: '함께 바꿀 메이트',
    why: (axes) => `나와 이 유형 모두 ${axes} 점수가 아직 '좋아요'에 못 미쳐요.`,
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
              <span key={a.key} className="inline-flex items-center gap-1 rounded-full bg-white px-2 py-0.5 text-xs font-bold">
                <Icon name={a.icon} size={14} />
                {a.label}
              </span>
            ))}
          </span>
        )}
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
            <p className="mt-1 flex items-center gap-1.5 text-sm font-bold text-ink-soft">
              <GroupChip code={p.id[0]} name={p.main.name} />
              {KIND[open].caption}
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
