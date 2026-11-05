// 함께 먹을 때 성분별 하루 합계와 상한섭취량 (데이터는 lib/supplements.js dailyTotals)
//   고른 제품 창과 '내가 먹는 건강기능식품' 화면이 같이 쓴다
import { UL_NOTICES } from '../../data/supplementInfo.js'
import { totalsMessage } from '../../lib/supplements.js'

export default function TotalsTable({ totals, headroom = [] }) {
  const over = totals.filter((x) => x.over)
  return (
    <>
      <p className={`text-sm ${over.length ? 'font-bold text-primary-shade' : 'text-ink-soft'}`}>
        {totalsMessage(totals)}
      </p>
      {headroom.length > 0 && (
        <details className="mt-2 text-xs leading-relaxed text-ink-soft">
          <summary className="cursor-pointer font-semibold">상한 여유가 적은 제품 {headroom.length}개 · 성분 중복 확인</summary>
          <ul className="mt-2 space-y-1">
            {headroom.map((p) => <li key={p.id}>{p.name} ({p.halfUlIngredients})</li>)}
          </ul>
        </details>
      )}
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
        {UL_NOTICES[0]}
      </p>
      <details className="mt-2 text-xs leading-relaxed text-ink-soft">
        <summary className="cursor-pointer font-semibold">상한 기준 자세히</summary>
        {UL_NOTICES.slice(1).map((notice) => <p key={notice} className="mt-2">{notice}</p>)}
      </details>
    </>
  )
}
