import { useMemo } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import GroupChip from '../components/GroupChip.jsx'
import Icon from '../components/Icon.jsx'
import Mascot from '../components/Mascot.jsx'
import PrimaryButton, { SecondaryButton } from '../components/PrimaryButton.jsx'
import { FACTS, surveyFact } from '../lib/surveyStats.js'
import Card from '../components/result/Card.jsx'
import HabitTabs from '../components/result/HabitTabs.jsx'
import MissionList from '../components/result/MissionList.jsx'
import AboutLink from '../components/result/AboutLink.jsx'
import PartnerCard from '../components/result/PartnerCard.jsx'
import ShareButton from '../components/result/ShareButton.jsx'
import ShareImageButton from '../components/result/ShareImageButton.jsx'
import TypeBoundary from '../components/result/TypeBoundary.jsx'
import TypeNutrients from '../components/result/TypeNutrients.jsx'
import { buildTypeResult } from '../lib/result.js'
import { clearSurvey, loadSurvey } from '../lib/storage.js'

// 1단계 유형 결과 (공유용). 보여 줄 값은 lib/result.js의 buildTypeResult가 계산한다
// 첫 화면은 유형 카드만 (마스코트·이름·해시태그·한 줄 설명·비율), 내리면 생활습관(내 신호등 / 평균과 비교)·이번 주 해볼 것
//   → 내 유형 위치(경계) → 부족할 수 있는 영양소 → 짝꿍 유형
// '공유'와 '나에게 맞는 결과'는 맨 아래 (다시 검사하기 위)
const PENDING = '영양 분석 결과가 준비되면 이곳에 표시돼요.'

function useResult() {
  return useMemo(() => {
    const { answers, done } = loadSurvey()
    return done[1] ? { ...buildTypeResult(answers), personalDone: done[2], peerFacts: Object.keys(FACTS).map((id) => surveyFact(id, answers)).filter(Boolean) } : null
  }, [])
}

export default function ResultPage() {
  const navigate = useNavigate()
  const r = useResult()
  if (!r) return <Navigate to="/survey" replace />

  const retry = () => {
    // 응답을 지우고 시작 화면으로 (다시 시작할지는 사용자가 고른다)
    clearSurvey()
    navigate('/')
  }

  return (
    <main className="flex flex-1 flex-col gap-4 px-5 pt-8 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <header className="flex min-h-[calc(100dvh-4rem)] flex-col items-center justify-center text-center">
        <p className="mt-auto text-sm font-semibold text-ink-soft">나의 NBTI 유형은</p>
        <Mascot name={`type_${r.leafId}`} className="mt-3" />
        <GroupChip code={r.leafId[0]} name={r.mainType.name} className="mt-3" />
        <h1 className="mt-2 font-display text-[1.75rem] leading-tight font-normal">{r.name}</h1>
        <p className="mt-4 max-w-80 leading-relaxed whitespace-pre-line text-ink-soft">{r.summary}</p>
        {r.tags.length > 0 && (
          <ul className="mt-3 flex flex-wrap justify-center gap-1.5">
            {r.tags.map((tag) => (
              <li key={tag} className="rounded-full bg-white px-3 py-1 text-sm font-bold text-primary-shade shadow-soft">
                {tag}
              </li>
            ))}
          </ul>
        )}
        <p className="mt-3 text-sm text-ink-soft">
          조사 자료에서 성인 100명 중 약 <b className="text-primary-shade">{Math.round(r.sharePct)}명</b>이 이 유형이에요
        </p>
        <PrimaryButton to={r.personalDone ? '/result2' : '/survey2'} size="sm" className="mt-5">
          {r.personalDone ? '내 식사 결과 다시 보기' : '식사 설문하고 내 영양소 보기'}
        </PrimaryButton>
        {/* 누르면 첫 카드(생활습관 신호등)로 내려간다 */}
        <button
          type="button"
          onClick={(e) => e.currentTarget.closest('header').nextElementSibling?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
          className="mt-auto animate-bounce px-4 pt-6 pb-2 text-sm font-semibold text-ink-faint motion-reduce:animate-none"
        >
          <span className="inline-flex items-center gap-1">
            자세히 보기 <Icon name="down" size={16} />
          </span>
        </button>
      </header>

      <Card title="나의 생활습관" icon="traffic">
        <HabitTabs habits={r.habits} code={r.leafId[0]} />
        {r.peerFacts.length > 0 && <details className="mt-3 text-sm text-ink-soft">
          <summary className="cursor-pointer py-2 font-bold">같은 성별·나이대의 조사 통계</summary>
          <ul className="space-y-2">{r.peerFacts.map((f) => <li key={f.label}>{f.lead} 약 {f.pct}{f.tail}.</li>)}</ul>
          <p className="mt-2 text-xs">국민건강영양조사 2022–2024 가중 비율을 약 5% 단위로 표시했어요.</p>
        </details>}
        <h3 className="mt-5 mb-2 flex items-center gap-1.5 text-sm font-bold">
          <Icon name="target" size={18} className="text-primary-shade" />
          이번 주 해볼 것
        </h3>
        <MissionList missions={r.missions} />
      </Card>

      <Card title="내 유형 위치" icon="compass">
        <TypeBoundary leafId={r.leafId} name={r.name} boundary={r.boundary} />
      </Card>

      <Card title="부족할 수 있는 영양소" icon="apple">
        {r.nutrients ? (
          <TypeNutrients
            common={r.nutrients.common}
            picks={r.nutrients.picks}
            sexLabel={r.sexLabel}
            ageLabel={r.ageLabel}
          />
        ) : (
          <p className="text-sm text-ink-faint">{PENDING}</p>
        )}
      </Card>

      <Card title="다른 유형 둘러보기" icon="users">
        <details>
          <summary className="cursor-pointer py-2 text-sm font-bold">내 습관과 비교할 유형</summary>
          <PartnerCard fill={r.partners.fill} together={r.partners.together} />
        </details>
        <Link to="/types" className="mt-3 block py-2 text-center text-sm font-bold text-primary-shade">
          12가지 유형 모두 보기 ›
        </Link>
      </Card>

      <footer className="mt-2 flex flex-col gap-3">
        {/* 공유 + 2단계 개인 결과 (화면 맨 아래, 고정하지 않음) */}
        <div className="relative grid grid-cols-2 gap-2">
          <ShareButton typeName={r.name} className="py-3.5" />
          <ShareImageButton r={r} className="py-3.5" />
        </div>
        <SecondaryButton onClick={retry}>처음부터 다시 검사하기</SecondaryButton>
        <AboutLink />
      </footer>
    </main>
  )
}
