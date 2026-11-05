import { useState } from 'react'

// 음식·영양소 그림: public/illust/{name}.webp → .png → 이모지 (그림이 아직 없으면 이모지 그대로)
//   그림은 bigskyyang/scripts/optimize_mascots.py가 WebP로 줄인다. 꾸밈용이라 화면 읽기 프로그램에는 읽히지 않는다
// name: 파일 이름 (확장자 없이, 예: 'nutrient_protein'), className: 그림 크기, emojiClass: 이모지일 때 글씨 크기
export default function Illust({ name, emoji, className = 'size-5', emojiClass = '' }) {
  const candidates = name ? [`/illust/${name}.webp`, `/illust/${name}.png`] : []
  const [tried, setTried] = useState({ name, i: 0 })
  const i = tried.name === name ? tried.i : 0
  const src = candidates[i]

  if (!src) {
    return (
      <span aria-hidden="true" className={emojiClass}>
        {emoji}
      </span>
    )
  }
  return (
    <img
      key={src}
      src={src}
      alt=""
      aria-hidden="true"
      draggable={false}
      onError={() => setTried({ name, i: i + 1 })}
      className={`inline-block shrink-0 object-contain ${className}`}
    />
  )
}
