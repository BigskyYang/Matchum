import { useState } from 'react'

const prefersReducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

// 마스코트를 보여준다. 우선순위: 움직이는 GIF → 정지 이미지 → 원형 💊 placeholder
// name: public/mascot/{name}.png  ('start' | 'thinking' | 'happy' | 'default')
// gif:  public/mascot/{gif}.gif (선택). 크림색 배경 위에서 만든 애니메이션이라 앱 배경과 이어져 보인다.
//       '동작 줄이기'를 켠 사용자에게는 정지 이미지를 보여준다.
// float: 정지 이미지일 때 둥실거리는 애니메이션 (GIF는 스스로 움직이므로 적용하지 않음)
export default function Mascot({ name = 'default', gif, float = false, className = '' }) {
  const imageSrc = `/mascot/${name}.png`
  const gifSrc = gif && !prefersReducedMotion() ? `/mascot/${gif}.gif` : null
  const [failed, setFailed] = useState([])
  const fail = (src) => setFailed((prev) => [...prev, src])

  if (gifSrc && !failed.includes(gifSrc)) {
    return (
      // GIF는 캐릭터 주변 여백이 PNG보다 넓어서 박스를 크게 잡아야 캐릭터 크기가 비슷해진다
      <img
        src={gifSrc}
        alt="마스코트"
        draggable={false}
        onError={() => fail(gifSrc)}
        className={`size-64 shrink-0 object-contain ${className}`}
      />
    )
  }

  const box = `size-44 shrink-0 ${float ? 'animate-float motion-reduce:animate-none' : ''} ${className}`

  if (failed.includes(imageSrc)) {
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
    <img src={imageSrc} alt="마스코트" draggable={false} onError={() => fail(imageSrc)} className={`${box} object-contain`} />
  )
}
