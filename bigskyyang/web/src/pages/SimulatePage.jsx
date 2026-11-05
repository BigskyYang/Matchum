import { useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import Icon from '../components/Icon.jsx'
import Mascot from '../components/Mascot.jsx'
import NutrientArt from '../components/NutrientArt.jsx'
import { availableChanges, simulate } from '../lib/simulate.js'
import { loadSurvey } from '../lib/storage.js'
import { useModels } from '../lib/useCatalog.js'

// 응답 변경 비교 (/simulate): 결과 화면과 같은 대표 모델을 유지하고 생활습관 모델은 따로 비교한다.
//   습관 버튼(2열) 바로 아래에 결과를 두어 한 화면에서 같이 보이게 한다 (고정 영역은 두지 않는다)
//   실제 효과를 예측하지 않는다는 안내는 비교 결과 바로 위에 둔다.
const BAND = { High: '높은 편', Mid: '보통', Low: '낮은 편' }
const SOURCE = { lifestyle: '생활습관', habitual: '평소 식사' }
const NOTICE = '설문 응답을 바꿨을 때 모델의 예측을 비교하는 기능이며, 실제 영양 상태의 변화나 습관 개선 효과를 예측하는 것은 아닙니다.'

function Badge({ band }) {
  return <span className="inline-block rounded-full bg-cream px-2 py-1 text-xs font-bold">{BAND[band]}</span>
}

function TypeRow({ type }) {
  return (
    <div className="grid grid-cols-2 gap-3 text-center">
      {[['현재 응답 기준', type.before], ['변경한 응답 기준', type.after]].map(([label, t]) => (
        <div key={label} className="flex min-w-0 flex-col items-center">
          <p className="text-xs text-ink-soft">{label}</p>
          <Mascot name={`type_${t.id}`} size="xs" className="my-1" />
          <p className="text-sm font-bold">{t.name}</p>
        </div>
      ))}
    </div>
  )
}

function NutrientComparison({ nutrients }) {
  if (!nutrients.length) return <p className="text-sm text-ink-soft">예측 등급이 달라진 영양소가 없어요. 실제 효과가 없다는 뜻은 아니에요.</p>
  return (
    <table className="w-full table-fixed text-sm">
      <caption className="mb-2 text-left text-xs text-ink-soft">영양소별 상대 등급</caption>
      <thead>
        <tr className="text-xs text-ink-soft">
          <th scope="col" className="w-2/5 pb-2 text-left font-semibold">영양소</th>
          <th scope="col" className="px-1 pb-2 font-semibold">현재 응답 기준</th>
          <th scope="col" className="px-1 pb-2 font-semibold">변경한 응답 기준</th>
        </tr>
      </thead>
      <tbody>
        {nutrients.map((n) => (
          <tr key={n.key} className="border-t border-ink/10">
            <th scope="row" className="py-3 text-left">
              <span className="flex items-center gap-1.5"><NutrientArt n={n} className="size-6" />{n.label}</span>
              {n.excess && <span className="mt-1 block text-[11px] font-normal text-ink-soft">기준 초과 가능성</span>}
              <span className="block text-[11px] font-normal text-ink-faint">{SOURCE[n.source]} 응답 기준</span>
            </th>
            <td className="px-1 py-3 text-center"><Badge band={n.from} /></td>
            <td className="px-1 py-3 text-center"><Badge band={n.to} /></td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function Result({ sim, showLifestyle }) {
  return (
    <section aria-live="polite" className="rounded-card bg-white p-5 shadow-soft">
      <h2 className="font-display text-xl font-normal">응답별 예측 비교</h2>
      <p className="mt-2 text-xs leading-relaxed text-ink-soft">{NOTICE}</p>
      <div className="mt-3">
        <TypeRow type={sim.type} />
      </div>
      <div className="mt-4">
        {!sim.nutrients ? (
          <p className="text-sm text-ink-soft">영양소를 계산하고 있어요…</p>
        ) : (
          <NutrientComparison nutrients={sim.nutrients} />
        )}
      </div>
      {showLifestyle && sim.habitualAvailable && (
        <details className="mt-4 border-t border-ink/10 pt-3">
          <summary className="cursor-pointer text-sm font-bold">생활습관 응답 기준으로 비교</summary>
          <p className="mt-2 text-xs leading-relaxed text-ink-soft">평소 식사 모델에는 운동·수면·끼니 응답이 반영되지 않아요. 아래는 생활습관 모델만 따로 비교한 결과예요.</p>
          <div className="mt-3"><NutrientComparison nutrients={sim.lifestyleNutrients} /></div>
        </details>
      )}
      {sim.nutrients?.some((n) => n.excess) && (
        <p className="mt-3 text-xs leading-relaxed text-ink-soft">나트륨의 등급 차이는 선택한 음식이나 습관이 나트륨 섭취를 늘리거나 줄인다는 뜻이 아니에요.</p>
      )}
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
      <header className="flex items-start gap-2">
        <button
          type="button"
          onClick={back}
          aria-label="뒤로"
          className="-ml-2 flex size-11 shrink-0 items-center justify-center rounded-full text-2xl text-ink-soft active:bg-primary-soft"
        >
          <Icon name="back" size={26} />
        </button>
        <h1 className="py-2 font-display text-xl font-normal">응답을 바꾸면 예측은 어떻게 달라질까?</h1>
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
                  <span>
                    {c.label}
                    <span className={`mt-1 block text-[11px] font-normal ${active ? 'text-white' : 'text-ink-soft'}`}>{SOURCE[c.model]} 모델에 반영</span>
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      ) : (
        <p className="flex items-center gap-3 rounded-card bg-white p-5 text-sm shadow-soft">
          <Mascot name="cheer" fallback="happy" size="xs" />
          비교할 수 있는 응답 변경 항목이 없어요.
        </p>
      )}

      {sim ? (
        <Result sim={sim} showLifestyle={changes.some((c) => on.includes(c.id) && c.model === 'lifestyle')} />
      ) : (
        changes.length > 0 && (
          <p className="flex items-center gap-3 rounded-card bg-white p-5 text-sm text-ink-soft shadow-soft">
            <Mascot name="thinking" size="xs" />
            비교할 응답을 선택해 보세요.
          </p>
        )
      )}

      {on.length > 0 && (
        <button type="button" onClick={() => setOn([])} className="py-2 text-sm font-semibold text-ink-soft">
          모두 끄기
        </button>
      )}

      <p className="mt-auto text-center text-xs leading-relaxed text-ink-faint">변경값은 비교를 위한 가정이며 개인별 권장 목표는 아니에요.</p>
    </main>
  )
}
