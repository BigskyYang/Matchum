import { Link } from 'react-router-dom'
import Mascot from '../components/Mascot.jsx'
import { ESTIMATED_MINUTES, QUESTION_COUNT, SERVICE_NAME } from '../config.js'

export default function StartPage() {
  return (
    <main className="flex flex-1 flex-col px-6 pt-10 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <section className="flex flex-1 flex-col items-center justify-center text-center">
        <Mascot name="start" className="animate-float motion-reduce:animate-none" />

        <h1 className="mt-8 text-[2rem] leading-tight font-extrabold tracking-tight">{SERVICE_NAME}</h1>

        <p className="mt-3 text-base text-ink-soft">몇 가지 질문으로 나에게 맞는 영양제를 찾아보세요</p>

        <p className="mt-6 inline-flex items-center gap-1.5 rounded-full bg-white px-4 py-2 text-sm font-medium text-ink-soft shadow-soft">
          <span>⏱ 약 {ESTIMATED_MINUTES}분</span>
          <span aria-hidden="true" className="text-ink-faint">
            ·
          </span>
          <span>📝 {QUESTION_COUNT}문항</span>
        </p>
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
