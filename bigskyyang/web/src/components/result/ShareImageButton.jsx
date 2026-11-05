import { useEffect, useState } from 'react'
import { SERVICE_NAME } from '../../config.js'
import { FORMATS, drawShareImage } from '../../lib/shareImage.js'
import BottomSheet from '../BottomSheet.jsx'
import Icon from '../Icon.jsx'

// '이미지' 버튼 → 공유 이미지 미리보기 창 (스토리 9:16 / 정사각형 1:1)
//   휴대폰 공유 창에 파일을 넘길 수 있으면 '이미지 공유하기', 아니면 파일로 저장
//   카카오톡 안 브라우저처럼 둘 다 막힌 곳에서는 미리보기 이미지를 길게 눌러 저장할 수 있다
function PreviewSheet({ r, onClose }) {
  const [format, setFormat] = useState('story')
  const [drawn, setDrawn] = useState(null) // { format, blob, url }
  const [note, setNote] = useState('')

  useEffect(() => {
    let url = null
    let alive = true
    drawShareImage(r, format, { serviceName: SERVICE_NAME })
      .then((blob) => {
        if (!alive) return
        url = URL.createObjectURL(blob)
        setDrawn({ format, blob, url })
      })
      .catch(() => alive && setNote('이미지를 만들지 못했어요. 잠시 뒤에 다시 해 주세요.'))
    return () => {
      alive = false
      if (url) URL.revokeObjectURL(url)
    }
  }, [r, format])

  // 비율을 바꾸면 새로 그리는 동안은 '만들고 있어요'
  const image = drawn?.format === format ? drawn : null
  const fileName = `NBTI_${r.name.replace(/\s+/g, '_')}_${format}.png`
  const file = image && new File([image.blob], fileName, { type: 'image/png' })
  const canShareFile = Boolean(file && navigator.canShare?.({ files: [file] }))

  const save = async () => {
    if (!image) return
    setNote('')
    if (canShareFile) {
      try {
        await navigator.share({ files: [file], title: SERVICE_NAME })
      } catch {
        // 공유 창을 닫은 경우
      }
      return
    }
    const a = document.createElement('a')
    a.href = image.url
    a.download = fileName
    document.body.appendChild(a)
    a.click()
    a.remove()
    setNote('이미지를 저장했어요. 저장이 안 되면 위 이미지를 길게 눌러 저장해 주세요.')
  }

  return (
    <BottomSheet title="공유 이미지" onClose={onClose}>
      <div role="radiogroup" aria-label="이미지 비율" className="grid grid-cols-2 gap-2">
        {Object.entries(FORMATS).map(([key, f]) => (
          <button
            key={key}
            type="button"
            role="radio"
            aria-checked={format === key}
            onClick={() => setFormat(key)}
            className={`rounded-button py-2.5 text-sm font-bold ${format === key ? 'bg-primary-shade text-white' : 'bg-cream text-ink-soft'}`}
          >
            {f.label}
          </button>
        ))}
      </div>
      <div className="mt-4 flex justify-center">
        {image ? (
          <img
            src={image.url}
            alt={`${r.name} 공유 이미지 미리보기`}
            className={`rounded-card shadow-soft ${format === 'story' ? 'max-h-[52dvh]' : 'max-h-[44dvh]'} w-auto`}
          />
        ) : (
          <p className="py-16 text-sm text-ink-soft">{note || '이미지를 만들고 있어요…'}</p>
        )}
      </div>
      <button
        type="button"
        onClick={save}
        disabled={!image}
        className="mt-4 flex w-full items-center justify-center gap-2 rounded-button bg-primary-strong py-3.5 text-xl font-bold text-white shadow-button active:translate-y-1 active:shadow-button-pressed disabled:bg-ink/10 disabled:text-ink-soft disabled:shadow-none"
      >
        <Icon name={canShareFile ? 'share' : 'download'} size={22} />
        {canShareFile ? '이미지 공유하기' : '이미지 저장하기'}
      </button>
      {image && note && (
        <p role="status" className="mt-2 text-center text-xs text-ink-soft">
          {note}
        </p>
      )}
      <p className="mt-2 text-center text-xs text-ink-faint">이미지에는 유형만 담기고 내 응답은 들어가지 않아요.</p>
    </BottomSheet>
  )
}

export default function ShareImageButton({ r, className = '' }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={`flex shrink-0 items-center justify-center gap-1 rounded-button bg-white px-4 font-bold shadow-soft active:scale-[0.98] ${className}`}
      >
        <Icon name="photo" size={20} /> 이미지
      </button>
      {open && <PreviewSheet r={r} onClose={() => setOpen(false)} />}
    </>
  )
}
