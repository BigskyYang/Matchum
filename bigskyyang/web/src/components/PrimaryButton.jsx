import { Link } from 'react-router-dom'

// 화면 하단의 큰 버튼. to가 있으면 링크, 없으면 버튼으로 그린다
const BASE =
  'block w-full rounded-button py-5 text-center text-lg font-bold select-none transition-[translate,box-shadow,background-color] duration-100'
const ENABLED = 'bg-primary-strong text-white shadow-button active:translate-y-1 active:shadow-button-pressed'
const DISABLED = 'bg-primary-soft text-primary-shade/60 cursor-not-allowed'

export default function PrimaryButton({ to, disabled = false, className = '', children, ...props }) {
  const cls = `${BASE} ${disabled ? DISABLED : ENABLED} ${className}`
  if (to) {
    return (
      <Link to={to} className={cls} {...props}>
        {children}
      </Link>
    )
  }
  return (
    <button type="button" disabled={disabled} className={cls} {...props}>
      {children}
    </button>
  )
}

// 보조 버튼 (흰 배경)
export function SecondaryButton({ to, className = '', children, ...props }) {
  const cls = `block w-full rounded-button bg-white py-4 text-center font-semibold text-ink-soft shadow-soft select-none active:scale-[0.98] ${className}`
  if (to) {
    return (
      <Link to={to} className={cls} {...props}>
        {children}
      </Link>
    )
  }
  return (
    <button type="button" className={cls} {...props}>
      {children}
    </button>
  )
}
