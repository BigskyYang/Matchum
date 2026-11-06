import { useState } from 'react'
import { Link } from 'react-router-dom'
import BottomSheet from '../BottomSheet.jsx'
import Icon from '../Icon.jsx'

// 개인 결과의 '비타민 D와 내 생활' (데이터는 재준님 함수 → lib/vitaminD.js vitaminDInfo)
//   재준님 표시 순서(DISPLAY_POLICY.md): 제목 → 요약 → 다음 할 일 → 버튼(식품·야외활동 순서는 primaryActionId, 제품은 항상 마지막) → 안내 문구
//   - 안내 문구는 작은 글씨로 늘 보이게 (숨기거나 눌러야 보이게 하지 않는다)
//   - 응답 정리(summaryCards)는 '내 답 보기'로 접어 둔다. 본문 요약과 같은 문구를 펼친 채 두 번 보여 주지 않는다
//   - 제품은 누를 때만 일반 제품 목록(/supplements?n=vitamin_d)을 연다. 개인 추천·필요 표시 없음
//   - 점수·등급·부족 예측 없음. 기존 영양소 목록에 비타민 D를 넣지 않는다
const INFO_KEY = { food_information: 'foodInformation', outdoor_information: 'outdoorInformation' }
const INFO_ICON = { food_information: 'meal', outdoor_information: 'sunrise' }

export default function VitaminDCard({ info }) {
  const [open, setOpen] = useState(null) // 'food_information' | 'outdoor_information'
  const { guidance } = info
  const sheet = open && info[INFO_KEY[open]]

  return (
    <div>
      <p className="font-bold leading-snug">{guidance.headline}</p>
      <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{info.emptyMessage ?? guidance.summary}</p>
      <p className="mt-2 text-sm leading-relaxed">{guidance.nextStep}</p>

      <ul className="mt-3 space-y-2">
        {info.actions.map((a) =>
          a.id === 'product_information' ? (
            <li key={a.id}>
              <Link
                to="/supplements?n=vitamin_d"
                className="flex items-center gap-2 rounded-card bg-cream px-4 py-3 text-sm font-semibold text-ink-soft active:scale-[0.99]"
              >
                <Icon name="pill" size={18} className="shrink-0" />
                <span className="flex-1">{a.label}</span>
                <Icon name="next" size={16} className="shrink-0 text-ink-faint" />
              </Link>
            </li>
          ) : (
            <li key={a.id}>
              <button
                type="button"
                onClick={() => setOpen(a.id)}
                className="flex w-full items-center gap-2 rounded-card border-2 border-primary-soft bg-white px-4 py-3 text-left font-bold active:scale-[0.99]"
              >
                <Icon name={INFO_ICON[a.id]} size={20} className="shrink-0 text-primary-shade" />
                <span className="flex-1">{a.label}</span>
                <Icon name="next" size={16} className="shrink-0 text-ink-faint" />
              </button>
            </li>
          ),
        )}
      </ul>

      {info.notices.map((t) => (
        <p key={t} className="mt-2 text-xs text-ink-faint">
          {t}
        </p>
      ))}

      {info.summaryCards.length > 0 && (
        <details className="mt-1 text-sm text-ink-soft">
          <summary className="cursor-pointer py-2 font-bold">내 답 보기</summary>
          <ul className="space-y-1.5">
            {info.summaryCards.map((c) => (
              <li key={c.id} className="rounded-card bg-cream px-3.5 py-2.5">
                {c.text}
              </li>
            ))}
          </ul>
        </details>
      )}

      {sheet && (
        <BottomSheet title={sheet.title} onClose={() => setOpen(null)}>
          <p className="leading-relaxed">{sheet.text}</p>
        </BottomSheet>
      )}
    </div>
  )
}
