import { useMemo } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import Mascot from '../components/Mascot.jsx'
import PrimaryButton, { SecondaryButton } from '../components/PrimaryButton.jsx'
import Card from '../components/result/Card.jsx'
import HabitSignals from '../components/result/HabitSignals.jsx'
import MissionList from '../components/result/MissionList.jsx'
import PartnerCard from '../components/result/PartnerCard.jsx'
import TypeNutrients from '../components/result/TypeNutrients.jsx'
import { buildTypeResult } from '../lib/result.js'
import { clearSurvey, loadSurvey } from '../lib/storage.js'

// 1단계 유형 결과 (공유용). 보여 줄 값은 lib/result.js의 buildTypeResult가 계산한다
// 순서: 유형·비율 → 생활습관 신호등·이번 주 해볼 것 → 부족할 수 있는 영양소 → 짝꿍 유형 → 2단계로
const PENDING = '영양 분석 결과가 준비되면 이곳에 표시돼요.'

function useResult() {
  return useMemo(() => {
    const { answers, done } = loadSurvey()
    return done[1] ? { ...buildTypeResult(answers), personalDone: done[2] } : null
  }, [])
}

export default function ResultPage() {
  const navigate = useNavigate()
  const r = useResult()
  if (!r) return <Navigate to="/survey" replace />

  const retry = () => {
    clearSurvey()
    navigate('/survey')
  }

  return (
    <main className="flex flex-1 flex-col gap-4 px-5 pt-8 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <header className="flex flex-col items-center text-center">
        <p className="text-sm font-semibold text-ink-soft">나의 NBTI 유형은</p>
        <Mascot name={`type_${r.leafId}`} className="mt-3" />
        <p className="mt-3 text-sm font-bold text-ink-soft">
          <span aria-hidden="true">{r.mainType.emoji} </span>
          {r.mainType.name}
        </p>
        <h1 className="mt-1 text-[1.75rem] leading-tight font-extrabold">{r.name}</h1>
        {r.tags.length > 0 && (
          <ul className="mt-3 flex flex-wrap justify-center gap-1.5">
            {r.tags.map((tag) => (
              <li key={tag} className="rounded-full bg-white px-3 py-1 text-sm font-bold text-primary-strong shadow-soft">
                {tag}
              </li>
            ))}
          </ul>
        )}
        <p className="mt-4 max-w-80 leading-relaxed text-ink-soft">{r.summary}</p>
        <p className="mt-3 text-sm text-ink-soft">
          조사 대상 성인 중 <b className="text-primary-strong">{r.sharePct.toFixed(1)}%</b>가 이 유형이에요
        </p>
      </header>

      <Card title="나의 생활습관 신호등" icon="🚦">
        <HabitSignals habits={r.habits} />
        <h3 className="mt-5 mb-2 text-sm font-bold">🎯 이번 주 해볼 것</h3>
        <MissionList missions={r.missions} />
      </Card>

      <Card title="부족할 수 있는 영양소" icon="🥄">
        {r.nutrients ? (
          <TypeNutrients
            common={r.nutrients.common}
            picks={r.nutrients.picks}
            emptyText={r.nutrientsEmptyText}
            sexLabel={r.sexLabel}
            ageLabel={r.ageLabel}
          />
        ) : (
          <p className="text-sm text-ink-faint">{PENDING}</p>
        )}
      </Card>

      <Card title="같이 다니면 좋은 유형" icon="🤝">
        <PartnerCard me={r.mainType} partner={r.partner.type} helps={r.partner.helps} />
      </Card>

      <section className="rounded-card bg-primary-soft p-5 text-center">
        <h2 className="text-lg font-bold">🔍 나에게 맞는 결과도 볼까요?</h2>
        <p className="mt-2 text-sm leading-relaxed text-ink-soft">
          흡연·음주·식습관 질문 몇 개만 더 답하면 나에게 맞춘 결과를 보여 드려요. 지금까지 답한 내용은 그대로 이어서 써요.
        </p>
        <PrimaryButton to={r.personalDone ? '/result2' : '/survey2'} className="mt-4">
          {r.personalDone ? '나에게 맞는 결과 다시 보기' : '나에게 맞는 결과 보기 (약 2분)'}
        </PrimaryButton>
      </section>

      <footer className="mt-2 flex flex-col gap-3">
        <SecondaryButton onClick={retry}>처음부터 다시 검사하기</SecondaryButton>
        <p className="mt-2 text-center text-xs leading-relaxed text-ink-faint">
          추천 결과는 국민건강영양조사 자료를 바탕으로 한 참고용이며 의료적 진단이나 처방을 대체하지 않습니다.
        </p>
      </footer>
    </main>
  )
}
