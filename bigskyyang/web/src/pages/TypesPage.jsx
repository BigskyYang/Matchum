import { useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import BottomSheet from '../components/BottomSheet.jsx'
import GroupChip, { GroupDot } from '../components/GroupChip.jsx'
import Icon from '../components/Icon.jsx'
import Mascot from '../components/Mascot.jsx'
import HabitSignals from '../components/result/HabitSignals.jsx'
import { allTypes, buildTypeResult } from '../lib/result.js'
import { loadSurvey } from '../lib/storage.js'

// 전체 유형 보기 (/types): 대분류 4개 × 세부 유형 3개. 설문을 하지 않아도 볼 수 있다
//   유형을 누르면 그 유형 평균의 생활습관 신호등·해시태그·비율을 아래에서 올라오는 창으로
//   내 결과가 있으면 내 유형에 '내 유형' 표시
function useMyType() {
  return useMemo(() => {
    const { answers, done } = loadSurvey()
    return done[1] ? buildTypeResult(answers).leafId : null
  }, [])
}

function TypeSheet({ t, mine, onClose }) {
  return (
    <BottomSheet title={t.name} onClose={onClose}>
      <div className="flex flex-col items-center text-center">
        <Mascot name={`type_${t.id}`} />
        <p className="mt-1 flex items-center gap-1.5 text-sm font-bold text-ink-soft">
          <GroupChip code={t.id[0]} name={t.main.name} />
          {mine && <span className="ml-1.5 rounded-full bg-primary-soft px-2 py-0.5 text-xs text-primary-shade">내 유형</span>}
        </p>
        <p className="mt-3 leading-relaxed whitespace-pre-line">{t.summary}</p>
        {t.tags.length > 0 && (
          <ul className="mt-3 flex flex-wrap justify-center gap-1.5">
            {t.tags.map((tag) => (
              <li key={tag} className="rounded-full bg-cream px-3 py-1 text-sm font-bold text-primary-shade">
                {tag}
              </li>
            ))}
          </ul>
        )}
        <p className="mt-3 text-sm text-ink-soft">
          성인 100명 중 <b className="text-primary-shade">{Math.round(t.sharePct)}명</b>이 이 유형이에요
        </p>
      </div>
      <h4 className="mt-5 mb-2 flex items-center gap-1.5 text-sm font-bold">
        <Icon name="traffic" size={18} className="text-primary-shade" />
        이 유형의 평균 생활습관
      </h4>
      <HabitSignals habits={t.habits} />
    </BottomSheet>
  )
}

export default function TypesPage() {
  const navigate = useNavigate()
  const groups = useMemo(() => allTypes(), [])
  const myType = useMyType()
  const [open, setOpen] = useState(null)

  const back = () => {
    if ((window.history.state?.idx ?? 0) > 0) navigate(-1)
    else navigate(myType ? '/result' : '/')
  }

  return (
    <main className="flex flex-1 flex-col gap-5 px-5 pt-4 pb-[max(1.5rem,env(safe-area-inset-bottom))]">
      <header className="flex items-center gap-2">
        <button
          type="button"
          onClick={back}
          aria-label="뒤로"
          className="-ml-2 flex size-11 items-center justify-center rounded-full text-2xl text-ink-soft active:bg-primary-soft"
        >
          <Icon name="back" size={26} />
        </button>
        <h1 className="font-display text-xl font-normal">NBTI 유형 모두 보기</h1>
      </header>
      <p className="-mt-2 text-sm leading-relaxed text-ink-soft">
        국민건강영양조사 성인들의 생활습관을 비슷한 사람끼리 묶은 {groups.reduce((n, g) => n + g.types.length, 0)}가지 유형이에요.
      </p>

      {groups.map((g) => (
        <section key={g.code} className="rounded-card bg-white p-4 shadow-soft">
          <h2 className="flex items-center gap-2 font-display text-xl font-normal">
            <GroupDot code={g.code} className="size-3" />
            {g.name}
            <span className="font-sans text-sm font-semibold text-ink-soft">100명 중 {Math.round(g.sharePct)}명</span>
          </h2>
          <p className="mt-1 text-sm text-ink-soft">{g.summary}</p>
          <ul className="mt-3 space-y-2">
            {g.types.map((t) => (
              <li key={t.id}>
                <button
                  type="button"
                  onClick={() => setOpen(t)}
                  className={`flex w-full items-center gap-3 rounded-card px-3 py-2.5 text-left active:scale-[0.98] ${
                    t.id === myType ? 'border-2 border-primary-strong bg-primary-soft/40' : 'bg-cream'
                  }`}
                >
                  <Mascot name={`type_${t.id}`} size="sm" className="size-16!" />
                  <span className="min-w-0 flex-1">
                    <span className="flex flex-wrap items-center gap-1.5 font-bold">
                      {t.name}
                      {t.id === myType && (
                        <span className="rounded-full bg-primary-shade px-2 py-0.5 text-xs text-white">내 유형</span>
                      )}
                    </span>
                    <span className="mt-0.5 block text-xs leading-relaxed text-ink-soft">{t.summary.replace('\n', ' ')}</span>
                  </span>
                  <span aria-hidden="true" className="text-ink-faint">
                    ›
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}

      {!myType && (
        <Link to="/survey" className="block rounded-button bg-primary-strong py-4 text-center text-xl font-bold text-white shadow-button">
          내 유형 알아보기
        </Link>
      )}

      {open && <TypeSheet t={open} mine={open.id === myType} onClose={() => setOpen(null)} />}
    </main>
  )
}
