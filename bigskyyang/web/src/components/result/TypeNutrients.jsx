import { useCallback, useState } from 'react'
import BottomSheet from '../BottomSheet.jsx'
import { BASIS_TEXT } from '../../data/nutrientGuide.js'

// 유형 화면의 '부족할 수 있는 영양소' ((나)안, 데이터는 lib/nutrition.js의 typeNutrients)
//   🔹 내 유형이 특히 챙길 영양소: 2줄 중 유형특이·식사량영향 (테두리 색 = 부족·주의). 내 유형 결과라 맨 위에 크게
//   ▫️ 나와 같은 성별·나이대에서 흔한 영양소: 2줄 중 '흔함' (유형이 아니라 성별·나이 때문)
//   🔸 모두가 챙겨야 할 영양소: 공통 8개 (유형과 상관없어 맨 아래 작은 칩으로)
// 영양소를 누르면 화면 아래에서 올라오는 창(BottomSheet)으로 역할·대표 음식을 보여 준다. 근거 설명은 '어떻게 만들었나요?' 창에
const BORDER = { poor: 'border-primary-strong', fair: 'border-[#f2c14e]' }
const CHIP = { poor: 'bg-primary-soft text-primary-shade', fair: 'bg-butter text-ink' }

function CommonChip({ n, onOpen }) {
  return (
    <li>
      <button
        type="button"
        onClick={() => onOpen(n)}
        className="flex items-center gap-1 rounded-full bg-cream px-3 py-2 text-sm font-bold active:scale-95"
      >
        <span aria-hidden="true">{n.icon}</span>
        {n.label}
      </button>
    </li>
  )
}

// 10명 중 몇 명인지 점 10개로 (색칠한 점 = 적게 먹는 사람)
function Dots({ of10, tone }) {
  const fill = tone === 'muted' ? 'bg-ink-soft' : tone === 'fair' ? 'bg-[#e0a92e]' : 'bg-primary-strong'
  return (
    <span aria-hidden="true" className="mt-1.5 flex gap-1">
      {Array.from({ length: 10 }, (_, i) => (
        <span key={i} className={`size-2.5 rounded-full ${i < of10 ? fill : 'bg-ink/10'}`} />
      ))}
    </span>
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
          <Dots of10={n.of10} tone={muted ? 'muted' : n.level.tone} />
        </span>
        <span className="shrink-0 text-right text-xs leading-tight text-ink-soft">
          <b className="block text-base text-ink">10명 중 {n.of10}명</b>
          평균 {n.peerOf10}명
        </span>
        <span aria-hidden="true" className="text-ink-faint">
          ›
        </span>
      </button>
    </li>
  )
}

function NutrientSheet({ n, sexLabel, ageLabel, onClose }) {
  const pick = n.level !== undefined
  return (
    <BottomSheet
      title={
        <>
          <span aria-hidden="true">{n.icon}</span>
          {n.label}
        </>
      }
      aside={pick && <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${CHIP[n.level.tone]}`}>{n.level.label}</span>}
      onClose={onClose}
    >
      <p className="leading-relaxed">
        {pick ? (
          <>
            나와 같은 유형·{sexLabel}·{ageLabel} <b>10명 중 {n.of10}명</b>이 {BASIS_TEXT[n.basis]}보다 적게 먹어요. 같은 성별·나이
            평균은 10명 중 {n.peerOf10}명이에요.
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
    </BottomSheet>
  )
}

export default function TypeNutrients({ common, picks, emptyText, sexLabel, ageLabel }) {
  const [open, setOpen] = useState(null)
  const close = useCallback(() => setOpen(null), [])
  const typePicks = picks.filter((n) => n.tag !== '흔함')
  const peerPicks = picks.filter((n) => n.tag === '흔함')

  return (
    <div>
      <h3 className="text-sm font-bold">🔹 내 유형이 특히 챙길 영양소</h3>
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

      <h3 className="mt-5 text-sm font-bold">🔸 모두가 챙겨야 할 영양소 {common.length}개</h3>
      <p className="mt-1 text-xs text-ink-soft">유형과 상관없이 성인 절반 이상이 적게 먹는 영양소예요.</p>
      <ul className="mt-2 flex flex-wrap gap-1.5">
        {common.map((n) => (
          <CommonChip key={n.key} n={n} onOpen={setOpen} />
        ))}
      </ul>


      {open && <NutrientSheet n={open} sexLabel={sexLabel} ageLabel={ageLabel} onClose={close} />}
    </div>
  )
}
