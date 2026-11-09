// 만든 이미지를 휴대폰에 넘긴다: 공유 창에 파일을 넘길 수 있으면 공유, 아니면 파일로 저장
//   카카오톡 안 브라우저처럼 둘 다 막힌 곳에서는 미리보기 이미지를 길게 눌러 저장하도록 화면에서 안내한다
export const imageFile = (blob, fileName) => new File([blob], fileName, { type: 'image/png' })
export const canShareFile = (file) => Boolean(file && navigator.canShare?.({ files: [file] }))

// → 'shared' | 'cancelled' | 'saved'
//   파일만 넘긴다. title·text를 같이 넘기면 카카오톡 등에서 이미지와 별도로 글 메시지가 한 번 더 보내진다
export async function shareOrSave(blob, fileName) {
  const file = imageFile(blob, fileName)
  if (canShareFile(file)) {
    try {
      await navigator.share({ files: [file] })
      return 'shared'
    } catch {
      return 'cancelled'
    }
  }
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
  return 'saved'
}
