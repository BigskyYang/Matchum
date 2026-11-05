import { useEffect, useMemo, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import BottomSheet from '../components/BottomSheet.jsx'
import Icon from '../components/Icon.jsx'
import PrimaryButton from '../components/PrimaryButton.jsx'
import TotalsTable from '../components/supplements/TotalsTable.jsx'
import { SERVICE_NAME } from '../config.js'
import { drawMemoImage } from '../lib/memoImage.js'
import { buildPersonalResult } from '../lib/result.js'
import { canShareFile, imageFile, shareOrSave } from '../lib/saveImage.js'
import { loadSurvey } from '../lib/storage.js'
import { combinedIds, dailyTotals, searchProducts } from '../lib/supplements.js'
import { useCatalog, useModels } from '../lib/useCatalog.js'
import { usePicks } from '../lib/usePicks.js'

// 내가 먹는 건강기능식품 (/my-supplements)
//   1) 먹고 있는 제품 등록: 준혁님 제품 목록에서 이름·회사로 찾기, 목록에 없으면 이름만 적기 (함량을 몰라 합계에서 빠진다)
//   2) 먹고 있는 제품 + 고른 제품(♡)을 함께 먹을 때 성분별 하루 합계와 상한섭취량
//   3) 약사 상담 메모: 위 내용과 물어보고 싶은 것을 이미지 한 장으로 (휴대폰에서 만들고 어디에도 보내지 않는다)
const MAX_QUESTION = 120
const decadeOf = (age) => (age >= 70 ? '70대 이상' : `${Math.max(20, Math.floor(age / 10) * 10)}대`)

function MemoSheet({ memo, onClose }) {
  const [question, setQuestion] = useState('')
  const [drawn, setDrawn] = useState(null) // { key, blob, url }
  const [note, setNote] = useState('')
  const key = question.trim()
  const image = drawn?.key === key ? drawn : null

  useEffect(() => {
    let url = null
    let alive = true
    const id = setTimeout(() => {
      drawMemoImage({ ...memo, question: key }, { serviceName: SERVICE_NAME })
        .then((blob) => {
          if (!alive) return
          url = URL.createObjectURL(blob)
          setDrawn({ key, blob, url })
        })
        .catch(() => alive && setNote('이미지를 만들지 못했어요. 잠시 뒤에 다시 해 주세요.'))
    }, 400)
    return () => {
      alive = false
      clearTimeout(id)
      if (url) URL.revokeObjectURL(url)
    }
  }, [memo, key])

  const fileName = `약사상담메모_${memo.dateLabel.replace(/\D+/g, '')}.png`
  const sharable = image && canShareFile(imageFile(image.blob, fileName))
  const save = async () => {
    if (!image) return
    const result = await shareOrSave(image.blob, fileName, '약사 상담 메모')
    if (result === 'saved') setNote('이미지를 저장했어요. 저장이 안 되면 위 이미지를 길게 눌러 저장해 주세요.')
  }

  return (
    <BottomSheet title="약사 상담 메모" onClose={onClose}>
      <label htmlFor="memo-question" className="text-sm font-bold">
        약사에게 물어보고 싶은 것 <span className="font-normal text-ink-soft">(선택)</span>
      </label>
      <textarea
        id="memo-question"
        value={question}
        maxLength={MAX_QUESTION}
        rows={2}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="예: 지금 먹는 약과 같이 먹어도 되나요?"
        className="mt-1.5 w-full resize-none rounded-card border border-ink/15 bg-white px-3.5 py-2.5 text-sm focus:border-primary-strong focus:outline-none"
      />
      <div className="mt-3 flex justify-center">
        {image ? (
          <img src={image.url} alt="약사 상담 메모 미리보기" className="max-h-[44dvh] w-auto rounded-card shadow-soft" />
        ) : (
          <p className="py-12 text-sm text-ink-soft">{note || '메모를 만들고 있어요…'}</p>
        )}
      </div>
      <button
        type="button"
        onClick={save}
        disabled={!image}
        className="mt-4 flex w-full items-center justify-center gap-2 rounded-button bg-primary-strong py-3.5 text-xl font-bold text-white shadow-button active:translate-y-1 active:shadow-button-pressed disabled:bg-ink/10 disabled:text-ink-soft disabled:shadow-none"
      >
        <Icon name={sharable ? 'share' : 'download'} size={22} />
        {sharable ? '메모 공유하기' : '메모 저장하기'}
      </button>
      {image && note && (
        <p role="status" className="mt-2 text-center text-xs text-ink-soft">
          {note}
        </p>
      )}
      <p className="mt-2 text-center text-xs text-ink-faint">메모는 이 휴대폰에서만 만들고 어디에도 보내지 않아요.</p>
    </BottomSheet>
  )
}

export default function MySupplementsPage() {
  const navigate = useNavigate()
  const survey = useMemo(() => loadSurvey(), [])
  const models = useModels()
  const catalog = useCatalog()
  const { picks, addMine, removeMine } = usePicks()
  const [query, setQuery] = useState('')
  const [memoOpen, setMemoOpen] = useState(false)
  const [today] = useState(() => new Date().toLocaleDateString('ko-KR'))
  const r = useMemo(() => (survey.done[2] && models ? buildPersonalResult(survey.answers, models) : null), [survey, models])
  const found = useMemo(() => (catalog ? searchProducts(catalog, query) : { items: [], total: 0 }), [catalog, query])
  const totals = catalog ? dailyTotals(catalog, combinedIds(picks.mine, picks.ids), survey.answers.sex) : []
  const manualCount = picks.mine.filter((m) => !m.id).length

  const memo = useMemo(() => {
    if (!catalog || !r) return null
    const product = (id) => ({ name: catalog.products[id].name, maker: catalog.products[id].maker })
    return {
      who: `${r.sex === 1 ? '남성' : '여성'} · ${decadeOf(r.age)}`,
      dateLabel: today,
      watch: r.nutrition.watch.map((n) => n.label),
      mine: picks.mine.map((m) => (m.id ? product(m.id) : { name: m.name })),
      picks: picks.ids.filter((id) => !picks.mine.some((m) => m.id === id)).map(product),
      manualCount: picks.mine.filter((m) => !m.id).length,
      totals: dailyTotals(catalog, combinedIds(picks.mine, picks.ids), r.sex),
    }
  }, [catalog, r, picks, today])

  if (!survey.done[2]) return <Navigate to={survey.done[1] ? '/survey2' : '/survey'} replace />

  const back = () => {
    if ((window.history.state?.idx ?? 0) > 0) navigate(-1)
    else navigate('/supplements')
  }
  const q = query.trim()
  const isMine = (id) => picks.mine.some((m) => m.id === id)

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
        <h1 className="font-display text-xl font-normal">내가 먹는 건강기능식품</h1>
      </header>

      <section className="rounded-card bg-white p-5 shadow-soft">
        <label htmlFor="product-search" className="font-bold">
          먹고 있는 제품 찾기
        </label>
        <div className="mt-2 flex items-center gap-2 rounded-button bg-cream px-3.5">
          <Icon name="search" size={20} className="shrink-0 text-ink-soft" />
          <input
            id="product-search"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="제품명이나 회사 이름"
            className="min-w-0 flex-1 bg-transparent py-3 text-base focus:outline-none"
          />
        </div>
        {!catalog && <p className="mt-3 text-sm text-ink-soft">제품 목록을 불러오고 있어요…</p>}
        {catalog && q.length >= 2 && (
          <div className="mt-3">
            {found.items.length > 0 && (
              <ul className="flex flex-col gap-1.5">
                {found.items.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      disabled={isMine(p.id)}
                      onClick={() => addMine({ id: p.id })}
                      className="flex w-full items-center gap-2 rounded-card bg-cream px-3.5 py-2.5 text-left active:scale-[0.99] disabled:opacity-60"
                    >
                      <span className="min-w-0 flex-1">
                        <span className="block text-sm leading-snug font-bold">{p.name}</span>
                        <span className="block text-xs text-ink-soft">
                          {p.maker} · {p.form}
                        </span>
                      </span>
                      <span className="shrink-0 text-sm font-bold text-primary-shade">{isMine(p.id) ? '추가됨' : '추가'}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {found.total > found.items.length && (
              <p className="mt-2 text-xs text-ink-soft">
                {found.total.toLocaleString('ko-KR')}개 중 {found.items.length}개만 보여요. 더 자세히 적어 보세요.
              </p>
            )}
            <button
              type="button"
              onClick={() => {
                addMine({ name: q })
                setQuery('')
              }}
              className="mt-2 w-full rounded-card border border-dashed border-ink/20 px-3.5 py-2.5 text-left text-sm text-ink-soft"
            >
              {found.items.length ? '찾는 제품이 없나요? ' : '목록에 없는 제품이에요. '}
              <b className="text-ink">‘{q}’ 이름만 적어 두기</b>
            </button>
          </div>
        )}
      </section>

      <section className="rounded-card bg-white p-5 shadow-soft">
        <h2 className="font-display text-xl font-normal">먹고 있는 제품 {picks.mine.length}개</h2>
        {picks.mine.length ? (
          <ul className="mt-3 space-y-1.5">
            {picks.mine.map((m, i) => {
              const p = m.id && catalog?.products[m.id]
              return (
                <li key={m.id ?? `name-${m.name}`} className="flex items-center gap-2 rounded-card bg-cream px-3.5 py-2.5">
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm leading-snug font-bold">{p ? p.name : m.name}</span>
                    <span className="block text-xs text-ink-soft">{p ? p.maker : '이름만 적은 제품 · 함량 모름'}</span>
                  </span>
                  <button
                    type="button"
                    onClick={() => removeMine(i)}
                    aria-label={`${p ? p.name : m.name} 빼기`}
                    className="flex size-9 shrink-0 items-center justify-center rounded-full text-ink-soft active:bg-white"
                  >
                    <Icon name="close" size={18} />
                  </button>
                </li>
              )
            })}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-ink-soft">위에서 찾아 추가해 주세요.</p>
        )}
      </section>

      {totals.length > 0 && (
        <section className="rounded-card bg-white p-5 shadow-soft">
          <h2 className="font-display text-xl font-normal">함께 먹으면 하루에</h2>
          {picks.ids.length > 0 && <p className="mt-1 text-xs text-ink-soft">고른 제품 {picks.ids.length}개도 함께 계산했어요.</p>}
          <div className="mt-2">
            <TotalsTable totals={totals} />
          </div>
          {manualCount > 0 && <p className="mt-1 text-xs text-ink-soft">이름만 적은 제품 {manualCount}개는 함량을 몰라 합계에 넣지 않았어요.</p>}
        </section>
      )}

      <PrimaryButton size="sm" onClick={() => setMemoOpen(true)} disabled={!memo}>
        약사 상담 메모 만들기
      </PrimaryButton>
      {memoOpen && memo && <MemoSheet memo={memo} onClose={() => setMemoOpen(false)} />}
    </main>
  )
}
