import WheelPicker from './WheelPicker.jsx'
import { hourLabel, range } from '../../lib/inputs.js'

// 문항 유형별 휠 입력. 모든 값은 언제나 올바른 값이라 '다음'을 바로 누를 수 있다

function Wheels({ children }) {
  return <div className="flex items-center gap-2 rounded-card bg-white px-4 py-3 shadow-soft">{children}</div>
}

const Unit = ({ children }) => <span className="shrink-0 text-base font-semibold text-ink-soft">{children}</span>

const pad = (n) => String(n).padStart(2, '0')
const MINUTE_OPTIONS = range(0, 50, 10).map((m) => ({ label: pad(m), value: m }))
export function NumberWheel({ value, onChange, min, max, unit }) {
  return (
    <Wheels>
      <WheelPicker
        label={unit}
        className="flex-1"
        options={range(min, max).map((v) => ({ label: `${v}`, value: v }))}
        value={value}
        onChange={onChange}
      />
      <Unit>{unit}</Unit>
    </Wheels>
  )
}

// 시각 'HH:MM'. 시 목록은 hourStart부터 24시간을 돈다 (예: 취침은 오후 6시부터)
export function TimeWheel({ value, onChange, hourStart = 0 }) {
  const [h, m] = value.split(':').map(Number)
  const hours = range(0, 23).map((i) => (hourStart + i) % 24)
  return (
    <Wheels>
      <WheelPicker
        label="시"
        className="flex-[1.6]"
        options={hours.map((v) => ({ label: hourLabel(v), value: v }))}
        value={h}
        onChange={(v) => onChange(`${pad(v)}:${pad(m)}`)}
      />
      <WheelPicker
        label="분"
        className="flex-1"
        options={MINUTE_OPTIONS}
        value={m - (m % 10)}
        onChange={(v) => onChange(`${pad(h)}:${pad(v)}`)}
      />
      <Unit>분</Unit>
    </Wheels>
  )
}

// 생년월일 'YYYY-MM-DD' 휠 (년·월·일). 일 목록은 그 달의 날 수만큼, 달을 바꿔 날이 넘치면 그 달 마지막 날로 맞춘다
//   아이폰 기본 날짜 칸은 화면 밖으로 넘치고 달력 아이콘도 안 보여서 휠로 고르게 한다
const daysIn = (y, m) => new Date(y, m, 0).getDate()
const numbers = (from, to) => range(from, to).map((v) => ({ label: `${v}`, value: v }))
export function DateWheel({ value, onChange, minYear, maxYear }) {
  const [y, m, d] = value.split('-').map(Number)
  const last = daysIn(y, m)
  const set = (yy, mm, dd) => onChange(`${yy}-${pad(mm)}-${pad(Math.min(dd, daysIn(yy, mm)))}`)
  return (
    <Wheels>
      <WheelPicker label="년" className="flex-[1.5]" options={numbers(minYear, maxYear)} value={y} onChange={(v) => set(v, m, d)} />
      <Unit>년</Unit>
      <WheelPicker label="월" className="flex-1" options={numbers(1, 12)} value={m} onChange={(v) => set(y, v, d)} />
      <Unit>월</Unit>
      <WheelPicker label="일" className="flex-1" options={numbers(1, last)} value={Math.min(d, last)} onChange={(v) => set(y, m, v)} />
      <Unit>일</Unit>
    </Wheels>
  )
}

// 시간 + 분 → 분 단위 숫자
export function DurationWheel({ value, onChange, per, maxHours }) {
  const h = Math.floor(value / 60)
  const m = value % 60
  return (
    <div>
      <p className="mb-2 text-center text-sm font-semibold text-ink-soft">{per}</p>
      <Wheels>
        <WheelPicker
          label="시간"
          className="flex-1"
          options={range(0, maxHours).map((v) => ({ label: `${v}`, value: v }))}
          value={h}
          onChange={(v) => onChange(Math.min(v * 60 + m, maxHours * 60))}
        />
        <Unit>시간</Unit>
        <WheelPicker
          label="분"
          className="flex-1"
          options={MINUTE_OPTIONS}
          value={m - (m % 10)}
          onChange={(v) => onChange(Math.min(h * 60 + v, maxHours * 60))}
        />
        <Unit>분</Unit>
      </Wheels>
    </div>
  )
}
