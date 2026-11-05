import { useState } from 'react'
import BottomSheet from '../BottomSheet.jsx'
import GroupChip from '../GroupChip.jsx'
import Mascot from '../Mascot.jsx'

// 내 유형 위치: 내 유형 중심 ~ 두 유형의 경계 ~ 가장 가까운 다른 유형 (lib/result.js typeBoundary)
//   막대 왼쪽 끝이 내 유형 중심, 가운데 점선이 경계. '나' 점이 가운데에 가까울수록 이웃 유형과도 닮았다
//   이웃 유형을 누르면 그 유형 설명을 아래 창으로 보여 준다
// 막대 반쪽 색: 그쪽 유형의 대분류 색 (연하게)
const HALF = { N: 'bg-group-n/40', O: 'bg-group-o/40', S: 'bg-group-s/40', A: 'bg-group-a/40' }

const POSITION = { core: '내 유형 중심에 가까움', near: '이웃 유형과도 닮음', edge: '두 유형의 경계에 가까움' }

export default function TypeBoundary({ leafId, name, boundary }) {
  const [open, setOpen] = useState(false)
  const n = boundary.neighbor

  return (
    <div>
      <p className="sr-only">{name} / {n.name} 사이의 내 위치: {POSITION[boundary.level]}</p>

      <div className="flex items-end gap-2">
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
