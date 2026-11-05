import { useState } from 'react'
import { SERVICE_NAME } from '../../config.js'
import Icon from '../Icon.jsx'

// 유형 결과 공유: 휴대폰 공유 창(Web Share API), 안 되면 링크를 복사하고 잠깐 알려 준다
//   응답은 서버에 없어서 결과 화면 자체가 아니라 검사 첫 화면 주소와 내 유형 이름을 보낸다
export default function ShareButton({ typeName }) {
  const [copied, setCopied] = useState(false)

  const share = async () => {
    const url = window.location.origin
    const text = `나는 '${typeName}'! 나의 생활습관 유형은? - ${SERVICE_NAME}`
    try {
      if (navigator.share) {
        await navigator.share({ title: SERVICE_NAME, text, url })
        return
      }
      await navigator.clipboard.writeText(`${text} ${url}`)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // 공유 창을 닫았거나 복사가 막힌 경우: 아무것도 하지 않는다
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={share}
        className="flex shrink-0 items-center justify-center gap-1 rounded-button bg-white px-5 font-bold shadow-soft active:scale-[0.98]"
      >
        <Icon name="share" size={20} /> 공유
      </button>
      <span role="status" className="sr-only">
        {copied ? '링크를 복사했어요' : ''}
      </span>
      {copied && (
        <p aria-hidden="true" className="absolute -top-11 left-1/2 -translate-x-1/2 rounded-full bg-ink px-4 py-2 text-sm text-white">
          링크를 복사했어요
        </p>
      )}
    </>
  )
}
