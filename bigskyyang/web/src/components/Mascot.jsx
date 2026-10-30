import { useState } from 'react'

// public/mascot/{name}.png 를 보여준다. 이미지가 없거나 깨지면 같은 크기의 원형 💊 placeholder로 대신한다.
// name: 'start' | 'thinking' | 'happy' | 'default'
export default function Mascot({ name = 'default', className = '' }) {
  const src = `/mascot/${name}.png`
  const [failedSrc, setFailedSrc] = useState(null)

  const box = `size-44 shrink-0 ${className}`

  if (failedSrc === src) {
    return (
      <div
        role="img"
        aria-label="마스코트"
        className={`${box} flex items-center justify-center rounded-full bg-primary-soft text-7xl shadow-soft ring-8 ring-white/70`}
      >
        💊
      </div>
    )
  }

  return (
    <img src={src} alt="마스코트" draggable={false} onError={() => setFailedSrc(src)} className={`${box} object-contain`} />
  )
}
