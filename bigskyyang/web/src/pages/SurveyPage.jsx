import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import Mascot from '../components/Mascot.jsx'
import PrimaryButton from '../components/PrimaryButton.jsx'
import ChoiceInput from '../components/survey/ChoiceInput.jsx'
import ProgressBar from '../components/survey/ProgressBar.jsx'
import RowsInput from '../components/survey/RowsInput.jsx'
import { DateWheel, DurationWheel, NumberWheel, TimeWheel } from '../components/survey/WheelInputs.jsx'
import { SECTIONS, visibleQuestions } from '../data/questions.js'
import { loadSurvey, saveSurvey } from '../lib/storage.js'
import { resolveStep, resultPath, surveyPath } from '../lib/surveyFlow.js'

function QuestionStep({ q, answer, isLast, onAnswer }) {
  // 휠 입력은 이전 응답이 있으면 그 값, 없으면 문항의 initial 값에서 시작. 여러 줄 선택은 빈 값에서 시작
  const [draft, setDraft] = useState(() => answer ?? q.initial ?? (q.type === 'rows' ? {} : undefined))
  // check: 다음으로 넘어갈 수 없는 값이면 안내 문구 (예: 만 19세 미만)
  const error = q.check?.(draft) ?? null
  const ready = (q.type !== 'rows' || q.rows.every((row) => draft[row.id] !== undefined)) && !error

  return (
    <>
      <section className="flex-1">
        <h1 className="text-xl leading-snug font-bold">{q.title}</h1>
        {q.help && (
          <ul className="mt-3 space-y-1 text-sm leading-relaxed text-ink-soft">
            {q.help.map((line) => (
              <li key={line}>※ {line}</li>
            ))}
          </ul>
        )}

        <div className="mt-6">
          {q.type === 'choice' && <ChoiceInput options={q.options} value={answer} onSelect={onAnswer} layout={q.layout} />}
          {q.type === 'rows' && <RowsInput rows={q.rows} options={q.options} value={draft} onChange={setDraft} />}
          {q.type === 'number' && <NumberWheel value={draft} onChange={setDraft} unit={q.unit} min={q.min} max={q.max} />}
          {q.type === 'time' && <TimeWheel value={draft} onChange={setDraft} hourStart={q.hourStart} />}
          {q.type === 'duration' && <DurationWheel value={draft} onChange={setDraft} per={q.per} maxHours={q.maxHours} />}
          {q.type === 'date' && <DateWheel value={draft} onChange={setDraft} minYear={q.minYear} maxYear={q.maxYear} />}
          {error && (
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

  const list = visibleQuestions(state.answers, stage)
  const step = resolveStep(list, state.answers, params.get('q'), state.step[stage])
  const q = list[step]

  // 응답과 지금 위치를 저장해 새로고침해도 이어서 할 수 있게 한다
  useEffect(() => saveSurvey({ ...state, step: { ...state.step, [stage]: step } }), [state, step, stage])

  // 주소를 지금 문항에 맞춘다 (처음 들어왔거나, 답하지 않은 문항으로 건너뛰려 한 경우)
  useEffect(() => {
    if (params.get('q') !== q.id) navigate(surveyPath(q, stage), { replace: true })
    window.scrollTo(0, 0)
  }, [q, params, navigate, stage])
  // 지금까지 답한 비율 (단계마다 0~100%)
  const percent = Math.round((step / list.length) * 100)

  const answer = (value) => {
    if (busy.current) return
    const answers = { ...state.answers, [q.id]: value }
    const next = visibleQuestions(answers, stage)
    const idx = next.findIndex((x) => x.id === q.id)
    const last = idx === next.length - 1
    const go = () => {
      busy.current = false
      setState((s) => ({
        answers,
        step: { ...s.step, [stage]: last ? idx : idx + 1 },
        done: { ...s.done, [stage]: s.done[stage] || last },
      }))
      navigate(last ? resultPath(stage) : surveyPath(next[idx + 1], stage))
    }
    // 보기를 누른 경우 선택 표시가 잠깐 보이도록 조금 늦게 넘어간다
    if (q.type === 'choice') {
      busy.current = true
      setState((s) => ({ ...s, answers }))
      setTimeout(go, 180)
    } else {
      go()
    }
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
          ‹
        </button>
        <div className="flex-1">
          <div className="mb-1.5 flex justify-between text-xs font-semibold text-ink-soft">
            <span>
              {stage === 2 && <b className="mr-1.5 text-primary-shade">2단계</b>}
              {SECTIONS[q.section]}
            </span>
            <span className="text-primary-shade" aria-label={`${list.length}문항 중 ${step + 1}번째`}>
              {step + 1} / {list.length}
            </span>
          </div>
          <ProgressBar percent={percent} />
        </div>
      </header>

      <div className="mt-6 flex justify-center">
        <Mascot name="thinking" size="sm" />
      </div>

      <div className="mt-4 flex flex-1 flex-col">
        <QuestionStep
          key={q.id}
          q={q}
          answer={state.answers[q.id]}
          isLast={step === list.length - 1}
          onAnswer={answer}
        />
      </div>
    </main>
  )
}
