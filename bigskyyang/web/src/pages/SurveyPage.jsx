import { Link } from 'react-router-dom'
import Mascot from '../components/Mascot.jsx'

// 임시 페이지. 다음 단계에서 설문 화면으로 교체한다.
export default function SurveyPage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 text-center">
      <Mascot name="thinking" />
      <h1 className="mt-8 text-2xl font-bold">설문을 준비 중이에요</h1>
      <p className="mt-2 text-ink-soft">조금만 기다려 주세요!</p>
      <Link
        to="/"
        className="mt-8 rounded-full bg-white px-6 py-3 text-sm font-semibold text-ink-soft shadow-soft active:scale-95"
      >
        처음으로
      </Link>
    </main>
  )
}
