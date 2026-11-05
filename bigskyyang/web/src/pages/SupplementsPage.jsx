import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import BottomSheet from '../components/BottomSheet.jsx'
import Icon from '../components/Icon.jsx'
import { NUTRIENT_GUIDE } from '../data/nutrientGuide.js'
import { PAGE_SIZE, SUPPLEMENT_NOTICES, TARGET_LABELS } from '../data/supplementInfo.js'
import { buildPersonalResult } from '../lib/result.js'
import { loadPicks, loadSurvey, savePicks } from '../lib/storage.js'
import { dailyTotals, formsOf, productCount, productSections, productTexts, targetsFor } from '../lib/supplements.js'
import { useCatalog, useModels } from '../lib/useCatalog.js'

// 건강기능식품 살펴보기 (/supplements?n=영양소). 개인 결과에서 '부족하기 쉬워요'로 나온 영양소의 제품을 모두 보고 고른다
//   제품: 준혁님 9단계 통과 후보 전체 (data/supplementCatalog.json). 대상 칸을 섞지 않고, 같은 칸 안의 순서는 그대로
//   고른 제품(♡)은 이 휴대폰(sessionStorage)에만 두고, 함께 먹을 때 성분별 하루 합계를 상한섭취량과 비교해 보여 준다
//   제품을 보기 전에 임신·수유·질환·복용약을 한 번 묻고(답은 이 휴대폰에만), 해당되면 제품 대신 상담을 권한다
const GUIDE = Object.fromEntries(NUTRIENT_GUIDE.map((n) => [n.key, n]))
const SOURCE = { habitual: '평소 식사 응답으로 예측', lifestyle: '생활습관 응답으로 예측' }

// '마그네슘이' / '비타민 B1·B2가' (숫자로 끝나면 읽는 소리로)
const iGa = (word) => {
  const code = word.charCodeAt(word.length - 1) - 0xac00
  const final = code >= 0 && code <= 11171 ? code % 28 !== 0 : /[136780LMNR]$/i.test(word)
  return final ? '이' : '가'
}

function usePicks() {
  const [picks, setPicks] = useState(loadPicks)
  useEffect(() => savePicks(picks), [picks])
  const toggle = useCallback(
    (id) => setPicks((p) => ({ ...p, ids: p.ids.includes(id) ? p.ids.filter((x) => x !== id) : [...p.ids, id] })),
    [],
  )
  const setGate = useCallback((gate) => setPicks((p) => ({ ...p, gate })), [])
  return { picks, toggle, setGate }
}

function Gate({ onAnswer }) {
  return (
    <div className="rounded-card bg-white p-5 shadow-soft">
      <p className="text-lg font-bold">제품을 보기 전에 확인해 주세요</p>
      <p className="mt-2 leading-relaxed text-ink-soft">
        임신·수유 중이거나, 치료 중인 질환이 있거나, 약을 드시고 있나요? 해당되면 필요한 영양소와 주의할 점이 달라질 수 있어요.
      </p>
      <div className="mt-4 grid grid-cols-2 gap-2">
        <button type="button" onClick={() => onAnswer('ok')} className="rounded-button bg-cream py-3.5 font-bold active:scale-[0.98]">
          해당 없어요
        </button>
        <button type="button" onClick={() => onAnswer('consult')} className="rounded-button bg-cream py-3.5 font-bold active:scale-[0.98]">
          해당돼요
        </button>
      </div>
      <p className="mt-2 text-xs text-ink-soft">답은 이 휴대폰에만 잠시 두고 저장하지 않아요.</p>
    </div>
  )
}

function Consult({ onRetry }) {
  return (
    <div className="rounded-card bg-white p-5 shadow-soft">
      <p className="text-lg font-bold">의사·약사와 먼저 이야기해 보세요</p>
      <p className="mt-2 leading-relaxed text-ink-soft">
        임신·수유 중이거나 질환·복용약이 있으면 건강기능식품은 전문가와 먼저 상의하는 게 좋아요. 결과 화면의 음식 안내는 그대로
        참고하셔도 좋아요.
      </p>
      <div className="mt-4 flex gap-2">
        <Link to="/result2" className="flex-1 rounded-button bg-cream py-3.5 text-center font-bold">
          결과로 돌아가기
        </Link>
        <button type="button" onClick={onRetry} className="rounded-button px-4 py-3.5 font-semibold text-ink-soft">
          다시 선택하기
        </button>
      </div>
    </div>
  )
}

// 제품 한 줄의 특징 (원문에 있는 것만)
function Features({ p }) {
  const items = [p.form, p.intake, p.amount && `1일 ${p.amount}${p.dvPct != null ? ` · 기준치 ${p.dvPct}%` : ''}`, p.type].filter(Boolean)
  return (
    <span className="mt-1.5 flex flex-wrap gap-1">
      {items.map((x) => (
        <span key={x} className="rounded-full bg-cream px-2 py-0.5 text-xs text-ink-soft">
          {x}
        </span>
      ))}
    </span>
  )
}

function PickButton({ picked, onToggle, name }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={picked}
      aria-label={picked ? `${name} 빼기` : `${name} 담기`}
      className={`flex size-11 shrink-0 items-center justify-center rounded-full text-xl active:scale-90 ${
        picked ? 'bg-primary-soft text-primary-shade' : 'bg-cream text-ink-soft'
      }`}
    >
      <Icon name={picked ? 'heartFilled' : 'heart'} size={22} />
    </button>
  )
}

function ProductCard({ p, picked, onToggle, onOpen }) {
  return (
    <li className="flex items-start gap-2 rounded-card bg-white p-3.5 shadow-soft">
      <button type="button" onClick={onOpen} className="min-w-0 flex-1 text-left">
        <span className="block leading-snug font-bold">{p.name}</span>
        <span className="mt-0.5 block text-xs text-ink-soft">{p.maker}</span>
        <Features p={p} />
      </button>
      <PickButton picked={picked} onToggle={onToggle} name={p.name} />
    </li>
  )
}

function ProductSheet({ catalog, p, picked, onToggle, onClose }) {
  const t = productTexts(catalog, p)
  return (
    <BottomSheet title={p.name} onClose={onClose}>
      <p className="text-sm text-ink-soft">
        {p.maker} · 신고번호 {p.id}
      </p>
      <Features p={p} />
      <div className="mt-4 rounded-card bg-cream px-4 py-3">
        <p className="text-sm font-bold">기능성 (식약처 인정 문구)</p>
        <p className="mt-1 text-sm leading-relaxed whitespace-pre-line">{t.function}</p>
      </div>
      <div className="mt-2 rounded-card bg-cream px-4 py-3">
        <p className="text-sm font-bold">섭취 시 주의사항</p>
        <p className="mt-1 text-sm leading-relaxed whitespace-pre-line text-ink-soft">{t.caution}</p>
      </div>
      <button
        type="button"
        onClick={onToggle}
        aria-pressed={picked}
        className={`mt-4 w-full rounded-button py-3.5 font-bold active:scale-[0.98] ${picked ? 'bg-primary-soft text-primary-shade' : 'bg-cream'}`}
      >
        <span className="inline-flex items-center gap-1.5">
          <Icon name={picked ? 'heartFilled' : 'heart'} size={20} />
          {picked ? '고른 제품에서 빼기' : '고른 제품에 담기'}
        </span>
      </button>
    </BottomSheet>
  )
}

function PicksSheet({ catalog, ids, sex, onToggle, onClose }) {
  const totals = dailyTotals(catalog, ids, sex)
  const over = totals.filter((x) => x.over)
  return (
    <BottomSheet title={`고른 제품 ${ids.length}개`} onClose={onClose}>
      <ul className="space-y-1.5">
        {ids.map((id) => (
          <li key={id} className="flex items-center gap-2 rounded-card bg-cream px-3.5 py-2.5">
            <span className="min-w-0 flex-1 text-sm leading-snug font-bold">{catalog.products[id].name}</span>
            <button
              type="button"
              onClick={() => onToggle(id)}
              aria-label={`${catalog.products[id].name} 빼기`}
              className="flex size-9 shrink-0 items-center justify-center rounded-full text-ink-soft active:bg-white"
            >
              <Icon name="close" size={18} />
            </button>
          </li>
        ))}
      </ul>

      <p className="mt-5 font-bold">함께 먹으면 하루에 이만큼이에요</p>
      <p className={`mt-1 text-sm ${over.length ? 'font-bold text-primary-shade' : 'text-ink-soft'}`}>
        {over.length
          ? `${over.map((x) => x.label).join('·')} 상한섭취량을 넘어요. 함께 먹기 전에 약사와 상의하세요.`
          : '상한섭취량을 넘는 성분은 없어요.'}
      </p>
      <table className="mt-2 w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-ink-soft">
            <th className="py-1.5 font-semibold">성분</th>
            <th className="py-1.5 text-right font-semibold">하루 합계</th>
            <th className="py-1.5 text-right font-semibold">상한</th>
          </tr>
        </thead>
        <tbody>
          {totals.map((x) => (
            <tr key={x.key} className="border-t border-ink/10">
              <td className="py-2 font-bold">{x.label}</td>
              <td className={`py-2 text-right ${x.over ? 'font-bold text-primary-shade' : ''}`}>
                {x.total.toLocaleString('ko-KR')} {x.unit}
              </td>
              <td className="py-2 text-right text-ink-soft">{x.ul ? `${x.ul.toLocaleString('ko-KR')} ${x.unit}` : '없음'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-3 text-xs leading-relaxed text-ink-soft">
        2025 한국인 영양소 섭취기준의 성인 상한섭취량이에요. 음식으로 먹는 양은 빠져 있고, 하루 함량을 알 수 없는 성분은 계산하지
        않았어요.
      </p>
    </BottomSheet>
  )
}

// 한 대상 칸: 20개씩 이어서 보기
function Section({ section, picked, onToggle, onOpen }) {
  const [shown, setShown] = useState(PAGE_SIZE)
  const items = section.items.slice(0, shown)
  return (
    <section>
      <h3 className="text-sm font-bold">
        {TARGET_LABELS[section.target]} <span className="text-ink-soft">{section.items.length}개</span>
      </h3>
      {section.items.length ? (
        <ul className="mt-2 space-y-2">
          {items.map((p) => (
            <ProductCard key={p.id} p={p} picked={picked.includes(p.id)} onToggle={() => onToggle(p.id)} onOpen={() => onOpen(p)} />
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-ink-soft">이 제형의 제품은 없어요.</p>
      )}
      {shown < section.items.length && (
        <button
          type="button"
          onClick={() => setShown((n) => n + PAGE_SIZE)}
          className="mt-2 w-full rounded-button bg-white py-3 font-semibold text-ink-soft shadow-soft"
        >
          {Math.min(PAGE_SIZE, section.items.length - shown)}개 더 보기 (남은 {section.items.length - shown}개)
        </button>
      )}
    </section>
  )
}

export default function SupplementsPage() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const models = useModels()
  const catalog = useCatalog()
  const { picks, toggle, setGate } = usePicks()
  const [form, setForm] = useState(null)
  const [open, setOpen] = useState(null) // 제품 또는 'picks'
  const close = useCallback(() => setOpen(null), [])

  const survey = useMemo(() => loadSurvey(), [])
  const r = useMemo(() => (survey.done[2] && models ? buildPersonalResult(survey.answers, models) : null), [survey, models])

  if (!survey.done[2]) return <Navigate to={survey.done[1] ? '/survey2' : '/survey'} replace />

  const header = (
    <header className="flex items-center gap-2">
      <button
        type="button"
        onClick={() => navigate('/result2')}
        aria-label="결과로 돌아가기"
        className="-ml-2 flex size-11 items-center justify-center rounded-full text-2xl text-ink-soft active:bg-primary-soft"
      >
        <Icon name="back" size={26} />
      </button>
      <h1 className="font-display text-xl font-normal">건강기능식품 살펴보기</h1>
    </header>
  )
  const wrap = (children) => (
    <main className={`flex flex-1 flex-col gap-4 px-5 pt-4 ${picks.ids.length ? 'pb-28' : 'pb-8'}`}>
      {header}
      {children}
    </main>
  )

  if (picks.gate === null) return wrap(<Gate onAnswer={setGate} />)
  if (picks.gate === 'consult') return wrap(<Consult onRetry={() => setGate(null)} />)
  if (!r || !catalog) return wrap(<p className="text-sm text-ink-soft">불러오고 있어요…</p>)

  const { nutrients } = r.supplements
  if (!nutrients.length) {
    return wrap(
      <p className="rounded-card bg-white p-5 leading-relaxed shadow-soft">
        지금 응답으로는 건강기능식품으로 챙길 영양소가 없어요. 결과 화면의 음식 안내를 참고해 주세요.
      </p>,
    )
  }

  const sex = survey.answers.sex
  const age = r.age
  const targets = targetsFor(sex, age)
  const active = nutrients.find((n) => n.key === params.get('n')) ?? nutrients[0]
  const watchRows = r.nutrition.watch.filter((w) => active.from.includes(w.key))
  const foods = [...new Set(active.from.flatMap((k) => GUIDE[k]?.foods ?? []))]
  const reasonName = watchRows.length > 1 ? `비타민 ${watchRows.map((w) => w.label.replace('비타민 ', '')).join('·')}` : watchRows[0].label
  const forms = formsOf(catalog, active.key, targets)
  const sections = productSections(catalog, active.key, targets, form ? [form] : [])
  const pick = (key) => {
    setForm(null)
    setParams({ n: key }, { replace: true })
  }

  return wrap(
    <>
      {/* 영양소 고르기 */}
      <div role="tablist" aria-label="영양소" className="-mx-5 flex gap-2 overflow-x-auto px-5 pb-1 [scrollbar-width:none]">
        {nutrients.map((n) => (
          <button
            key={n.key}
            type="button"
            role="tab"
            aria-selected={n.key === active.key}
            onClick={() => pick(n.key)}
            className={`flex shrink-0 items-center gap-1.5 rounded-full px-3.5 py-2.5 font-bold ${
              n.key === active.key ? 'bg-primary-shade text-white' : 'bg-white text-ink shadow-soft'
            }`}
          >
            <span aria-hidden="true">{n.icon}</span>
            {n.label}
            <span className={`text-xs ${n.key === active.key ? 'text-white' : 'text-ink-soft'}`}>{productCount(catalog, n.key, targets)}</span>
          </button>
        ))}
      </div>

      {/* 왜 이 영양소인지 */}
      <div className="rounded-card bg-lavender/50 px-4 py-3 text-sm leading-relaxed">
        <p className="font-bold">
          {reasonName}
          {iGa(reasonName)} 부족하기 쉬워요
          <span className="ml-1.5 text-xs font-normal text-ink-soft">{SOURCE[watchRows[0].source]}</span>
        </p>
        {foods.length > 0 && <p className="mt-0.5 text-ink-soft">음식으로는 {foods.join('·')}에 많아요.</p>}
      </div>

      {/* 제형 고르기 */}
      <div role="group" aria-label="제형" className="-mx-5 flex gap-1.5 overflow-x-auto px-5 [scrollbar-width:none]">
        {[{ form: null, count: forms.reduce((s, f) => s + f.count, 0) }, ...forms].map((f) => (
          <button
            key={f.form ?? 'all'}
            type="button"
            aria-pressed={form === f.form}
            onClick={() => setForm(f.form)}
            className={`shrink-0 rounded-full px-3 py-2 text-sm font-semibold ${
              form === f.form ? 'bg-ink text-white' : 'bg-white text-ink-soft shadow-soft'
            }`}
          >
            {f.form ?? '전체'} {f.count}
          </button>
        ))}
      </div>

      {sections.map((s) => (
        <Section
          key={`${active.key}-${s.target}-${form}`}
          section={s}
          picked={picks.ids}
          onToggle={toggle}
          onOpen={(p) => setOpen(p)}
        />
      ))}

      <ul className="space-y-1 text-xs leading-relaxed text-ink-soft">
        {SUPPLEMENT_NOTICES.map((t) => (
          <li key={t}>· {t}</li>
        ))}
      </ul>

      {/* 고른 제품 */}
      {picks.ids.length > 0 && (
        <div className="fixed inset-x-0 bottom-0 z-10">
          <div className="mx-auto max-w-app border-t border-ink/10 bg-cream/95 px-5 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] backdrop-blur">
            <button
              type="button"
              onClick={() => setOpen('picks')}
              className="flex w-full items-center justify-between rounded-button bg-primary-strong px-5 py-3.5 text-xl font-bold text-white shadow-button active:translate-y-1 active:shadow-button-pressed"
            >
              <span className="inline-flex items-center gap-2">
                <Icon name="heartFilled" size={22} />고른 제품 {picks.ids.length}개
              </span>
              <span>함께 먹을 때 ›</span>
            </button>
          </div>
        </div>
      )}

      {open === 'picks' && <PicksSheet catalog={catalog} ids={picks.ids} sex={sex} onToggle={toggle} onClose={close} />}
      {open && open !== 'picks' && (
        <ProductSheet catalog={catalog} p={open} picked={picks.ids.includes(open.id)} onToggle={() => toggle(open.id)} onClose={close} />
      )}
    </>,
  )
}
