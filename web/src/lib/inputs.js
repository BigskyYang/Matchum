// 휠 입력용 보조 함수

// from부터 to까지 step 간격의 숫자 배열 (to 포함). step이 음수면 내려간다
export function range(from, to, step = 1) {
  const out = []
  for (let v = from; step > 0 ? v <= to : v >= to; v += step) out.push(v)
  return out
}

// 0~23시 → '오전 7시', '오후 10시', '밤 12시'
export function hourLabel(h) {
  if (h === 0) return '밤 12시'
  if (h === 12) return '낮 12시'
  return h < 12 ? `오전 ${h}시` : `오후 ${h - 12}시`
}
