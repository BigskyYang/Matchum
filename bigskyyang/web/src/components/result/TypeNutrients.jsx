import { useCallback, useState } from 'react'
import BottomSheet from '../BottomSheet.jsx'
import { BASIS_TEXT } from '../../data/nutrientGuide.js'
import NutrientArt from '../NutrientArt.jsx'

// 유형 화면의 '부족할 수 있는 영양소' ((나)안, 데이터는 lib/nutrition.js의 typeNutrients)
//   🔹 나와 비슷한 사람들이 적게 먹은 영양소: 2줄 전부를 한 목록으로 (테두리 색 = 부족·주의)
//      내 유형이라 적은 것(유형특이·식사량영향)을 먼저, 같은 성별·나이대라 적은 것('흔함')을 뒤에. 항목마다 이유 표시
//   🔸 조사에서 섭취가 적었던 영양소: 공통 8개 (유형과 상관없어 맨 아래 작은 칩으로)
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
        <NutrientArt n={n} className="size-6" />
        {n.label}
      </button>
    </li>
  )
}

// 10명 중 몇 명인지 점 10개로 (색칠한 점 = 적게 먹는 사람)
function Dots({ of10, tone }) {
  const fill = tone === 'fair' ? 'bg-[#e0a92e]' : 'bg-primary-strong'
  return (
    <span aria-hidden="true" className="mt-1.5 flex gap-1">
      {Array.from({ length: 10 }, (_, i) => (
        <span key={i} className={`size-2.5 rounded-full ${i < of10 ? fill : 'bg-ink/10'}`} />
      ))}
    </span>
  )
}

const REASON = { type: '내 유형', peer: '성별·나이대' }

function PickRow({ n, onOpen }) {
  const reason = n.tag === '흔함' ? 'peer' : 'type'
  return (
    <li>
      <button
        type="button"
        onClick={() => onOpen(n)}
        className={`flex w-full items-center gap-3 rounded-card border-2 bg-white px-3.5 py-3 text-left active:scale-[0.98] ${BORDER[n.level.tone]}`}
      >
        <NutrientArt n={n} className="size-10" emojiClass="text-2xl" />
        <span className="min-w-0 flex-1">
          <span className="flex flex-wrap items-center gap-x-1.5">
            <b>{n.label}</b>
            <span className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${reason === 'type' ? 'bg-primary-soft text-primary-shade' : 'bg-cream text-ink-soft'}`}>
              {REASON[reason]}
            </span>
          </span>
          <Dots of10={n.of10} tone={n.level.tone} />
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
          <NutrientArt n={n} className="size-6" />
          {n.label}
        </>
      }
      aside={pick && <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-bold ${CHIP[n.level.tone]}`}>{n.level.label}</span>}
      onClose={onClose}
    >
      <p className="leading-relaxed">
        {pick ? (
          <>
            조사 자료로 추정하면 같은 유형·{sexLabel}·{ageLabel} <b>10명 중 약 {n.of10}명</b>이 {BASIS_TEXT[n.basis]}보다 적게 먹어요. 같은 성별·나이
            평균은 10명 중 {n.peerOf10}명이에요.
          </>
        ) : (
          <>조사에서 성인 절반 이상이 하루 식사로 {BASIS_TEXT[n.basis]}보다 적게 섭취한 영양소예요.</>
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

export default function TypeNutrients({ common, picks, sexLabel, ageLabel }) {
  const [open, setOpen] = useState(null)
  const close = useCallback(() => setOpen(null), [])
  const sorted = [...picks.filter((n) => n.tag !== '흔함'), ...picks.filter((n) => n.tag === '흔함')]

  // 해당 영양소가 없는 칸은 소제목째 숨긴다 (120칸 중 103칸이 '내 유형만 더 부족한 영양소 없음'이라 '없어요'만 보이게 되므로)
  return (
    <div className="space-y-5">
      {sorted.length > 0 && (
        <section>
          <h3 className="flex items-center gap-2 text-sm font-bold">
            <span aria-hidden="true" className="size-2.5 rounded-full bg-primary-strong" />
            같은 유형에서 섭취가 적었던 영양소
          </h3>
          <ul className="mt-2 space-y-2">
            {sorted.map((n) => (
              <PickRow key={n.key} n={n} onOpen={setOpen} />
            ))}
          </ul>
        </section>
      )}

      <section>
        <h3 className="flex items-center gap-2 text-sm font-bold">
          <span aria-hidden="true" className="size-2.5 rounded-full bg-[#e0a92e]" />조사에서 섭취가 적었던 영양소 {common.length}개
        </h3>
        <ul className="mt-2 flex flex-wrap gap-1.5">
          {common.map((n) => (
            <CommonChip key={n.key} n={n} onOpen={setOpen} />
          ))}
        </ul>
      </section>

      {open && <NutrientSheet n={open} sexLabel={sexLabel} ageLabel={ageLabel} onClose={close} />}
    </div>
  )
}
