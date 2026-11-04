import { useEffect, useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { SecondaryButton } from '../components/PrimaryButton.jsx'
import Card from '../components/result/Card.jsx'
import FoodGrid from '../components/result/FoodGrid.jsx'
import HabitSignals from '../components/result/HabitSignals.jsx'
import MissionList from '../components/result/MissionList.jsx'
import AboutLink from '../components/result/AboutLink.jsx'
import NutritionRisk from '../components/result/NutritionRisk.jsx'
import { buildPersonalResult } from '../lib/result.js'
import { clearSurvey, loadSurvey } from '../lib/storage.js'

// 2단계 개인 결과 (나만 보기). 보여 줄 값은 lib/result.js의 buildPersonalResult가 계산한다
// 개인 영양 위험은 재준님 모델(data/nutritionModels.json, 약 1.3MB)을 이 화면에서만 불러와 휴대폰에서 계산한다
// 우울 점수·질환별 조언은 하지 않는다
// 순서: 내가 챙겨야 할 영양소(부족하기 쉬운 영양소 칩, 누르면 상세 창) → 흡연·음주 신호등·이번 주 해볼 것 → 음식
// 건강기능식품 안내는 영양소 상세 창 안에, 근거·주의 안내는 맨 아래 '어떻게 만들었나요?' 창에 모았다

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
        <p className="mt-2 text-sm text-ink-soft">🔒 이 휴대폰에서만 볼 수 있어요</p>
      </header>

      <Card title="내가 챙겨야 할 영양소" icon="🔍">
        <NutritionRisk nutrition={r.nutrition} ffqAsked={r.ffqAsked} />
      </Card>

      <Card title="흡연·음주 신호등" icon="🚦">
        <HabitSignals habits={r.habits} />
        <h3 className="mt-5 mb-2 text-sm font-bold">🎯 이번 주 해볼 것</h3>
        <MissionList missions={r.missions} empty="흡연·음주 습관은 지금처럼 유지해 주세요! 🎉" />
      </Card>

      <Card title="챙겨 먹으면 좋은 음식" icon="🥗">
        <FoodGrid foods={r.foods} />
      </Card>

      <footer className="mt-2 flex flex-col gap-3">
        <SecondaryButton to="/result">내 유형 결과로 돌아가기</SecondaryButton>
        <SecondaryButton onClick={retry}>처음부터 다시 검사하기</SecondaryButton>
        <AboutLink personal />
      </footer>
    </main>
  )
}
