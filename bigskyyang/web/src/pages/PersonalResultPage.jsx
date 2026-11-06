import { useMemo } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import Icon from '../components/Icon.jsx'
import { SecondaryButton } from '../components/PrimaryButton.jsx'
import Card from '../components/result/Card.jsx'
import FoodGrid from '../components/result/FoodGrid.jsx'
import HabitSignals from '../components/result/HabitSignals.jsx'
import MissionList from '../components/result/MissionList.jsx'
import AboutLink from '../components/result/AboutLink.jsx'
import NutritionRisk from '../components/result/NutritionRisk.jsx'
import VitaminDCard from '../components/result/VitaminDCard.jsx'
import { buildPersonalResult } from '../lib/result.js'
import { clearSurvey, loadSurvey } from '../lib/storage.js'
import { useModels } from '../lib/useCatalog.js'
import { vitaminDInfo } from '../lib/vitaminD.js'

// 2단계 개인 결과 (나만 보기). 보여 줄 값은 lib/result.js의 buildPersonalResult가 계산한다
// 개인 영양 위험은 재준님 모델(data/nutritionModels.json, 약 1.3MB)을 이 화면에서만 불러와 휴대폰에서 계산한다
// 우울 점수·질환별 조언은 하지 않는다
// 순서: 영양소 → 비타민 D와 내 생활(재준님 생활 안내, 예측 아님) → 음식 → 흡연·음주 신호등·이번 주 해볼 것 → 응답 변경 비교(/simulate)
// 영양소 칩 아래에 도움이 될 수 있는 건강기능식품(추천 이유·제품 수) → 모두 보고 고르기는 /supplements
// 근거·주의 안내는 맨 아래 '어떻게 만들었나요?' 창에 모았다

function useResult() {
  const models = useModels()
  const survey = useMemo(() => loadSurvey(), [])
  return useMemo(() => {
    const { answers, done } = survey
    const redirect = !done[1] ? '/survey' : !done[2] ? '/survey2' : null
    return { redirect, result: redirect ? null : { ...buildPersonalResult(answers, models), vitaminD: vitaminDInfo(answers) } }
  }, [survey, models])
}

export default function PersonalResultPage() {
  const navigate = useNavigate()
  const { redirect, result: r } = useResult()
  if (redirect) return <Navigate to={redirect} replace />

  const retry = () => {
    // 응답을 지우고 시작 화면으로 (다시 시작할지는 사용자가 고른다)
    clearSurvey()
    navigate('/')
  }

  return (
    <main className="flex flex-1 flex-col gap-4 px-5 pt-8 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <header className="text-center">
        <p className="text-sm font-semibold text-ink-soft">{r.typeName}의</p>
        <h1 className="mt-1 font-display text-[1.75rem] leading-tight font-normal">나에게 맞는 결과</h1>
        <p className="mt-2 inline-flex items-center gap-1 text-sm text-ink-soft">
          <Icon name="lock" size={16} />이 브라우저에서 계산한 결과예요
        </p>
      </header>

      <Card title="내가 특히 살펴볼 영양소" icon="checklist">
        <NutritionRisk nutrition={r.nutrition} ffqAsked={r.ffqAsked} />
        {r.supplements?.nutrients.length > 0 && (
          <Link to="/supplements" className="mt-3 block rounded-button bg-cream py-3 text-center text-sm font-bold text-primary-shade active:scale-[0.99]">
            관련 제품 찾아보기 ›
          </Link>
        )}
      </Card>

      <Card title="비타민 D와 내 생활" icon="sunrise">
        <VitaminDCard info={r.vitaminD} />
      </Card>

      <Card title="챙겨 먹으면 좋은 음식" icon="salad">
        <FoodGrid foods={r.foods} watchKeys={r.nutrition?.watch.map((n) => n.key) ?? []} />
      </Card>

      <Card title="흡연·음주 신호등" icon="traffic">
        <HabitSignals habits={r.habits} />
        <h3 className="mt-5 mb-2 flex items-center gap-1.5 text-sm font-bold">
          <Icon name="target" size={18} className="text-primary-shade" />
          이번 주 해볼 것
        </h3>
        <MissionList missions={r.missions} empty="흡연·음주 습관은 지금처럼 유지해 주세요." />
      </Card>

      <Link
        to="/simulate"
        className="flex items-center gap-3 rounded-card bg-lavender/60 p-5 shadow-soft active:scale-[0.99]"
      >
        <Icon name="sparkles" size={28} className="shrink-0 text-primary-shade" />
        <span className="flex-1 font-display text-xl">내 습관을 개선했을 때 확인하기</span>
        <Icon name="next" size={20} className="shrink-0 text-ink-faint" />
      </Link>

      <Card title="제품 확인과 약사 상담" icon="pill">
        <SecondaryButton to="/my-supplements">먹는 제품 등록 · 상담 메모 만들기</SecondaryButton>
      </Card>

      <footer className="mt-2 flex flex-col gap-3">
        <SecondaryButton to="/result">내 유형 결과로 돌아가기</SecondaryButton>
        <SecondaryButton onClick={retry}>처음부터 다시 검사하기</SecondaryButton>
        <AboutLink personal />
      </footer>
    </main>
  )
}
