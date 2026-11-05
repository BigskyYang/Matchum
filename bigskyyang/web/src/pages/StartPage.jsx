import Mascot from '../components/Mascot.jsx'
import PrimaryButton from '../components/PrimaryButton.jsx'
import RotatingNotes from '../components/RotatingNotes.jsx'
import { SERVICE_NAME, TEAM_NAME } from '../config.js'
import { model } from '../lib/classify.js'

// 'NBTI 유형 검사'에서 앞의 N(Nutrient)만 강조
function Title() {
  const [head, ...rest] = SERVICE_NAME
  return (
    <h1 className="font-display text-[2.25rem] leading-tight font-normal">
      {head === 'N' ? (
        <>
          <span className="text-mint-strong">N</span>
          {rest.join('')}
        </>
      ) : (
        SERVICE_NAME
      )}
    </h1>
  )
}

export default function StartPage() {
  const sampleSize = model.population.n.toLocaleString('ko-KR')

  return (
    <main className="flex flex-1 flex-col px-6 pt-5 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <header className="flex justify-start">
        <span className="rounded-full bg-white px-3.5 py-1.5 text-xs font-bold text-primary-shade shadow-soft">
          <span className="font-semibold text-ink-faint">Team</span> {TEAM_NAME}
        </span>
      </header>

      <section className="flex flex-1 flex-col items-center justify-center py-4 text-center">
        {/* 세로가 짧은 휴대폰(iPhone SE 등)에서는 마스코트를 줄여 버튼까지 한 화면에 들어오게 */}
        <Mascot name="start" gif="hello" float className="[@media(max-height:720px)]:size-48" />

        <div className="mt-2">
          <Title />
        </div>
        {/* NBTI = Nutrient + MBTI */}
        <p className="mt-2.5 flex items-center gap-1.5 text-xs font-bold" aria-label="Nutrient와 MBTI를 합친 말">
          <span className="inline-flex items-center gap-1 rounded-full bg-mint px-2.5 py-1">
            <span aria-hidden="true">🥗</span> Nutrient
          </span>
          <span className="text-ink-faint">+</span>
          <span className="inline-flex items-center gap-1 rounded-full bg-lavender px-2.5 py-1">
            <span aria-hidden="true">🧩</span> MBTI
          </span>
        </p>
        <p className="mt-5 text-sm leading-relaxed text-ink-soft">
          내 생활습관 유형을 알아보고,
          <br />
          식사에서 살펴볼 점을 확인해요
        </p>
      </section>

      <footer>
        {/* 머신러닝 분석은 팀이 미리 해 두었고, 설문은 그중 가장 가까운 유형을 찾을 뿐이다 */}
        <RotatingNotes
          className="mb-3 text-center text-xs text-ink-soft"
          items={[
            <>
              <span aria-hidden="true" className="mr-1">✨</span>먼저 <b className="text-ink">생활습관 유형</b>을 보고, 개인 식사 설문은 이어서 선택해요
            </>,
            <>
              <span aria-hidden="true" className="mr-1">📊</span>국민건강영양조사 성인 <b className="text-ink">{sampleSize}명</b>(2022–2024) 분석
            </>,
            // 응답은 sessionStorage에만 잠시 두고 서버로 보내지 않는다 (lib/storage.js)
            <>
              <span aria-hidden="true" className="mr-1">🔒</span>응답과 결과는 <b className="text-ink">이 브라우저 탭</b>에서 계산하고 보관해요
            </>,
          ]}
        />
        <PrimaryButton to="/survey">검사 시작하기</PrimaryButton>
        <p className="mt-4 text-center text-xs leading-relaxed text-ink-faint">
          추천 결과는 참고용이며 의료적 진단이나 처방을 대체하지 않습니다.
        </p>
      </footer>
    </main>
  )
}
