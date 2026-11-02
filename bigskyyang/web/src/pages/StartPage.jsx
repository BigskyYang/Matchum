import { Link } from 'react-router-dom'
import Mascot from '../components/Mascot.jsx'
import { SERVICE_NAME } from '../config.js'

export default function StartPage() {
  return (
    <main className="flex flex-1 flex-col px-6 pt-10 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <section className="flex flex-1 flex-col items-center justify-center text-center">
        <Mascot name="start" gif="hello" float />

        <h1 className="mt-4 text-[2rem] leading-tight font-extrabold tracking-tight">{SERVICE_NAME}</h1>
      </section>

      <footer className="mt-10">
        <Link
          to="/survey"
          className="block w-full rounded-button bg-primary-strong py-5 text-center text-lg font-bold text-white shadow-button transition-[translate,box-shadow] duration-100 select-none active:translate-y-1 active:shadow-button-pressed"
        >
          검사 시작하기
        </Link>

        <p className="mt-5 text-center text-xs leading-relaxed text-ink-faint">
          추천 결과는 참고용이며 의료적 진단이나 처방을 대체하지 않습니다.
        </p>
      </footer>
    </main>
  )
}
