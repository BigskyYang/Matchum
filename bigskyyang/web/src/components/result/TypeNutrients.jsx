import { useCallback, useEffect, useRef, useState } from 'react'
import { BASIS_TEXT } from '../../data/nutrientGuide.js'

// 유형 화면의 '부족할 수 있는 영양소' ((나)안, 데이터는 lib/nutrition.js의 typeNutrients)
//   🔸 모두가 챙겨야 할 영양소: 공통 8개 (같은 크기 타일 4열)
//   🔹 내 유형이 특히 챙길 영양소: 2줄 중 유형특이·식사량영향 (테두리 색 = 부족·주의)
//   ▫️ 나와 같은 성별·나이대에서 흔한 영양소: 2줄 중 '흔함' (유형이 아니라 성별·나이 때문)
// 영양소를 누르면 화면 아래에서 올라오는 카드로 역할·대표 음식을 보여 준다 (화면이 밀리지 않게)
const BORDER = { poor: 'border-primary-strong', fair: 'border-[#f2c14e]' }
const CHIP = { poor: 'bg-primary-soft text-primary-shade', fair: 'bg-butter text-ink' }

function CommonTile({ n, onOpen }) {
  return (
    <li>
      <button
        type="button"
        onClick={() => onOpen(n)}
        className="flex aspect-square w-full flex-col items-center justify-center gap-1 rounded-card bg-cream px-1 text-center active:scale-95"
      >
        <span aria-hidden="true" className="text-2xl">
          {n.icon}
        </span>
        <span className="text-[0.75rem] leading-tight font-bold">{n.label}</span>
      </button>
    </li>
  )
}

function PickRow({ n, onOpen, muted = false }) {
  return (
    <li>
      <button
        type="button"
        onClick={() => onOpen(n)}
        className={`flex w-full items-center gap-3 rounded-card border-2 bg-white px-3.5 py-3 text-left active:scale-[0.98] ${
          muted ? 'border-ink-faint/30' : BORDER[n.level.tone]
        }`}
      >
        <span aria-hidden="true" className="text-2xl">
          {n.icon}
        </span>
        <span className="min-w-0 flex-1">
          <span className="block font-bold">{n.label}</span>
          {!muted && <span className="block text-xs text-ink-soft">{n.text}</span>}
        </span>
        <span className="shrink-0 text-right text-xs leading-tight text-ink-soft">
          <b className="block text-base text-ink">10명 중 {n.of10}명</b>
          평균 {n.peerOf10}명
        </span>
      </button>
    </li>
  )
}

function NutrientSheet({ n, sexLabel, ageLabel, onClose }) {
  const closeRef = useRef(null)
  useEffect(() => {
    closeRef.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  const pick = n.level !== undefined

  return (
    <div className="fixed inset-0 z-20 flex items-end justify-center">
      <button type="button" aria-label="닫기" tabIndex={-1} onClick={onClose} className="absolute inset-0 bg-ink/40" />
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="nutrient-sheet-title"
        className="relative max-h-[85dvh] w-full max-w-app overflow-y-auto rounded-t-[1.75rem] bg-white px-6 pt-5 pb-[max(1.5rem,env(safe-area-inset-bottom))] shadow-soft"
      >
        <div className="flex items-center gap-2">
          <span aria-hidden="true" className="text-3xl">
            {n.icon}
          </span>
          <h3 id="nutrient-sheet-title" className="text-xl font-extrabold">
            {n.label}
          </h3>
          {pick && <span className={`rounded-full px-2.5 py-1 text-xs font-bold ${CHIP[n.level.tone]}`}>{n.level.label}</span>}
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label="닫기"
            className="ml-auto flex size-9 items-center justify-center rounded-full text-xl text-ink-soft active:bg-cream"
          >
            ✕
          </button>
        </div>
        <p className="mt-4 leading-relaxed">
          {pick ? (
            <>
              나와 같은 유형·{sexLabel}·{ageLabel} <b>10명 중 {n.of10}명</b>이 {BASIS_TEXT[n.basis]}보다 적게 먹어요. 같은
              성별·나이 평균은 10명 중 {n.peerOf10}명이에요.
            </>
          ) : (
            <>성인 절반 이상이 {BASIS_TEXT[n.basis]}보다 적게 먹는 영양소예요. 유형과 상관없이 모두 챙겨 주세요.</>
          )}
        </p>
        {pick && n.text && <p className="mt-2 inline-block rounded-full bg-lavender px-2.5 py-1 text-xs font-bold">{n.text}</p>}
        <dl className="mt-4 space-y-2 text-sm leading-relaxed">
          <div className="rounded-card bg-cream px-4 py-3">
            <dt className="font-bold">하는 일</dt>
            <dd className="mt-0.5 text-ink-soft">{n.role}</dd>
          </div>
          <div className="rounded-card bg-cream px-4 py-3">
            <dt className="font-bold">이런 음식에 많아요</dt>
            <dd className="mt-0.5 text-ink-soft">{n.foods.join(' · ')}</dd>
          </div>
        </dl>
        {n.basis === 'AI' && (
          <p className="mt-3 text-xs leading-relaxed text-ink-faint">
            충분섭취량은 필요량을 정하기 어려운 영양소에 쓰는 넉넉한 기준이라, 이보다 적다고 꼭 부족하다는 뜻은 아니에요.
          </p>
        )}
      </section>
    </div>
  )
}

export default function TypeNutrients({ common, picks, emptyText, sexLabel, ageLabel }) {
  const [open, setOpen] = useState(null)
  const close = useCallback(() => setOpen(null), [])
  const typePicks = picks.filter((n) => n.tag !== '흔함')
  const peerPicks = picks.filter((n) => n.tag === '흔함')

  return (
    <div>
      <h3 className="text-sm font-bold">🔸 모두가 챙겨야 할 영양소</h3>
      <ul className="mt-2 grid grid-cols-4 gap-1.5">
        {common.map((n) => (
          <CommonTile key={n.key} n={n} onOpen={setOpen} />
        ))}
      </ul>

      <h3 className="mt-5 text-sm font-bold">🔹 내 유형이 특히 챙길 영양소</h3>
      {typePicks.length ? (
        <ul className="mt-2 space-y-2">
          {typePicks.map((n) => (
            <PickRow key={n.key} n={n} onOpen={setOpen} />
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-ink-soft">
          {peerPicks.length ? '내 유형만 특히 더 부족한 영양소는 없어요 👍' : `${emptyText} 👍`}
        </p>
      )}

      {peerPicks.length > 0 && (
        <>
          <h3 className="mt-5 text-sm font-bold text-ink-soft">▫️ 나와 같은 성별·나이대에서 흔한 영양소</h3>
          <ul className="mt-2 space-y-2">
            {peerPicks.map((n) => (
              <PickRow key={n.key} n={n} onOpen={setOpen} muted />
            ))}
          </ul>
        </>
      )}

      <p className="mt-3 text-[0.7rem] leading-relaxed text-ink-faint">
        영양소를 누르면 하는 일과 음식을 볼 수 있어요. 국민건강영양조사 2022–2024의 하루 식사 기록(음식만, 영양제 제외)을 2025
        한국인 영양소 섭취기준과 비교한, 나와 비슷한 사람들의 경향이에요. 나의 영양 상태를 진단한 결과가 아니에요.
      </p>

      {open && <NutrientSheet n={open} sexLabel={sexLabel} ageLabel={ageLabel} onClose={close} />}
    </div>
  )
}
