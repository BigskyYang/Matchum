import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import GroupChip, { GroupDot } from '../components/GroupChip.jsx'
import Icon from '../components/Icon.jsx'
import Mascot from '../components/Mascot.jsx'
import PrimaryButton, { SecondaryButton } from '../components/PrimaryButton.jsx'
import ShareButton from '../components/result/ShareButton.jsx'
import ShareImageButton from '../components/result/ShareImageButton.jsx'
import { model } from '../lib/classify.js'
import { buildTypeResult, revealStory } from '../lib/result.js'
import { loadSurvey } from '../lib/storage.js'
import NutrientArt from '../components/NutrientArt.jsx'

// 결과 공개 (/reveal): 1단계 설문이 끝나면 '분석 중' → 유형 공개 스토리 카드 6장 → 자세한 유형 결과(/result)
//   카드: 유형 공개 · 100명 중 N명 · 잘 챙기는/챙겨 볼 습관 · 챙길 영양소 · 짝꿍 · 마무리(공유)
//   넘기기: 옆으로 밀기(스와이프) 또는 화면 오른쪽 2/3 누르기 = 다음, 왼쪽 1/3 = 이전, 키보드 ←·→
//   카드를 모두 보게 한다: '건너뛰기'·'다음' 버튼·첫 카드의 식사 설문 버튼은 두지 않는다
//   화면 읽기 프로그램용 이전·다음 버튼은 눈에 보이지 않게 두고, 키보드로 가면 보인다
//   '동작 줄이기'를 켠 사용자에게는 움직임 없이 바로 보여 준다
//   마스코트: 분석 중 analyzing → 마지막 줄('찾았어요')에서 surprise, 마무리 카드 cheer (그림이 없으면 thinking·happy)
const reducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
const SAMPLE = model.population.n.toLocaleString('ko-KR')
const LINES = ['생활습관 응답을 정리하고 있어요', `국민건강영양조사 성인 ${SAMPLE}명과 비교하고 있어요`, '가장 가까운 유형을 찾았어요']
const ANALYZE_MS = 2400

// 영양소 카드의 이유 표시 (lib/result.js revealStory의 reason)
const REASON = { type: '내 유형에서', peer: '내 성별·나이대에서' }
const COLS = { 2: 'grid-cols-2', 3: 'grid-cols-3' }

function Dots({ count, total, code, size = 'size-3.5' }) {
  return (
    <span aria-hidden="true" className="grid grid-cols-10 gap-1.5">
      {Array.from({ length: total }, (_, i) =>
        i < count ? (
          <GroupDot key={i} code={code} className={`${size} animate-pop motion-reduce:animate-none`} style={{ animationDelay: `${i * 15}ms` }} />
        ) : (
          <span key={i} className={`${size} rounded-full bg-ink/10`} />
        ),
      )}
    </span>
  )
}

function HabitChips({ habits, tone }) {
  return (
    <ul className="flex flex-wrap justify-center gap-2">
      {habits.map((h) => (
        <li key={h.key} className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-2 font-bold ${tone}`}>
          <Icon name={h.icon} size={20} />
          {h.label}
        </li>
      ))}
    </ul>
  )
}

const Title = ({ children }) => <h2 className="font-display text-[1.75rem] leading-tight font-normal">{children}</h2>

function cardsOf(r, s) {
  const code = r.leafId[0]
  return [
    // 1. 유형 공개
    <>
      <p className="text-sm font-semibold text-ink-soft">나의 NBTI 유형은</p>
      <Mascot name={`type_${r.leafId}`} className="mt-2 animate-pop motion-reduce:animate-none" />
      <GroupChip code={code} name={r.mainType.name} className="mt-2" />
      <h1 className="mt-2 font-display text-[1.75rem] leading-tight font-normal">{r.name}</h1>
      <p className="mt-2 text-sm text-ink-soft">{r.summary}</p>
      <ul className="mt-3 flex flex-wrap justify-center gap-1.5">
        {r.tags.map((tag) => (
          <li key={tag} className="rounded-full bg-white px-3 py-1 text-sm font-bold text-primary-shade shadow-soft">
            {tag}
          </li>
        ))}
      </ul>
    </>,
    // 2. 비율
    <>
      <Title>
        조사 자료에서 성인 100명 중 약 <span className="text-primary-shade">{s.share}명</span>
      </Title>
      <p className="mt-2 text-ink-soft">나와 같은 유형이에요</p>
      <div className="mt-6">
        <Dots count={s.share} total={100} code={code} />
      </div>

    </>,
    // 3. 습관
    <>
      <Title>내 생활습관을 보면</Title>
      <div className="mt-6 grid w-full gap-5">
        <div>
          <p className="mb-2 text-sm font-bold text-ink-soft">잘 챙기고 있어요</p>
          {s.strong.length ? (
            <HabitChips habits={s.strong} tone="bg-mint text-ink" />
          ) : (
            <p className="text-sm text-ink-soft">아직 &lsquo;좋아요&rsquo;인 습관은 없어요</p>
          )}
        </div>
        <div>
          <p className="mb-2 text-sm font-bold text-ink-soft">챙겨 볼 습관</p>
          {s.weak.length ? (
            <HabitChips habits={s.weak} tone="bg-primary-soft text-primary-shade" />
          ) : (
            <p className="text-sm text-ink-soft">모든 습관이 &lsquo;좋아요&rsquo;예요</p>
          )}
        </div>
      </div>
      {s.mission && (
        <p className="mt-6 inline-flex items-center gap-1.5 rounded-card bg-white px-4 py-3 font-bold shadow-soft">
          <Icon name={s.mission.icon} size={20} className="text-primary-shade" />
          이번 주에는 &lsquo;{s.mission.title}&rsquo;부터
        </p>
      )}
    </>,
    // 4. 영양소
    s.nutrient.kind === 'common' ? (
      <>
        <Title>조사에서 섭취가 적었던 영양소</Title>
        <p className="mt-2 text-ink-soft">유형과 상관없이 성인 절반 이상이 적게 먹어요</p>
        <ul className="mt-6 flex flex-wrap justify-center gap-2">
          {s.nutrient.items.map((n) => (
            <li key={n.key} className="inline-flex items-center gap-1.5 rounded-full bg-white px-4 py-2 font-bold shadow-soft">
              <NutrientArt n={n} className="size-7" />
              {n.label}
            </li>
          ))}
        </ul>
      </>
    ) : (
      <>
        <Title>
          같은 유형·성별·나이대의
          <br />
          섭취 경향
        </Title>
        {/* 영양소마다: 이유(내 유형에서 / 내 성별·나이대에서) → 그림 → 이름 → 적게 먹어요 → 10명 중 N명 */}
        <ul className={`mt-6 grid w-full gap-2 ${COLS[s.nutrient.items.length] ?? ''}`}>
          {s.nutrient.items.map((n) => {
            const one = s.nutrient.items.length === 1
            return (
              <li key={n.key} className={`flex flex-col items-center rounded-card bg-white shadow-soft ${one ? 'px-6 py-6' : 'px-2 py-4'}`}>
                <span className={`flex items-center rounded-full px-2.5 py-0.5 text-center text-xs leading-tight font-bold ${one ? '' : 'min-h-[2.6em]'} ${n.reason === 'type' ? 'bg-primary-soft text-primary-shade' : 'bg-cream text-ink-soft'}`}>
                  {REASON[n.reason]}
                </span>
                <NutrientArt
                  n={n}
                  className={`mt-3 animate-pop motion-reduce:animate-none ${one ? 'size-24' : 'size-14'}`}
                  emojiClass={one ? 'mt-3 text-5xl' : 'mt-3 text-3xl'}
                />
                <p className={`mt-2 font-display leading-tight font-normal ${one ? 'text-3xl' : 'text-lg'}`}>{n.label}</p>
                <p className={`mt-0.5 font-bold text-ink-soft ${one ? 'text-base' : 'text-sm'}`}>적게 먹어요</p>
                <p className={`mt-2 font-bold ${one ? 'text-xl' : 'text-sm'}`}>
                  10명 중 <span className="text-primary-shade">{n.of10}명</span>
                </p>
                {one && (
                  <div className="mt-3">
                    <Dots count={n.of10} total={10} code={code} size="size-4" />
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      </>
    ),
    // 6. 마무리
    <>
      <Mascot name="cheer" fallback="happy" className="animate-pop motion-reduce:animate-none" />
      <Title>나의 유형을 확인했어요</Title>
      <p className="mt-2 text-ink-soft">자세한 결과와 나에게 맞는 영양 정보도 볼 수 있어요</p>
    </>,
  ]
}

function Analyzing() {
  const [line, setLine] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setLine((l) => Math.min(l + 1, LINES.length - 1)), ANALYZE_MS / LINES.length)
    return () => clearInterval(id)
  }, [])
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 text-center">
      {line < LINES.length - 1 ? (
        <Mascot key="analyzing" name="analyzing" fallback="thinking" float />
      ) : (
        <Mascot key="surprise" name="surprise" fallback="happy" className="animate-pop motion-reduce:animate-none" />
      )}
      <p key={line} aria-live="polite" className="mt-4 animate-rise font-display text-xl font-normal motion-reduce:animate-none">
        {LINES[line]}
      </p>
      <span aria-hidden="true" className="mt-4 flex gap-1.5">
        {LINES.map((l, i) => (
          <span key={l} className={`size-2 rounded-full transition-colors ${i <= line ? 'bg-primary-strong' : 'bg-ink/10'}`} />
        ))}
      </span>
    </main>
  )
}

export default function RevealPage() {
  const navigate = useNavigate()
  const survey = useMemo(() => loadSurvey(), [])
  const r = useMemo(() => (survey.done[1] ? buildTypeResult(survey.answers) : null), [survey])
  const [phase, setPhase] = useState(() => (reducedMotion() ? 'story' : 'analyzing'))
  const [card, setCard] = useState(0)
  const cards = useMemo(() => (r ? cardsOf(r, revealStory(r)) : []), [r])
  const last = cards.length - 1
  const go = useCallback((d) => setCard((c) => Math.min(Math.max(c + d, 0), last)), [last])
  const toResult = useCallback(() => navigate('/result', { replace: true }), [navigate])
  const touch = useRef(null) // 밀기 시작점 { x, y }, 밀어서 넘겼으면 swiped

  useEffect(() => {
    if (phase !== 'analyzing') return undefined
    const id = setTimeout(() => setPhase('story'), ANALYZE_MS)
    return () => clearTimeout(id)
  }, [phase])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'ArrowRight') go(1)
      if (e.key === 'ArrowLeft') go(-1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [go])

  if (!r) return <Navigate to="/survey" replace />
  if (phase === 'analyzing') return <Analyzing />

  // 옆으로 50px 넘게 밀면 넘긴다 (세로로 더 많이 움직였으면 스크롤로 보고 넘기지 않는다)
  const SWIPE = 50
  const onTouchStart = (e) => {
    const t = e.touches[0]
    touch.current = { x: t.clientX, y: t.clientY, swiped: false }
  }
  const onTouchEnd = (e) => {
    const start = touch.current
    if (!start) return
    const t = e.changedTouches[0]
    const dx = t.clientX - start.x
    const dy = t.clientY - start.y
    if (Math.abs(dx) >= SWIPE && Math.abs(dx) > Math.abs(dy)) {
      start.swiped = true
      go(dx < 0 ? 1 : -1)
      // 밀고 난 뒤 따라오는 click만 무시한다 (잠시 뒤 표시를 지운다)
      setTimeout(() => {
        if (touch.current === start) touch.current = null
      }, 400)
    }
  }

  // 화면 왼쪽 1/3을 누르면 이전, 나머지는 다음 (마지막 카드에서는 넘기지 않는다)
  const onTap = (e) => {
    if (touch.current?.swiped) {
      touch.current = null
      return
    }
    const { left, width } = e.currentTarget.getBoundingClientRect()
    if (e.clientX - left < width / 3) go(-1)
    else if (card < last) go(1)
  }

  return (
    <main className="flex flex-1 flex-col px-5 pt-4 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <header className="flex items-center gap-3">
        <div aria-hidden="true" className="flex flex-1 gap-1">
          {cards.map((_, i) => (
            <span key={i} className="h-1 flex-1 overflow-hidden rounded-full bg-ink/10">
              <span className={`block h-full rounded-full bg-primary-strong transition-[width] duration-300 ${i <= card ? 'w-full' : 'w-0'}`} />
            </span>
          ))}
        </div>
      </header>
      <p className="sr-only" aria-live="polite">
        {cards.length}장 중 {card + 1}번째
      </p>

      {/* 밀기·누르기는 손가락용. 키보드는 ←·→ 또는 아래 숨은 이전·다음 버튼 */}
      <section
        key={card}
        onClick={onTap}
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
        className="flex flex-1 animate-rise cursor-pointer flex-col items-center justify-center py-6 text-center select-none motion-reduce:animate-none"
      >
        {cards[card]}
      </section>

      <footer className="grid gap-2">
        {card < last ? (
          <div className="flex items-center justify-center gap-2 py-3 text-sm text-ink-faint">
            {card > 0 && (
              <button type="button" onClick={() => go(-1)} className="sr-only rounded-button bg-white px-4 py-2 text-ink-soft focus:not-sr-only">
                이전 카드
              </button>
            )}
            <span aria-hidden="true">‹ 옆으로 넘겨 보세요 ›</span>
            <button type="button" onClick={() => go(1)} className="sr-only rounded-button bg-white px-4 py-2 text-ink-soft focus:not-sr-only">
              다음 카드
            </button>
          </div>
        ) : (
          <>
            <div className="relative grid grid-cols-2 gap-2">
              <ShareButton typeName={r.name} className="py-3.5" />
              <ShareImageButton r={r} className="py-3.5" />
            </div>
            <PrimaryButton size="sm" onClick={toResult}>
              결과 자세히 보기
            </PrimaryButton>
            <SecondaryButton to={survey.done[2] ? '/result2' : '/survey2'}>내 식사 결과 살펴보기</SecondaryButton>
          </>
        )}
      </footer>
    </main>
  )
}
