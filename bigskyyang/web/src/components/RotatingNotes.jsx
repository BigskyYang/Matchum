import { useEffect, useState } from 'react'

const prefersReducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

// 한 줄 안내를 번갈아 보여준다. 지금 줄은 위로 사라지고 다음 줄이 아래에서 올라온다.
// 바뀔 때마다 key가 바뀌어 애니메이션(index.css의 note-in/note-out)이 처음부터 다시 재생된다.
// '동작 줄이기'를 켠 사용자에게는 움직이지 않고 모든 줄을 한꺼번에 보여준다.
// items: 화면에 보일 내용(React 노드) 배열, interval: 바뀌는 간격(ms)
export default function RotatingNotes({ items, interval = 3200, className = '' }) {
  const [tick, setTick] = useState(0)
  const [still] = useState(prefersReducedMotion)

  useEffect(() => {
    if (still || items.length < 2) return undefined
    const id = setInterval(() => setTick((t) => t + 1), interval)
    return () => clearInterval(id)
  }, [still, items.length, interval])

  if (still) {
    return (
      <ul className={`space-y-1 ${className}`}>
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    )
  }

  const active = tick % items.length
  const leaving = (tick - 1 + items.length) % items.length
  const line = 'absolute inset-x-0 top-0 leading-5 whitespace-nowrap'
  return (
    <div className={className}>
      {/* 화면 읽기 프로그램에는 바뀔 때마다 읽지 않고 모든 줄을 한 번만 읽어 준다 */}
      <ul className="sr-only">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
      <div aria-hidden="true" className="relative h-5 overflow-hidden">
        {tick > 0 && (
          <p key={`out-${tick}`} className={`${line} animate-note-out`}>
            {items[leaving]}
          </p>
        )}
        <p key={`in-${tick}`} className={`${line} ${tick > 0 ? 'animate-note-in' : ''}`}>
          {items[active]}
        </p>
      </div>
    </div>
  )
}
