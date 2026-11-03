import { useMemo } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import Mascot from '../components/Mascot.jsx'
import PrimaryButton, { SecondaryButton } from '../components/PrimaryButton.jsx'
import Card from '../components/result/Card.jsx'
import FoodGrid from '../components/result/FoodGrid.jsx'
import HabitSignals from '../components/result/HabitSignals.jsx'
import MetabolicCard from '../components/result/MetabolicCard.jsx'
import MindCard from '../components/result/MindCard.jsx'
import MissionList from '../components/result/MissionList.jsx'
import PartnerCard from '../components/result/PartnerCard.jsx'
import TypeNutrients from '../components/result/TypeNutrients.jsx'
import { buildResult } from '../lib/result.js'
import { SCORE_AXES } from '../lib/profile.js'
import { clearSurvey, loadSurvey } from '../lib/storage.js'

// 결과 화면. 보여 줄 값은 lib/result.js의 buildResult가 계산한다
const PENDING = '영양 분석 결과가 준비되면 이곳에 표시돼요.'

function useResult() {
  return useMemo(() => {
    const { answers, done } = loadSurvey()
    return done ? buildResult(answers) : null
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
      </header>

      <Card title="나와 같은 유형은?" icon="👥">
        <p className="text-center">
          <span className="text-sm text-ink-soft">조사 대상 성인 중</span>
          <span className="mx-1.5 text-4xl font-extrabold text-primary-strong">{r.sharePct.toFixed(1)}%</span>
        </p>
        <p className="mt-1 text-center text-xs text-ink-faint">국민건강영양조사 2022–2024 기준</p>
      </Card>

      <Card title="나의 생활습관 신호등" icon="🚦">
        <HabitSignals axes={SCORE_AXES} mine={r.myScores} group={r.typeScores} />
      </Card>

      <Card title="오늘부터 해볼 미션" icon="🎯">
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

      <Card title="챙겨 먹으면 좋은 음식" icon="🥗">
        <FoodGrid foods={r.foods} />
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

      <Card title="같이 다니면 좋은 유형" icon="🤝">
        <PartnerCard me={r.mainType} partner={r.partner.type} helps={r.partner.helps} />
      </Card>

      <Card title="더 알아보기" icon="🔍">
        <p className="text-sm leading-relaxed text-ink-soft">
          유형 결과는 나와 비슷한 사람들의 경향이에요. 내 응답만으로 영양소별 부족 위험을 따로 예측하고, 그에 맞는 건강기능식품
          정보를 알려 주는 개인 맞춤 분석은 준비 중이에요.
        </p>
        <p className={`mt-3 text-xs leading-relaxed ${r.hasCondition ? 'font-semibold text-primary-shade' : 'text-ink-faint'}`}>
          {r.hasCondition
            ? '진단받은 질환이 있으니, 건강기능식품을 고를 때는 꼭 담당 의사·약사와 먼저 상의하세요.'
            : '질환이 있거나 약을 먹고 있다면 건강기능식품을 먹기 전에 의사·약사와 상담하세요.'}
        </p>
      </Card>

      <footer className="mt-2 flex flex-col gap-3">
        <PrimaryButton onClick={retry}>다시 검사하기</PrimaryButton>
        <SecondaryButton to="/">처음으로</SecondaryButton>
        <p className="mt-2 text-center text-xs leading-relaxed text-ink-faint">
          추천 결과는 국민건강영양조사 자료를 바탕으로 한 참고용이며 의료적 진단이나 처방을 대체하지 않습니다.
        </p>
      </footer>
    </main>
  )
}
