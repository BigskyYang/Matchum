import { useMemo } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { SecondaryButton } from '../components/PrimaryButton.jsx'
import Card from '../components/result/Card.jsx'
import FoodGrid from '../components/result/FoodGrid.jsx'
import HabitSignals from '../components/result/HabitSignals.jsx'
import MetabolicCard from '../components/result/MetabolicCard.jsx'
import MindCard from '../components/result/MindCard.jsx'
import MissionList from '../components/result/MissionList.jsx'
import { buildPersonalResult } from '../lib/result.js'
import { clearSurvey, loadSurvey } from '../lib/storage.js'

// 2단계 개인 결과 (나만 보기). 보여 줄 값은 lib/result.js의 buildPersonalResult가 계산한다
// 개인 영양 위험 예측(재준님 모델)과 건강기능식품 정보는 연결 준비 중
function useResult() {
  return useMemo(() => {
    const { answers, done } = loadSurvey()
    const redirect = !done[1] ? '/survey' : !done[2] ? '/survey2' : null
    return { redirect, result: redirect ? null : buildPersonalResult(answers) }
  }, [])
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

      <Card title="챙겨 먹으면 좋은 음식" icon="🥗">
        <FoodGrid foods={r.foods} />
      </Card>

      <Card title="나의 영양소 부족 위험" icon="🔍">
        <p className="text-sm leading-relaxed text-ink-soft">
          내 응답으로 영양소별 부족 위험을 따로 예측하고, 그에 맞는 건강기능식품 정보를 알려 주는 기능을 준비하고 있어요.
        </p>
        <p className={`mt-3 text-xs leading-relaxed ${r.hasCondition ? 'font-semibold text-primary-shade' : 'text-ink-faint'}`}>
          {r.hasCondition
            ? '진단받은 질환이 있으니, 건강기능식품을 고를 때는 꼭 담당 의사·약사와 먼저 상의하세요.'
            : '질환이 있거나 약을 먹고 있다면 건강기능식품을 먹기 전에 의사·약사와 상담하세요.'}
        </p>
      </Card>

      {r.optional && (
        <Card title="마음 건강 체크" icon="💗">
          <MindCard total={r.optional.phqTotal} item9={r.optional.phqItem9} />
        </Card>
      )}

      {r.hasCondition && (
        <Card title="진단받은 질환이 있다면" icon="🩺">
          <MetabolicCard optional={r.optional} />
        </Card>
      )}

      <footer className="mt-2 flex flex-col gap-3">
        <SecondaryButton to="/result">내 유형 결과로 돌아가기</SecondaryButton>
        <SecondaryButton onClick={retry}>처음부터 다시 검사하기</SecondaryButton>
        <p className="mt-2 text-center text-xs leading-relaxed text-ink-faint">
          추천 결과는 국민건강영양조사 자료를 바탕으로 한 참고용이며 의료적 진단이나 처방을 대체하지 않습니다.
        </p>
      </footer>
    </main>
  )
}
