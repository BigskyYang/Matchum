import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Mascot from '../components/Mascot.jsx'
import PrimaryButton from '../components/PrimaryButton.jsx'
import ChoiceInput from '../components/survey/ChoiceInput.jsx'
import ProgressBar from '../components/survey/ProgressBar.jsx'
import { DateWheel, DurationWheel, NumberWheel, TimeWheel } from '../components/survey/WheelInputs.jsx'
import { SECTIONS, visibleQuestions } from '../data/questions.js'
import { loadSurvey, saveSurvey } from '../lib/storage.js'

function QuestionStep({ q, answer, isLast, onAnswer }) {
  // 휠 입력은 이전 응답이 있으면 그 값, 없으면 문항의 initial 값에서 시작
  const [draft, setDraft] = useState(() => answer ?? q.initial)

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
          {q.type === 'choice' && <ChoiceInput options={q.options} value={answer} onSelect={onAnswer} />}
          {q.type === 'date' && <DateWheel value={draft} onChange={setDraft} />}
          {q.type === 'number' && <NumberWheel value={draft} onChange={setDraft} unit={q.unit} min={q.min} max={q.max} />}
          {q.type === 'time' && <TimeWheel value={draft} onChange={setDraft} hourStart={q.hourStart} />}
          {q.type === 'duration' && <DurationWheel value={draft} onChange={setDraft} per={q.per} maxHours={q.maxHours} />}
        </div>
      </section>

      {q.type !== 'choice' && (
        <footer className="mt-8">
          <PrimaryButton onClick={() => onAnswer(draft)}>
            {isLast ? '결과 보기' : '다음'}
          </PrimaryButton>
        </footer>
      )}
    </>
  )
}

export default function SurveyPage() {
  const navigate = useNavigate()
  const [state, setState] = useState(loadSurvey)
  const busy = useRef(false)

  useEffect(() => saveSurvey(state), [state])

  const list = visibleQuestions(state.answers)
  const step = Math.min(state.step, list.length - 1)
  const q = list[step]
  // 지금까지 답한 비율 (분기에 따라 전체 문항 수가 바뀌어도 자연스럽게 늘어난다)
  const percent = Math.round((step / list.length) * 100)

  const answer = (value) => {
    if (busy.current) return
    const answers = { ...state.answers, [q.id]: value }
    const next = visibleQuestions(answers)
    const idx = next.findIndex((x) => x.id === q.id)
    const done = idx === next.length - 1
    const go = () => {
      busy.current = false
      setState({ answers, step: done ? idx : idx + 1, done })
      if (done) navigate('/result')
      else window.scrollTo(0, 0)
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

  const back = () => {
    if (step === 0) navigate('/')
    else setState((s) => ({ ...s, step: step - 1 }))
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
            <span>{SECTIONS[q.section]}</span>
            <span className="text-primary-strong">{percent}%</span>
          </div>
          <ProgressBar percent={percent} />
        </div>
      </header>

      <div className="mt-6 flex justify-center">
        <Mascot name="thinking" size="sm" />
      </div>

      <div className="mt-4 flex flex-1 flex-col">
        <QuestionStep key={q.id} q={q} answer={state.answers[q.id]} isLast={step === list.length - 1} onAnswer={answer} />
      </div>
    </main>
  )
}
