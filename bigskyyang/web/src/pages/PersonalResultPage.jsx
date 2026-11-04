import { useEffect, useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { SecondaryButton } from '../components/PrimaryButton.jsx'
import Card from '../components/result/Card.jsx'
import FoodGrid from '../components/result/FoodGrid.jsx'
import HabitSignals from '../components/result/HabitSignals.jsx'
import MissionList from '../components/result/MissionList.jsx'
import NutritionRisk from '../components/result/NutritionRisk.jsx'
import { buildPersonalResult } from '../lib/result.js'
import { clearSurvey, loadSurvey } from '../lib/storage.js'

// 2단계 개인 결과 (나만 보기). 보여 줄 값은 lib/result.js의 buildPersonalResult가 계산한다
// 개인 영양 위험은 재준님 모델(data/nutritionModels.json, 약 1.3MB)을 이 화면에서만 불러와 휴대폰에서 계산한다
// 우울 점수·질환별 조언은 하지 않는다
// 맨 위 '한눈에 보기'에 가장 먼저 챙길 것만 모으고, 자세한 것은 아래 카드에서 본다
// 건강기능식품 정보는 '나의 영양소 부족 위험' 카드 맨 아래 (같은 영양소라 카드를 따로 두지 않는다, components/result/SupplementInfo.jsx)

function useModels() {
  const [models, setModels] = useState(null)
  useEffect(() => {
    import('../data/nutritionModels.json').then((m) => setModels(m.default))
  }, [])
  return models
}

function useResult() {
  const models = useModels()
  const survey = useMemo(() => loadSurvey(), [])
  return useMemo(() => {
    const { answers, done } = survey
    const redirect = !done[1] ? '/survey' : !done[2] ? '/survey2' : null
    return { redirect, result: redirect ? null : buildPersonalResult(answers, models) }
  }, [survey, models])
}

// 한눈에 보기: 살펴볼 영양소 · 이번 주 해볼 것 · 챙겨 먹을 음식 (자세한 것은 아래 카드)
function Summary({ r }) {
  const watch = r.nutrition?.watch
  const rows = [
    {
      icon: '🔺',
      title: '살펴볼 영양소',
      text: !watch ? '계산하고 있어요…' : watch.length ? watch.map((n) => n.label).join(', ') : '높은 편인 영양소는 없어요 👍',
    },
    { icon: '🎯', title: '이번 주 해볼 것', text: r.missions[0]?.title ?? '지금의 흡연·음주 습관 유지하기' },
    { icon: '🥗', title: '챙겨 먹을 음식', text: r.foods.slice(0, 3).map((f) => f.label).join(', ') },
  ]
  return (
    <section aria-labelledby="summary-title" className="rounded-card bg-primary-soft/70 px-5 py-4">
      <h2 id="summary-title" className="text-base font-bold">
        📌 한눈에 보기
      </h2>
      <dl className="mt-2.5 space-y-2 text-sm">
        {rows.map((row) => (
          <div key={row.title} className="flex gap-3">
            <dt className="w-28 shrink-0 font-bold">
              <span aria-hidden="true">{row.icon} </span>
              {row.title}
            </dt>
            <dd className="min-w-0 flex-1 leading-relaxed">{row.text}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

export default function PersonalResultPage() {
  const navigate = useNavigate()
  const { redirect, result: r } = useResult()
  if (redirect) return <Navigate to={redirect} replace />

  const retry = () => {
    clearSurvey()
    navigate('/survey')
  }

  return (
    <main className="flex flex-1 flex-col gap-4 px-5 pt-8 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <header className="text-center">
        <p className="text-sm font-semibold text-ink-soft">{r.typeName}의</p>
        <h1 className="mt-1 text-[1.75rem] leading-tight font-extrabold">나에게 맞는 결과</h1>
        <p className="mt-2 text-sm leading-relaxed text-ink-soft">이 결과는 공유되지 않고 이 휴대폰에서만 볼 수 있어요.</p>
      </header>

      <Summary r={r} />

      <Card title="흡연·음주 신호등" icon="🚦">
        <HabitSignals habits={r.habits} />
        <h3 className="mt-5 mb-2 text-sm font-bold">🎯 이번 주 해볼 것</h3>
        <MissionList missions={r.missions} empty="흡연·음주 습관은 지금처럼 유지해 주세요! 🎉" />
      </Card>

      <Card title="나의 영양소 부족 위험" icon="🔍">
        <NutritionRisk nutrition={r.nutrition} ffqAsked={r.ffqAsked} supplements={r.supplements} />
      </Card>

      <Card title="챙겨 먹으면 좋은 음식" icon="🥗">
        <FoodGrid foods={r.foods} />
      </Card>

      <footer className="mt-2 flex flex-col gap-3">
        <SecondaryButton to="/result">내 유형 결과로 돌아가기</SecondaryButton>
        <SecondaryButton onClick={retry}>처음부터 다시 검사하기</SecondaryButton>
        <p className="mt-2 text-center text-xs leading-relaxed text-ink-faint">
          결과는 국민건강영양조사 자료를 바탕으로 한 참고용이며 의료적 진단이나 처방을 대체하지 않습니다. 임신·수유 중이거나
          질환이 있거나 약을 먹고 있다면 식단과 건강기능식품은 의사·약사와 먼저 상의하세요.
        </p>
      </footer>
    </main>
  )
}
