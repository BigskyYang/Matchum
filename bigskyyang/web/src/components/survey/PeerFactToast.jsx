import { useEffect, useState } from 'react'
import Mascot from '../Mascot.jsx'

// 설문 중 '같은 성별·나이대 조사 통계' 말풍선 (내용은 lib/surveyStats.js surveyFact)
//   운동·앉는 시간·스트레스·끼니 문항에 답하면, 다음 문항 화면 아래에서 마스코트가 스르륵 올라와 말하고 잠시 뒤 내려간다
//   누르면 바로 내려간다. 화면을 막지 않도록 말풍선 밖은 눌림이 그대로 아래로 지나간다
//   raised: 화면 아래에 '다음' 버튼이 있는 문항(휠 입력)에서는 버튼을 가리지 않게 그 위에서 올라온다
//   그림: public/mascot/peek (아래에서 고개를 내민 마스코트, 없으면 thinking)
const SHOW_MS = 4500
const LEAVE_MS = 300

export default function PeerFactToast({ fact, onDone, raised = false }) {
  const [leaving, setLeaving] = useState(false)

  useEffect(() => {
    const t1 = setTimeout(() => setLeaving(true), SHOW_MS)
    return () => clearTimeout(t1)
  }, [])
  useEffect(() => {
    if (!leaving) return undefined
    const t2 = setTimeout(onDone, LEAVE_MS)
    return () => clearTimeout(t2)
  }, [leaving, onDone])

  return (
    <div className={`pointer-events-none fixed inset-x-0 z-10 mx-auto w-full max-w-app overflow-hidden px-4 ${raised ? 'bottom-[calc(5.5rem+env(safe-area-inset-bottom))] pb-1' : 'bottom-0 pb-[max(0.75rem,env(safe-area-inset-bottom))]'}`}>
      <button
        type="button"
        onClick={() => setLeaving(true)}
        aria-label={`${fact.lead} 약 ${fact.pct}${fact.tail} (누르면 닫혀요)`}
        className={`pointer-events-auto flex w-full items-end gap-2 text-left motion-reduce:animate-none ${leaving ? 'animate-peek-out' : 'animate-peek-in'}`}
      >
        <Mascot name="peek" fallback="thinking" size="sm" className="-mb-3" />
        <span role="status" className="relative mb-3 flex-1 rounded-card bg-white px-4 py-3 text-sm leading-relaxed shadow-soft">
          <span className="mb-0.5 block text-xs font-bold text-primary-shade">같은 성별·나이대 조사 통계 · {fact.label}</span>
          {fact.lead} 약 <b className="text-base text-primary-shade">{fact.pct}</b>
          {fact.tail}
          <span className="mt-0.5 block text-[11px] text-ink-faint">※ 국민건강영양조사 2022–2024, 약 5% 단위</span>
        </span>
      </button>
    </div>
  )
}
