// 설문 진행 막대: 영역(기본정보·신체활동·수면 …)마다 한 칸. 지난 영역은 꽉 차고, 지금 영역은 안에서 몇 번째인지만큼 찬다
//   percent: 전체 진행률 (화면 읽기 프로그램용), sections: 영역 수, current: 지금 영역 번호(0부터), fraction: 지금 영역 안 진행(0~1)
export default function ProgressBar({ percent, sections, current, fraction }) {
  return (
    <div role="progressbar" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100} aria-label="설문 진행률" className="flex gap-1">
      {Array.from({ length: sections }, (_, i) => (
        <div key={i} className="h-2 flex-1 overflow-hidden rounded-full bg-primary-soft">
          <div
            className="h-full rounded-full bg-primary-strong transition-[width] duration-300"
            style={{ width: `${i < current ? 100 : i === current ? fraction * 100 : 0}%` }}
          />
        </div>
      ))}
    </div>
  )
}
