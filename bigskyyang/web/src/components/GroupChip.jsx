// 대분류 4색 (디자인 시안 A안): 유형 결과·짝꿍·유형 보기에서 같은 색으로 대분류를 알려 준다
//   점은 기본색, 칩 바탕은 soft, 글씨는 deep (모두 명암비 4.5:1 이상) · 색은 index.css의 --color-group-*
const TONE = {
  N: { chip: 'bg-group-n-soft text-group-n-deep', dot: 'bg-group-n' },
  O: { chip: 'bg-group-o-soft text-group-o-deep', dot: 'bg-group-o' },
  S: { chip: 'bg-group-s-soft text-group-s-deep', dot: 'bg-group-s' },
  A: { chip: 'bg-group-a-soft text-group-a-deep', dot: 'bg-group-a' },
}

const dotOf = (code) => TONE[code]?.dot ?? 'bg-ink-faint'

// 대분류 색 점 하나 (제목 옆 등)
export function GroupDot({ code, className = 'size-2' }) {
  return <span aria-hidden="true" className={`rounded-full ${dotOf(code)} ${className}`} />
}

export default function GroupChip({ code, name, className = '' }) {
  const tone = TONE[code]
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-sm font-bold ${tone?.chip ?? ''} ${className}`}>
      <GroupDot code={code} />
      {name}
    </span>
  )
}
