import { useState } from 'react'
import BottomSheet from '../BottomSheet.jsx'
import GroupChip from '../GroupChip.jsx'
import Mascot from '../Mascot.jsx'

// 내 유형 위치: 내 유형 중심 ~ 두 유형의 경계 ~ 가장 가까운 다른 유형 (lib/result.js typeBoundary)
//   막대 왼쪽 끝이 내 유형 중심, 가운데 점선이 경계. '나' 점이 가운데에 가까울수록 이웃 유형과도 닮았다
//   이웃 유형을 누르면 그 유형 설명을 아래 창으로 보여 준다
// 막대 반쪽 색: 그쪽 유형의 대분류 색 (연하게)
const HALF = { N: 'bg-group-n/40', O: 'bg-group-o/40', S: 'bg-group-s/40', A: 'bg-group-a/40' }

const hasBatchim = (word) => {
  const c = word.charCodeAt(word.length - 1) - 0xac00
  return c >= 0 && c <= 11171 && c % 28 !== 0
}
const gwa = (word) => `${word}${hasBatchim(word) ? '과' : '와'}`
const iga = (word) => `${word}${hasBatchim(word) ? '이' : '가'}`

const TEXT = {
  core: (me) => ({ title: `${me}의 중심 가까이에 있어요`, sub: '응답이 조금 달라져도 같은 유형이 나오기 쉬워요.' }),
  near: (me, n) => ({ title: `${gwa(n)}도 조금 닮았어요`, sub: `${me} 다음으로 가까운 유형이에요.` }),
  edge: (me, n) => ({
    title: `${gwa(n)}의 경계에 있어요`,
    sub: `응답이 조금만 달라도 ${iga(n)} 나올 수 있어요. 성인 10명 중 2명쯤이 이렇게 경계에 있어요.`,
  }),
}

export default function TypeBoundary({ leafId, name, boundary }) {
  const [open, setOpen] = useState(false)
  const n = boundary.neighbor
  const text = TEXT[boundary.level](name, n.name)

  return (
    <div>
      <p className="font-bold">{text.title}</p>
      <p className="mt-1 text-sm leading-relaxed text-ink-soft">{text.sub}</p>

      <div className="mt-4 flex items-end gap-2">
        <span className="flex w-16 shrink-0 flex-col items-center text-center">
          <Mascot name={`type_${leafId}`} size="xs" />
          <span className="mt-1 text-xs leading-tight font-bold">{name}</span>
        </span>
        <span aria-hidden="true" className="relative mb-7 h-10 flex-1">
          <span className={`absolute bottom-2 left-0 h-1.5 w-1/2 rounded-l-full ${HALF[leafId[0]]}`} />
          <span className={`absolute right-0 bottom-2 h-1.5 w-1/2 rounded-r-full ${HALF[n.id[0]]}`} />
          <span className="absolute bottom-0 left-1/2 h-5 -translate-x-1/2 border-l-2 border-dashed border-ink-faint" />
          <span className="absolute top-0 left-1/2 -translate-x-1/2 text-xs text-ink-faint">경계</span>
          <span className="absolute bottom-0.5 flex -translate-x-1/2 flex-col items-center" style={{ left: `${boundary.pos * 100}%` }}>
            <span className="text-xs font-bold text-primary-shade">나</span>
            <span className="mt-0.5 block size-4 rounded-full bg-primary-strong ring-2 ring-white" />
          </span>
        </span>
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label={`${n.name} 유형 설명 보기`}
          className="flex w-16 shrink-0 flex-col items-center rounded-card text-center active:scale-[0.98]"
        >
          <Mascot name={`type_${n.id}`} size="xs" />
          <span className="mt-1 text-xs leading-tight font-bold underline decoration-ink/20 underline-offset-2">{n.name}</span>
        </button>
      </div>

      {open && (
        <BottomSheet title={n.name} onClose={() => setOpen(false)}>
          <div className="flex flex-col items-center text-center">
            <Mascot name={`type_${n.id}`} size="sm" />
            <GroupChip code={n.id[0]} name={n.main.name} className="mt-2" />
            <p className="mt-3 leading-relaxed whitespace-pre-line text-ink-soft">{n.summary}</p>
          </div>
        </BottomSheet>
      )}
    </div>
  )
}
