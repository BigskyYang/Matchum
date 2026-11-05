import { useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import GroupChip from '../components/GroupChip.jsx'
import Icon from '../components/Icon.jsx'
import Mascot from '../components/Mascot.jsx'
import NutrientArt from '../components/NutrientArt.jsx'
import { BAND_CLS, bandLabel } from '../data/bands.js'
import { availableChanges, simulate } from '../lib/simulate.js'
import { loadSurvey } from '../lib/storage.js'
import { useModels } from '../lib/useCatalog.js'

// '습관을 바꾸면 어떻게 될까?' (/simulate): 습관을 켜 보면 유형·영양소 결과를 다시 계산해 지금과 비교한다 (계산은 lib/simulate.js)
//   습관 버튼(2열) 바로 아래에 결과를 두어 한 화면에서 같이 보이게 한다 (고정 영역은 두지 않는다)
//   모델이 학습 자료에서 본 경향일 뿐 실제로 바뀐다는 뜻이 아니라는 안내를 한 줄 둔다
function Badge({ n, band }) {
  return <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-bold ${BAND_CLS[band]}`}>{bandLabel(n, band)}</span>
}

function TypeRow({ type }) {
  if (!type.changed) {
    return (
      <p className="flex items-center gap-2 text-sm text-ink-soft">
        <Mascot name={`type_${type.before.id}`} size="xs" />
        유형은 그대로 <b className="text-ink">{type.before.name}</b>예요
      </p>
    )
  }
  return (
    <div className="flex items-center gap-2">
      <Mascot name={`type_${type.before.id}`} size="xs" className="opacity-60" />
      <Icon name="next" size={18} className="text-ink-faint" />
      <Mascot name={`type_${type.after.id}`} size="xs" className="animate-pop motion-reduce:animate-none" />
      <span className="min-w-0">
        <GroupChip code={type.after.id[0]} name={type.after.main.name} className="text-xs" />
        <span className="mt-0.5 block font-bold">{type.after.name}</span>
      </span>
    </div>
  )
}

function Result({ sim, loading }) {
  return (
    <section aria-live="polite" className="rounded-card bg-white p-5 shadow-soft">
      <h2 className="font-display text-xl font-normal">이렇게 바뀌어요</h2>
      <div className="mt-3">
        <TypeRow type={sim.type} />
      </div>
      <div className="mt-4">
        {loading ? (
          <p className="text-sm text-ink-soft">영양소를 계산하고 있어요…</p>
        ) : sim.nutrients.length ? (
          <ul className="flex flex-col gap-2">
            {sim.nutrients.map((n) => (
              <li
                key={n.key}
                className={`flex items-center gap-2 rounded-card px-3 py-2.5 ${n.better ? 'bg-mint/60' : 'bg-primary-soft/60'}`}
              >
                <NutrientArt n={n} className="size-7" />
                <span className="min-w-0 flex-1 text-sm font-bold">{n.label}</span>
                <Badge n={n} band={n.from} />
                <Icon name="next" size={14} className="shrink-0 text-ink-faint" />
                <Badge n={n} band={n.to} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-ink-soft">영양소 결과는 그대로예요.</p>
        )}
      </div>
    </section>
  )
}

export default function SimulatePage() {
  const navigate = useNavigate()
  const survey = useMemo(() => loadSurvey(), [])
  const models = useModels()
  const [on, setOn] = useState([])
  const ready = survey.done[1] && survey.done[2]
  const changes = useMemo(() => (ready ? availableChanges(survey.answers) : []), [ready, survey])
  const sim = useMemo(() => (ready && on.length ? simulate(survey.answers, on, models) : null), [ready, survey, on, models])
  if (!survey.done[1]) return <Navigate to="/survey" replace />
  if (!survey.done[2]) return <Navigate to="/survey2" replace />

  const back = () => {
    if ((window.history.state?.idx ?? 0) > 0) navigate(-1)
    else navigate('/result2')
  }
  const toggle = (id) => setOn((list) => (list.includes(id) ? list.filter((x) => x !== id) : [...list, id]))

  return (
    <main className="flex flex-1 flex-col gap-4 px-5 pt-4 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <header className="flex items-center gap-2">
        <button
          type="button"
          onClick={back}
          aria-label="뒤로"
          className="-ml-2 flex size-11 items-center justify-center rounded-full text-2xl text-ink-soft active:bg-primary-soft"
        >
          <Icon name="back" size={26} />
        </button>
        <h1 className="font-display text-xl font-normal">습관을 바꾸면 어떻게 될까?</h1>
      </header>

      {changes.length ? (
        <ul className="grid grid-cols-2 gap-2">
          {changes.map((c) => {
            const active = on.includes(c.id)
            return (
              <li key={c.id}>
                <button
                  type="button"
                  aria-pressed={active}
                  onClick={() => toggle(c.id)}
                  className={`flex h-full w-full items-center gap-2 rounded-card px-3 py-3 text-left text-sm leading-tight font-bold transition-colors active:scale-[0.98] ${
                    active ? 'bg-primary-shade text-white' : 'bg-white text-ink shadow-soft'
                  }`}
                >
                  <Icon name={active ? 'check' : c.icon} size={20} className="shrink-0" />
                  {c.label}
                </button>
              </li>
            )
          })}
        </ul>
      ) : (
        <p className="flex items-center gap-3 rounded-card bg-white p-5 text-sm shadow-soft">
          <Mascot name="cheer" fallback="happy" size="xs" />
          바꿔 볼 습관이 없을 만큼 잘 챙기고 있어요.
        </p>
      )}

      {sim ? (
        <Result sim={sim} loading={!sim.nutrients} />
      ) : (
        changes.length > 0 && (
          <p className="flex items-center gap-3 rounded-card bg-white p-5 text-sm text-ink-soft shadow-soft">
            <Mascot name="thinking" size="xs" />
            위에서 습관을 하나 켜 보세요.
          </p>
        )
      )}

      {on.length > 0 && (
        <button type="button" onClick={() => setOn([])} className="py-2 text-sm font-semibold text-ink-soft">
          모두 끄기
        </button>
      )}

      <p className="mt-auto text-center text-xs leading-relaxed text-ink-faint">
        모델이 국민건강영양조사 자료에서 본 경향이에요.
        <br />
        습관을 바꾸면 꼭 이렇게 된다는 뜻은 아니에요.
      </p>
    </main>
  )
}
