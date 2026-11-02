export default function ProgressBar({ percent }) {
  return (
    <div
      role="progressbar"
      aria-valuenow={percent}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label="설문 진행률"
      className="h-2.5 w-full overflow-hidden rounded-full bg-primary-soft"
    >
      <div className="h-full rounded-full bg-primary-strong transition-[width] duration-300" style={{ width: `${percent}%` }} />
    </div>
  )
}
