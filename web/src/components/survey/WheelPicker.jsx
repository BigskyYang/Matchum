import { useEffect, useLayoutEffect, useRef } from 'react'

// 휴대폰 알람 시간 고르듯 위아래로 드래그해서 고르는 휠 한 줄.
// options: [{ label, value }], 가운데 칸에 멈춘 보기가 선택된다.
// 위·아래 끝이 없이 무한 반복된다: 보기 목록을 여러 벌 이어 붙여 그리고, 스크롤이 멈추면
// 같은 값이 있는 가운데 벌로 몰래 옮겨 둔다.
// 터치는 브라우저 기본 스크롤, PC 마우스는 끌어서 움직일 수 있게 따로 처리한다.
const ITEM_H = 44
const VISIBLE = 5 // 홀수
const PAD = ((VISIBLE - 1) / 2) * ITEM_H
const MIN_ROWS = 60 // 한 번에 세게 넘겨도 끝에 닿지 않을 만큼

const mod = (a, n) => ((a % n) + n) % n

export default function WheelPicker({ options, value, onChange, label, className = '' }) {
  const ref = useRef(null)
  const drag = useRef(null)
  const settle = useRef(0)
  const n = options.length
  // 이어 붙일 벌 수 (홀수, 최소 5)
  const copies = Math.max(5, Math.ceil(MIN_ROWS / n)) | 1
  const mid = Math.floor(copies / 2)
  const index = Math.max(
    0,
    options.findIndex((o) => o.value === value),
  )
  const rowOf = (el) => Math.round(el.scrollTop / ITEM_H)

  // 처음 그릴 때는 무조건, 그 뒤로는 바깥에서 값이 바뀌었을 때만(예: 2월 30일 → 28일) 가운데 벌의 해당 칸으로 맞춘다.
  // 사용자가 넘기는 중에 고른 값은 이미 화면 위치와 같으므로 건드리지 않는다
  const placed = useRef(false)
  useLayoutEffect(() => {
    const el = ref.current
    if (!el) return
    if (!placed.current || mod(rowOf(el), n) !== index) el.scrollTop = (mid * n + index) * ITEM_H
    placed.current = true
  }, [index, n, mid])

  useEffect(() => () => clearTimeout(settle.current), [])

  const pick = (row) => {
    const opt = options[mod(row, n)]
    if (opt.value !== value) onChange(opt.value)
  }

  // 멈춘 뒤: 가까운 칸으로 정렬하고, 가운데 벌을 벗어났으면 같은 값의 가운데 벌 칸으로 옮긴다
  const recenter = () => {
    const el = ref.current
    const row = rowOf(el)
    const center = mid * n + mod(row, n)
    if (row !== center) el.scrollTop = center * ITEM_H
    else el.scrollTo({ top: row * ITEM_H, behavior: 'smooth' })
  }

  const onScroll = () => {
    pick(rowOf(ref.current))
    clearTimeout(settle.current)
    settle.current = setTimeout(() => {
      if (!drag.current) recenter()
    }, 150)
  }

  const onPointerDown = (e) => {
    if (e.pointerType !== 'mouse') return
    const el = ref.current
    drag.current = { y: e.clientY, top: el.scrollTop, moved: false }
    el.style.scrollSnapType = 'none'
    el.setPointerCapture(e.pointerId)
  }
  const onPointerMove = (e) => {
    if (!drag.current) return
    const dy = e.clientY - drag.current.y
    if (Math.abs(dy) > 3) drag.current.moved = true
    ref.current.scrollTop = drag.current.top - dy
  }
  const onPointerUp = () => {
    if (!drag.current) return
    const el = ref.current
    drag.current = null
    el.style.scrollSnapType = ''
    el.scrollTo({ top: rowOf(el) * ITEM_H, behavior: 'smooth' })
  }

  const onKeyDown = (e) => {
    if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return
    e.preventDefault()
    const next = rowOf(ref.current) + (e.key === 'ArrowDown' ? 1 : -1)
    ref.current.scrollTo({ top: next * ITEM_H, behavior: 'smooth' })
    pick(next)
  }

  const rows = []
  for (let c = 0; c < copies; c++) {
    options.forEach((opt, i) => {
      const row = c * n + i
      const selected = i === index
      rows.push(
        <div
          key={row}
          role="option"
          aria-selected={selected}
          // 스크린리더에는 가운데 벌 한 벌만 읽힌다
          aria-hidden={c !== mid || undefined}
          onClick={() => {
            if (drag.current?.moved) return
            ref.current.scrollTo({ top: row * ITEM_H, behavior: 'smooth' })
          }}
          className={`flex snap-center items-center justify-center text-xl select-none ${
            selected ? 'font-bold text-ink' : 'font-medium text-ink-faint'
          }`}
          style={{ height: ITEM_H }}
        >
          {opt.label}
        </div>,
      )
    })
  }

  return (
    <div className={`relative ${className}`} style={{ height: ITEM_H * VISIBLE }}>
      {/* 가운데 선택 칸 */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 rounded-button bg-primary-soft"
        style={{ top: PAD, height: ITEM_H }}
      />
      <div
        ref={ref}
        role="listbox"
        aria-label={label}
        tabIndex={0}
        onScroll={onScroll}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onKeyDown={onKeyDown}
        className="relative h-full snap-y snap-mandatory overflow-y-scroll overscroll-contain rounded-button outline-none [scrollbar-width:none] focus-visible:ring-2 focus-visible:ring-primary-strong [&::-webkit-scrollbar]:hidden"
        style={{
          paddingBlock: PAD,
          maskImage: 'linear-gradient(transparent, black 30%, black 70%, transparent)',
          cursor: 'grab',
        }}
      >
        {rows}
      </div>
    </div>
  )
}
