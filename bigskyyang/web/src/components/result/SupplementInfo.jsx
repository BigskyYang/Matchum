import { useState } from 'react'
import { SUPPLEMENT_NOTICES } from '../../data/supplementInfo.js'

// 개인 결과의 '건강기능식품 정보' (데이터는 lib/supplements.js의 supplementInfo)
//   처음엔 접혀 있고, 펼치기 전에 임신·수유·질환·복용약을 한 번 확인한다 (응답은 저장하지 않음)
//   해당되면 제품 대신 상담 안내만 보여 준다. 제품은 순위 없이, 식약처 기능성 문구·주의사항 원문 그대로
const TARGET_BADGE = { 남성: '남성용', 여성: '여성용', 시니어: '시니어용' }

// 마지막 글자에 받침이 있으면 '은', 없으면 '는'
const eunNeun = (word) => {
  const code = word.charCodeAt(word.length - 1) - 0xac00
  return code >= 0 && code <= 11171 && code % 28 === 0 ? '는' : '은'
}

function ProductCard({ p }) {
  return (
    <li className="rounded-card border-2 border-cream bg-white px-4 py-3">
      <div className="flex items-start gap-2">
        <p className="min-w-0 flex-1 leading-snug font-bold">{p.name}</p>
        {TARGET_BADGE[p.target] && (
          <span className="shrink-0 rounded-full bg-lavender px-2 py-0.5 text-[0.7rem] font-bold">{TARGET_BADGE[p.target]}</span>
        )}
      </div>
      <p className="mt-0.5 text-xs text-ink-soft">제조사 {p.maker}</p>
      {(p.perDay || p.amount) && (
        <p className="mt-2 flex flex-wrap gap-1.5 text-xs">
          {p.perDay && <span className="rounded-full bg-cream px-2.5 py-1 font-semibold">{p.perDay}</span>}
          {p.amount && (
            <span className="rounded-full bg-cream px-2.5 py-1 font-semibold">
              1일 {p.amount}
              {p.dvPct != null && ` · 기준치의 ${p.dvPct}%`}
            </span>
          )}
        </p>
      )}
      <div className="mt-2.5 text-sm leading-relaxed">
        <p className="text-xs font-bold text-ink-soft">기능성 (식약처 인정 문구)</p>
        <p className="mt-0.5">{p.function}</p>
      </div>
      {p.caution && (
        <details className="mt-2 text-sm leading-relaxed">
          <summary className="cursor-pointer text-xs font-bold text-ink-soft">섭취 시 주의사항</summary>
          <p className="mt-1 whitespace-pre-line text-ink-soft">{p.caution}</p>
        </details>
      )}
      <p className="mt-2 text-[0.7rem] text-ink-faint">품목제조신고번호 {p.reportNo}</p>
    </li>
  )
}

function Products({ info }) {
  const [selected, setSelected] = useState(info.nutrients[0]?.key)
  const current = info.nutrients.find((n) => n.key === selected)

  return (
    <div>
      <p className="text-sm leading-relaxed">부족하기 쉬운 영양소를 채우는 데 이런 제품도 있어요.</p>
      {info.nutrients.length > 0 && (
        <div role="tablist" aria-label="영양소" className="mt-3 flex flex-wrap gap-1.5">
          {info.nutrients.map((n) => (
            <button
              key={n.key}
              type="button"
              role="tab"
              aria-selected={n.key === selected}
              onClick={() => setSelected(n.key)}
              className={`rounded-full px-3 py-1.5 text-sm font-bold active:scale-95 ${
                n.key === selected ? 'bg-primary-strong text-white' : 'bg-cream text-ink-soft'
              }`}
            >
              <span aria-hidden="true">{n.icon}</span> {n.label}
            </button>
          ))}
        </div>
      )}
      {!info.nutrients.length && (
        <p className="mt-3 text-sm text-ink-soft">부족 위험이 높은 편인 영양소가 없어 영양소별 제품 정보는 보여 드리지 않아요.</p>
      )}
      {current &&
        (current.products.length ? (
          <ul className="mt-3 space-y-2">
            {current.products.map((p) => (
              <ProductCard key={p.reportNo} p={p} />
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-ink-soft">{current.label} 제품 정보를 준비하고 있어요.</p>
        ))}
      {info.foodOnly.length > 0 && (
        <p className="mt-3 text-xs leading-relaxed text-ink-soft">
          {info.foodOnly.join('·')}
          {eunNeun(info.foodOnly.at(-1))} 음식으로 챙기는 영양소라 제품 정보를 보여 드리지 않아요.
        </p>
      )}
      {info.multivitamins.length > 0 && (
        <>
          <h3 className="mt-5 text-sm font-bold">한 번에 챙기고 싶다면: 종합비타민</h3>
          <ul className="mt-2 space-y-2">
            {info.multivitamins.map((p) => (
              <ProductCard key={p.reportNo} p={p} />
            ))}
          </ul>
        </>
      )}
      <ul className="mt-4 space-y-1 text-[0.7rem] leading-relaxed text-ink-faint">
        {SUPPLEMENT_NOTICES.map((t) => (
          <li key={t}>· {t}</li>
        ))}
        {info.source && <li>· 자료: {info.source}. 지금 판매 중인지는 확인하지 않았어요.</li>}
      </ul>
    </div>
  )
}

export default function SupplementInfo({ info }) {
  // closed → check(확인) → open(제품) 또는 consult(상담 안내)
  const [step, setStep] = useState('closed')

  if (!info.ready) {
    return (
      <p className="text-sm leading-relaxed text-ink-soft">
        음식으로 먼저 챙겨 보세요. 부족하기 쉬운 영양소의 건강기능식품 정보는 준비하고 있어요.
      </p>
    )
  }

  if (step === 'closed') {
    return (
      <div>
        <p className="text-sm leading-relaxed text-ink-soft">
          음식으로 먼저 챙기고, 더 알아보고 싶다면 부족하기 쉬운 영양소의 건강기능식품 정보를 참고로 볼 수 있어요.
        </p>
        <button
          type="button"
          onClick={() => setStep('check')}
          className="mt-3 w-full rounded-button bg-cream py-3.5 font-bold text-ink active:scale-[0.98]"
        >
          건강기능식품 정보 보기
        </button>
      </div>
    )
  }

  if (step === 'check') {
    return (
      <div className="rounded-card bg-butter/60 px-4 py-4">
        <p className="font-bold">제품 정보를 보기 전에 확인해 주세요</p>
        <p className="mt-1.5 text-sm leading-relaxed">
          임신·수유 중이거나, 치료 중인 질환이 있거나, 약을 드시고 있나요? 해당된다면 제품 정보보다 의사·약사와 먼저
          이야기해 보시길 권해요.
        </p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setStep('open')}
            className="rounded-button bg-white py-3 text-sm font-bold active:scale-[0.98]"
          >
            해당 없어요
          </button>
          <button
            type="button"
            onClick={() => setStep('consult')}
            className="rounded-button bg-white py-3 text-sm font-bold active:scale-[0.98]"
          >
            해당돼요
          </button>
        </div>
        <p className="mt-2 text-[0.7rem] text-ink-soft">이 선택은 저장하지 않아요.</p>
      </div>
    )
  }

  if (step === 'consult') {
    return (
      <div>
        <p className="text-sm leading-relaxed">
          임신·수유 중이거나 질환·복용약이 있으면 필요한 영양소와 주의할 점이 달라질 수 있어요. 건강기능식품은 의사·약사와
          먼저 이야기해 보세요. 위의 음식 안내는 그대로 참고하셔도 좋아요.
        </p>
        <button type="button" onClick={() => setStep('check')} className="mt-3 text-sm font-semibold text-ink-soft underline">
          다시 선택하기
        </button>
      </div>
    )
  }

  return <Products info={info} />
}
