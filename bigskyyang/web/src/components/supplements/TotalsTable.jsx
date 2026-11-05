// 함께 먹을 때 성분별 하루 합계와 상한섭취량 (데이터는 lib/supplements.js dailyTotals)
//   고른 제품 창과 '내가 먹는 건강기능식품' 화면이 같이 쓴다
export default function TotalsTable({ totals }) {
  const over = totals.filter((x) => x.over)
  return (
    <>
      <p className={`text-sm ${over.length ? 'font-bold text-primary-shade' : 'text-ink-soft'}`}>
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
    </>
  )
}
