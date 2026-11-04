import { useEffect, useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { SecondaryButton } from '../components/PrimaryButton.jsx'
import Card from '../components/result/Card.jsx'
import FoodGrid from '../components/result/FoodGrid.jsx'
import HabitSignals from '../components/result/HabitSignals.jsx'
import MissionList from '../components/result/MissionList.jsx'
import NutritionRisk from '../components/result/NutritionRisk.jsx'
import SupplementInfo from '../components/result/SupplementInfo.jsx'
import { buildPersonalResult } from '../lib/result.js'
import { clearSurvey, loadSurvey } from '../lib/storage.js'

// 2단계 개인 결과 (나만 보기). 보여 줄 값은 lib/result.js의 buildPersonalResult가 계산한다
// 개인 영양 위험은 재준님 모델(data/nutritionModels.json, 약 1.3MB)을 이 화면에서만 불러와 휴대폰에서 계산한다
// 우울 점수·질환별 조언은 하지 않는다
// 건강기능식품 정보는 음식 다음에, 재준님 결과 중 준혁님 제품 분류로 넘기는 영양소만 (제품 표시는 팀 합의 후, components/result/SupplementInfo.jsx)

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

      <Card title="흡연·음주 신호등" icon="🚦">
        <HabitSignals habits={r.habits} />
        <h3 className="mt-5 mb-2 text-sm font-bold">🎯 이번 주 해볼 것</h3>
        <MissionList missions={r.missions} empty="흡연·음주 습관은 지금처럼 유지해 주세요! 🎉" />
      </Card>

      <Card title="나의 영양소 부족 위험" icon="🔍">
        <NutritionRisk nutrition={r.nutrition} ffqAsked={r.ffqAsked} />
      </Card>

      <Card title="챙겨 먹으면 좋은 음식" icon="🥗">
        <FoodGrid foods={r.foods} />
      </Card>

      <Card title="건강기능식품 정보" icon="💊">
        <SupplementInfo info={r.supplements} />
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
