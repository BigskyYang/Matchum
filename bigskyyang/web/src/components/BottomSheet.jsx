import { useEffect, useId, useRef } from 'react'

// 화면 아래에서 올라오는 창 (자세한 설명·근거는 화면에 늘어놓지 않고 여기서 보여 준다)
//   닫기: ✕ 버튼, 어두운 바깥 누르기, Esc. 열려 있는 동안 뒤 화면은 스크롤되지 않는다
//   title: 제목 (아이콘 포함 가능), aside: 제목 옆에 붙일 것 (예: 등급 배지)
export default function BottomSheet({ title, aside, onClose, children }) {
  const titleId = useId()
  const closeRef = useRef(null)
  useEffect(() => {
    closeRef.current?.focus()
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = overflow
    }
  }, [onClose])

  return (
    <div className="fixed inset-0 z-20 flex items-end justify-center">
      <button
        type="button"
        aria-label="닫기"
        tabIndex={-1}
        onClick={onClose}
        className="absolute inset-0 animate-fade-in bg-ink/40 motion-reduce:animate-none"
      />
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative max-h-[85dvh] w-full max-w-app animate-sheet-up overflow-y-auto rounded-t-[1.75rem] bg-white px-6 pt-3 pb-[max(1.5rem,env(safe-area-inset-bottom))] shadow-soft motion-reduce:animate-none"
      >
        <div aria-hidden="true" className="mx-auto mb-3 h-1 w-10 rounded-full bg-ink/15" />
        <div className="flex items-center gap-2">
          <h3 id={titleId} className="flex min-w-0 flex-1 items-center gap-2 text-xl font-extrabold">
            {title}
          </h3>
          {aside}
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            aria-label="닫기"
            className="flex size-11 shrink-0 items-center justify-center rounded-full text-xl text-ink-soft active:bg-cream"
          >
            ✕
          </button>
        </div>
        <div className="mt-3">{children}</div>
      </section>
    </div>
  )
}
