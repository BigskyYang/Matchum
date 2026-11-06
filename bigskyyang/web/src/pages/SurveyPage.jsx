import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import BottomSheet from '../components/BottomSheet.jsx'
import Icon from '../components/Icon.jsx'
import Mascot from '../components/Mascot.jsx'
import PrimaryButton from '../components/PrimaryButton.jsx'
import ChoiceInput from '../components/survey/ChoiceInput.jsx'
import ProgressBar from '../components/survey/ProgressBar.jsx'
import RowsInput from '../components/survey/RowsInput.jsx'
import PeerFactToast from '../components/survey/PeerFactToast.jsx'
import { DateWheel, DurationWheel, NumberWheel, TimeWheel } from '../components/survey/WheelInputs.jsx'
import { SECTIONS, visibleQuestions } from '../data/questions.js'
import { loadSurvey, saveSurvey } from '../lib/storage.js'
import { recordAnswer, resolveStep, resultPath, surveyPath } from '../lib/surveyFlow.js'
import { SKIP } from '../lib/vitaminD.js'
import { surveyFact } from '../lib/surveyStats.js'

function QuestionStep({ q, answer, answers, isLast, onAnswer, onSkip }) {
  // 휠 입력은 이전 응답이 있으면 그 값, 없으면 문항의 initial 값에서 시작. 여러 줄 선택은 빈 값에서 시작
  const [draft, setDraft] = useState(() => answer ?? q.initial ?? (q.type === 'rows' ? {} : undefined))
  // check: 다음으로 넘어갈 수 없는 값이면 안내 문구 (예: 만 19세 미만)
  const error = q.check?.(draft, answers) ?? null
  const ready = (q.type !== 'rows' || q.rows.every((row) => draft[row.id] !== undefined)) && !error
  const [info, setInfo] = useState(false)

  return (
    <>
      <section className="flex-1">
        {q.period && (
          <p className="mb-2 inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-xs font-bold text-ink-soft shadow-soft">
            <Icon name="calendar" size={14} /> {q.period} 기준
          </p>
        )}
        <h1 className="text-xl leading-snug font-bold">{q.title}</h1>
        {(q.note || q.info) && (
          <p className="mt-1.5 flex flex-wrap items-center gap-x-2 text-sm text-ink-soft">
            {q.note}
            {q.info && (
              <button type="button" onClick={() => setInfo(true)} className="py-1.5 font-semibold text-primary-shade">
                <span className="inline-flex items-center gap-1">
                  <Icon name="info" size={16} /> 자세히
                </span>
              </button>
            )}
          </p>
        )}
        {info && (
          <BottomSheet title="도움말" onClose={() => setInfo(false)}>
            <ul className="space-y-2">
              {q.info.map((line) => (
                <li key={line} className="rounded-card bg-cream px-4 py-3 text-sm leading-relaxed">
                  {line}
                </li>
              ))}
            </ul>
          </BottomSheet>
        )}

        <div className="mt-6">
          {q.type === 'choice' && <ChoiceInput options={q.options} value={answer} onSelect={onAnswer} layout={q.layout} />}
          {q.optional && onSkip && (
            <button type="button" onClick={onSkip} className="mt-3 w-full py-3 text-center text-sm font-semibold text-ink-soft underline decoration-ink/20 underline-offset-4">
              {SECTIONS[q.section]} 문항 건너뛰고 결과 보기
            </button>
          )}
          {q.type === 'rows' && <RowsInput rows={q.rows} options={q.options} value={draft} onChange={setDraft} />}
          {q.type === 'number' && <NumberWheel value={draft} onChange={setDraft} unit={q.unit} min={q.min} max={q.max} />}
          {q.type === 'time' && <TimeWheel value={draft} onChange={setDraft} hourStart={q.hourStart} />}
          {q.type === 'duration' && <DurationWheel value={draft} onChange={setDraft} per={q.per} maxHours={q.maxHours} />}
          {q.type === 'date' && <DateWheel value={draft} onChange={setDraft} minYear={q.minYear} maxYear={q.maxYear} />}
          {error && draft && (
            <p role="alert" className="mt-3 text-center text-sm font-semibold text-primary-shade">
              {error}
            </p>
          )}
        </div>
      </section>

      {q.type !== 'choice' && (
        <footer className="mt-8">
          <PrimaryButton onClick={() => onAnswer(draft)} disabled={!ready}>
            {isLast ? '결과 보기' : '다음'}
          </PrimaryButton>
        </footer>
      )}
    </>
  )
}

// 문항마다 주소(/survey?q=문항ID, 2단계는 /survey2?q=)를 하나씩 쌓아서, 휴대폰의 뒤로·앞으로 가기로 문항을 오갈 수 있다
// stage 1: 유형 분류 문항 → /result, stage 2: 개인 결과 문항 → /result2 (1단계 응답을 이어 쓴다)
export default function SurveyPage({ stage = 1 }) {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [state, setState] = useState(loadSurvey)
  const busy = useRef(false)
  const timer = useRef(null)
  // 방금 답한 문항의 같은 성별·나이대 통계 (다음 문항 화면 아래에서 잠깐 보여 준다)
  const [fact, setFact] = useState(null)
  const hideFact = useCallback(() => setFact(null), [])

  const list = visibleQuestions(state.answers, stage)
  const step = resolveStep(list, state.answers, params.get('q'), state.step[stage])
  const q = list[step]

  useEffect(() => () => { clearTimeout(timer.current); busy.current = false }, [q.id])

  // 응답과 지금 위치를 저장해 새로고침해도 이어서 할 수 있게 한다
  useEffect(() => saveSurvey({ ...state, step: { ...state.step, [stage]: step } }), [state, step, stage])

  // 주소를 지금 문항에 맞춘다 (처음 들어왔거나, 답하지 않은 문항으로 건너뛰려 한 경우)
  useEffect(() => {
    if (params.get('q') !== q.id) navigate(surveyPath(q, stage), { replace: true })
    window.scrollTo(0, 0)
  }, [q, params, navigate, stage])
  // 진행: 영역(기본정보·신체활동·수면 …)마다 한 칸, 지금 영역 안에서 몇 번째인지
  const sections = [...new Set(list.map((x) => x.section))]
  const inSection = list.filter((x) => x.section === q.section)
  const position = inSection.indexOf(q) + 1
  const percent = Math.round((step / list.length) * 100)

  const answer = (value) => {
    if (busy.current) return
    const updated = recordAnswer(state, stage, q, value)
    const next = visibleQuestions(updated.answers, stage)
    const last = next.at(-1).id === q.id && updated.done[stage]
    const go = () => {
      busy.current = false
      saveSurvey(updated)
      setState(updated)
      const f = last ? null : surveyFact(q.id, updated.answers)
      setFact(f && { ...f, id: `${q.id}-${Date.now()}` })
      navigate(last ? resultPath(stage) : surveyPath(next[updated.step[stage]], stage))
    }
    // 보기를 누른 경우 선택 표시가 잠깐 보이도록 조금 늦게 넘어간다
    if (q.type === 'choice') {
      busy.current = true
      setState((s) => ({ ...s, answers: updated.answers, done: updated.done }))
      timer.current = setTimeout(go, 180)
    } else {
      go()
    }
  }

  // 선택 문항(비타민 D): 지금 문항부터 남은 선택 문항을 모두 '건너뛰기'로 기록하고 결과로
  const skipRest = () => {
    if (busy.current) return
    let updated = state
    for (const x of list.slice(step)) {
      if (x.optional && updated.answers[x.id] == null) updated = recordAnswer(updated, stage, x, SKIP)
    }
    saveSurvey(updated)
    setState(updated)
    navigate(updated.done[stage] ? resultPath(stage) : surveyPath(visibleQuestions(updated.answers, stage)[updated.step[stage]], stage))
  }

  // 화면의 ‹ 버튼은 휴대폰 뒤로 가기와 똑같이 동작한다.
  // 이 사이트 안에서 쌓인 기록이 없으면(주소로 바로 들어온 경우) 이전 문항이나 시작 화면으로 간다
  const back = () => {
    if ((window.history.state?.idx ?? 0) > 0) navigate(-1)
    else if (step > 0) navigate(surveyPath(list[step - 1], stage), { replace: true })
    else navigate(stage === 2 ? '/result' : '/')
  }

  return (
    <main className="flex flex-1 flex-col px-6 pt-4 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <header className="flex items-center gap-3">
        <button
          type="button"
          onClick={back}
          aria-label="이전 문항"
          className="-ml-2 flex size-10 items-center justify-center rounded-full text-2xl text-ink-soft active:bg-primary-soft"
        >
          <Icon name="back" size={26} />
        </button>
        <div className="flex-1">
          <div className="mb-1.5 flex justify-between text-xs font-semibold text-ink-soft">
            <span>
              <b className="mr-1.5 text-primary-shade">{stage === 1 ? '유형 설문' : '개인 식사 설문'}</b>
              {SECTIONS[q.section]}
            </span>
            <span className="text-primary-shade" aria-label={`이 단계 예상 ${list.length}문항 중 ${step + 1}번째`}>
              {step + 1} / {list.length}
            </span>
          </div>
          <ProgressBar
            percent={percent}
            sections={sections.length}
            current={sections.indexOf(q.section)}
            fraction={position / inSection.length}
          />
        </div>
      </header>

      <div className="mt-4 flex justify-center"><Mascot name="thinking" size="sm" /></div>

      <div className="mt-4 flex flex-1 flex-col">
        <QuestionStep
          key={q.id}
          q={q}
          answers={state.answers}
          answer={state.answers[q.id]}
          isLast={step === list.length - 1}
          onAnswer={answer}
          onSkip={skipRest}
        />
      </div>
      {fact && <PeerFactToast key={fact.id} fact={fact} onDone={hideFact} raised={q.type !== 'choice'} />}
    </main>
  )
}
