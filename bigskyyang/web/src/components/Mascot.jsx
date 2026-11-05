import { useState } from 'react'

const prefersReducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

// 마스코트를 보여준다. 아래 순서로 시도하고, 파일이 없거나 안 열리면 다음 것으로 넘어간다.
//   움직이는 이미지: {gif}.webp → {gif}.gif   (크림색 배경 위에서 만든 애니메이션이라 앱 배경과 이어져 보인다)
//   정지 이미지:     {name}.webp → {name}.png
//   모두 실패:       원형 💊 placeholder
// WebP는 용량이 훨씬 작아 먼저 쓴다 (bigskyyang/scripts/optimize_mascots.py가 만든다).
// name:  public/mascot/{name}  ('start' | 'thinking' | 'happy' | 'default' | 'type_N1' ~ 'type_O3' 유형별 그림)
// gif:   public/mascot/{gif}   (선택). '동작 줄이기'를 켠 사용자에게는 정지 이미지를 보여준다.
// float: 정지 이미지일 때 둥실거리는 애니메이션 (움직이는 이미지는 스스로 움직이므로 적용하지 않음)
// size:  'md'(176px, 기본) | 'sm'(96px, 설문 화면 등)
// fallback: name 그림이 아직 없을 때 대신 쓸 그림 (예: 새 표정 'analyzing'이 오기 전에는 'thinking')
const SIZES = { md: 'size-44', sm: 'size-24' }
// 움직이는 이미지는 캐릭터 주변 여백이 정지 이미지보다 넓어서 박스를 크게 잡아야 캐릭터 크기가 비슷해진다
const ANIMATED_SIZES = { md: 'size-64', sm: 'size-32' }

export default function Mascot({ name = 'default', gif, fallback, float = false, size = 'md', className = '' }) {
  const animated = gif && !prefersReducedMotion() ? [`/mascot/${gif}.webp`, `/mascot/${gif}.gif`] : []
  const candidates = [...animated, `/mascot/${name}.webp`, `/mascot/${name}.png`, ...(fallback ? [`/mascot/${fallback}.webp`, `/mascot/${fallback}.png`] : [])]
  const [tried, setTried] = useState(0)
  const src = candidates[tried]

  const still = `${SIZES[size]} shrink-0 ${float ? 'animate-float motion-reduce:animate-none' : ''} ${className}`

  if (!src) {
    return (
      <div
        role="img"
        aria-label="마스코트"
        className={`${still} flex items-center justify-center rounded-full bg-primary-soft shadow-soft ring-8 ring-white/70 ${size === 'sm' ? 'text-4xl' : 'text-7xl'}`}
      >
        💊
      </div>
    )
  }

  const box = tried < animated.length ? `${ANIMATED_SIZES[size]} shrink-0 ${className}` : still
  return (
    <img
      key={src}
      src={src}
      alt="마스코트"
      draggable={false}
      onError={() => setTried((t) => t + 1)}
      className={`${box} object-contain`}
    />
  )
}
