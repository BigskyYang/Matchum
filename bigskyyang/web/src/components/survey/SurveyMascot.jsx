import { useEffect, useState } from 'react'
import Mascot from '../Mascot.jsx'

// 설문 화면 위쪽 마스코트 + 같은 성별·나이대 조사 통계 말풍선 (내용은 lib/surveyStats.js surveyFact)
//   운동·앉는 시간·스트레스·끼니에 답하면, 다음 문항 위쪽에서 마스코트가 왼쪽으로 비켜서며 옆에 말풍선이 나왔다가 잠시 뒤 사라진다
//   자리 높이를 늘 같게 잡아 두어 말풍선이 나와도 아래 문항이 밀리거나 가려지지 않는다. 누르면 바로 닫힌다
const SHOW_MS = 4500
const LEAVE_MS = 250

function Bubble({ fact, onDone }) {
  const [leaving, setLeaving] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => setLeaving(true), SHOW_MS)
    return () => clearTimeout(t)
  }, [])
  useEffect(() => {
    if (!leaving) return undefined
    const t = setTimeout(onDone, LEAVE_MS)
    return () => clearTimeout(t)
  }, [leaving, onDone])

  return (
    <button
      type="button"
      onClick={() => setLeaving(true)}
      aria-label={`${fact.lead} 약 ${fact.pct}${fact.tail} (누르면 닫혀요)`}
      className={`absolute top-1/2 right-0 left-[6.5rem] origin-left -translate-y-1/2 text-left motion-reduce:animate-none ${leaving ? 'animate-fade-out' : 'animate-pop'}`}
    >
      <span role="status" className="relative block rounded-card bg-white px-3.5 py-2.5 text-sm leading-snug shadow-soft">
        {/* 말풍선 꼬리 (마스코트 쪽) */}
        <span aria-hidden="true" className="absolute top-1/2 -left-1.5 size-3 -translate-y-1/2 rotate-45 bg-white" />
        <span className="mb-0.5 block text-[11px] font-bold text-primary-shade">국민건강영양조사 · {fact.label}</span>
        {fact.lead} 약 <b className="text-base text-primary-shade">{fact.pct}</b>
        {fact.tail}
      </span>
    </button>
  )
}

export default function SurveyMascot({ fact, onDone }) {
  return (
    <div className="relative mt-4 h-28">
      <span
        className={`absolute top-1/2 -translate-y-1/2 transition-[left,translate] duration-300 motion-reduce:transition-none ${
          fact ? 'left-0 translate-x-0' : 'left-1/2 -translate-x-1/2'
        }`}
      >
        <Mascot name={fact ? 'happy' : 'thinking'} fallback="thinking" size="sm" />
      </span>
      {fact && <Bubble key={fact.id} fact={fact} onDone={onDone} />}
    </div>
  )
}
