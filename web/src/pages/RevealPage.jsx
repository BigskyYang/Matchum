import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import GroupChip, { GroupDot } from '../components/GroupChip.jsx'
import Icon from '../components/Icon.jsx'
import Mascot from '../components/Mascot.jsx'
import { model } from '../lib/classify.js'
import { buildTypeResult, revealStory } from '../lib/result.js'
import { loadSurvey } from '../lib/storage.js'
import NutrientArt from '../components/NutrientArt.jsx'

// 결과 공개 (/reveal): 1단계 설문이 끝나면 '분석 중' → 유형 공개 스토리 카드 6장 → 자세한 유형 결과(/result)
//   카드: 유형 공개 · 100명 중 N명 · 잘 챙기는/챙겨 볼 습관 · 같은 유형의 섭취 경향. 마지막 카드에서 한 번 더 넘기면 유형 결과(공유는 거기서)
//   넘기기: 옆으로 밀기(스와이프) 또는 화면 오른쪽 2/3 누르기 = 다음, 왼쪽 1/3 = 이전, 키보드 ←·→
//   카드를 모두 보게 한다: '건너뛰기'·'다음' 버튼·첫 카드의 식사 설문 버튼은 두지 않는다
//   화면 읽기 프로그램용 이전·다음 버튼은 눈에 보이지 않게 두고, 키보드로 가면 보인다
//   '동작 줄이기'를 켠 사용자에게는 움직임 없이 바로 보여 준다
//   마스코트: 분석 중 analyzing → 마지막 줄('찾았어요')에서 surprise, 마무리 카드 cheer (그림이 없으면 thinking·happy)
const reducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
const SAMPLE = model.population.n.toLocaleString('ko-KR')
const LINES = ['생활습관 응답을 정리하고 있어요', `국민건강영양조사 성인 ${SAMPLE}명과 비교하고 있어요`, '가장 가까운 유형을 찾았어요']
const ANALYZE_MS = 2400

const COLS = { 2: 'grid-cols-2', 3: 'grid-cols-3' }

// '철을' / '마그네슘을' / '비타민 B1을' (숫자·영문으로 끝나면 읽는 소리로)
const eulReul = (word) => {
  const code = word.charCodeAt(word.length - 1) - 0xac00
  const final = code >= 0 && code <= 11171 ? code % 28 !== 0 : /[136780LMNR]$/i.test(word)
  return final ? '을' : '를'
}

// 10명 중 N명: 회색 점 10개 위에 색 점이 하나씩 차례로 채워진다 (동작 줄이기를 켜면 바로 채워진 채로)
const FILL_START = 300
const FILL_STEP = 130
function FillDots({ count, code, delay = FILL_START, size, gap }) {
  return (
    <span aria-hidden="true" className={`grid grid-cols-10 ${gap}`}>
      {Array.from({ length: 10 }, (_, i) => (
        <span key={i} className={`relative ${size} rounded-full bg-ink/10`}>
          {i < count && (
            <GroupDot
              code={code}
              className="absolute inset-0 size-full animate-pop motion-reduce:animate-none"
              style={{ animationDelay: `${delay + i * FILL_STEP}ms` }}
            />
          )}
        </span>
      ))}
    </span>
  )
}

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
        <Title>대체로 섭취가 부족했던 영양소</Title>
        <p className="mt-2 text-ink-soft">유형과 상관없이 성인 절반 이상이 적게 먹어요</p>
        <ul className="mt-6 grid w-full grid-cols-3 gap-2">
          {s.nutrient.items.map((n) => (
            <li key={n.key} className="flex flex-col items-center gap-1.5 rounded-card bg-white px-2 py-4 text-sm font-bold shadow-soft">
              <NutrientArt n={n} className="size-12 animate-pop motion-reduce:animate-none" emojiClass="text-3xl" />
              {n.label}
            </li>
          ))}
        </ul>
      </>
    ) : (
      <>
        <Title>같은 유형의 섭취 경향</Title>
        {/* 영양소마다: 그림 → '마그네슘을 적게 먹어요' → 점 10개가 차례로 채워짐 → 10명 중 N명 */}
        <ul className={`mt-6 grid w-full gap-2 ${COLS[s.nutrient.items.length] ?? ''}`}>
          {s.nutrient.items.map((n, i) => {
            const one = s.nutrient.items.length === 1
            const delay = FILL_START + i * FILL_STEP * 3 // 여러 개면 칸마다 조금씩 늦게 시작
            return (
              <li key={n.key} className={`flex flex-col items-center rounded-card bg-white shadow-soft ${one ? 'px-6 py-6' : 'px-2 py-4'}`}>
                <NutrientArt
                  n={n}
                  className={`animate-pop motion-reduce:animate-none ${one ? 'size-24' : 'size-14'}`}
                  emojiClass={one ? 'text-5xl' : 'text-3xl'}
                />
                <p className={`mt-2 text-center leading-tight ${one ? 'text-xl' : 'text-sm'}`}>
                  <span className="whitespace-nowrap">
                    <b className={`font-display font-normal ${one ? 'text-3xl' : 'text-lg'}`}>{n.label}</b>
                    {eulReul(n.label)}
                  </span>{' '}
                  <span className="whitespace-nowrap font-bold text-ink-soft">적게 먹어요</span>
                </p>
                <div className={one ? 'mt-4' : 'mt-3'}>
                  <FillDots count={n.of10} code={code} delay={delay} size={one ? 'size-4' : 'size-1.5'} gap={one ? 'gap-1.5' : 'gap-1'} />
                </div>
                <p
                  className={`animate-rise font-bold motion-reduce:animate-none ${one ? 'mt-3 text-xl' : 'mt-2 text-sm'}`}
                  style={{ animationDelay: `${delay + n.of10 * FILL_STEP}ms` }}
                >
                  10명 중 <span className="text-primary-shade">{n.of10}명</span>
                </p>
              </li>
            )
          })}
        </ul>
      </>
    ),
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
  const toResult = useCallback(() => navigate('/result', { replace: true }), [navigate])
  // 마지막 카드에서 다음으로 넘기면 유형 결과로
  const go = useCallback((d) => (card + d > last ? toResult() : setCard(Math.max(card + d, 0))), [card, last, toResult])
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

  // 화면 왼쪽 1/3을 누르면 이전, 나머지는 다음 (마지막 카드에서 다음 = 유형 결과)
  const onTap = (e) => {
    if (touch.current?.swiped) {
      touch.current = null
      return
    }
    const { left, width } = e.currentTarget.getBoundingClientRect()
    if (e.clientX - left < width / 3) go(-1)
    else go(1)
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

      <footer className="flex items-center justify-center gap-2 py-3 text-sm text-ink-faint">
        {card > 0 && (
          <button type="button" onClick={() => go(-1)} className="sr-only rounded-button bg-white px-4 py-2 text-ink-soft focus:not-sr-only">
            이전 카드
          </button>
        )}
        <span aria-hidden="true">{card < last ? '‹ 옆으로 넘겨 보세요 ›' : '옆으로 넘기면 자세한 결과를 볼 수 있어요 ›'}</span>
        <button type="button" onClick={() => go(1)} className="sr-only rounded-button bg-white px-4 py-2 text-ink-soft focus:not-sr-only">
          {card < last ? '다음 카드' : '자세한 결과 보기'}
        </button>
      </footer>
    </main>
  )
}
