import { ICONS } from './icons.js'

// label이 있으면 화면 읽기 프로그램이 읽고, 없으면 꾸밈으로 숨긴다
export default function Icon({ name, size = 20, stroke = 1.8, className = '', label }) {
  const Svg = ICONS[name]
  if (!Svg) return null
  return (
    <Svg
      size={size}
      stroke={stroke}
      className={`shrink-0 ${className}`}
      aria-hidden={label ? undefined : true}
      aria-label={label}
      role={label ? 'img' : undefined}
    />
  )
}
