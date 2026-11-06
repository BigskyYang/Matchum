import { useState } from 'react'
import { model } from '../../lib/classify.js'
import BottomSheet from '../BottomSheet.jsx'
import Icon from '../Icon.jsx'

// 결과 화면 맨 아래 'ⓘ 어떻게 만들었나요?' 버튼 하나 → 근거·한계·주의(참고용 정보라는 안내 포함)를 한곳에 모은 창
//   카드마다 흩어져 있던 안내문(진단 아님, 정확도, 상담 권고, 의약품 아님)을 여기로 모았다
//   personal: 개인 결과면 영양 위험 예측과 건강기능식품 안내를 더한다
function Section({ icon, title, children }) {
  return (
    <div className="rounded-card bg-cream px-4 py-3">
      <p className="flex items-center gap-1.5 font-bold">
        <Icon name={icon} size={18} className="text-primary-shade" />
        {title}
      </p>
      <div className="mt-1 space-y-1 text-sm leading-relaxed text-ink-soft">{children}</div>
    </div>
  )
}

export default function AboutLink({ personal = false }) {
  const [open, setOpen] = useState(false)
  const n = model.population.n.toLocaleString('ko-KR')

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mx-auto flex items-center gap-1 px-2 py-3 text-xs text-ink-faint underline underline-offset-2"
      >
        <Icon name="info" size={14} />
        어떻게 만들었나요?
      </button>
      {open && (
        <BottomSheet title="이 결과는 어떻게 만들었나요?" onClose={() => setOpen(false)}>
          <div className="space-y-2">
            <Section icon="chart" title="자료">
              <p>국민건강영양조사 2022–2024 성인 {n}명의 생활습관과 하루 식사 기록을 분석했어요.</p>
            </Section>
            <Section icon="puzzle" title="유형">
              <p>생활습관이 비슷한 사람끼리 묶은 {model.types.length}가지 유형 중 내 응답과 가장 가까운 유형이에요.</p>
            </Section>
            <Section icon="traffic" title="습관 신호등">
              <p>팀이 정한 생활습관 점수 구간이에요. 예를 들어 근력운동은 주 3일까지 운동 점수에 반영해요. 유형 평균은 사람별 점수를 계산한 뒤 조사 가중치로 평균했어요.</p>
            </Section>
            <Section icon="apple" title="부족할 수 있는 영양소">
              <p>
                같은 유형·성별·나이대 사람 중 2025 한국인 영양소 섭취기준보다 적게 먹은 사람의 비율이에요. 음식만 셌고 영양제는
                뺐어요.
              </p>
            </Section>
            {personal && (
              <Section icon="checklist" title="내가 특히 살펴볼 영양소">
                <p>내 응답으로 섭취 기준보다 적게 먹었을 가능성(나트륨은 기준 초과 가능성)을 예측해, 조사 참여자들과 비교한 세 단계(높은 편·보통·낮은 편)로 보여 줘요. 실제로 충분히 먹는지는 알 수 없어요.</p>
                <p>
                  고기·생선·달걀·콩·유제품을 먹는 횟수로 예측한 결과(평소 식사 기준, 19~64세)가 있으면 그 결과를 먼저
                  보여 줘요. 그 밖에는 생활습관 응답을 사용해요. 영양소마다 예측 성능은 달라요.
                </p>
              </Section>
            )}
            {personal && (
              <Section icon="sunrise" title="비타민 D와 내 생활">
                <p>출퇴근·점심 외출·운동·쉬는 날 외출 응답에 맞춰 식품 정보와 야외활동 정보의 순서만 정했어요. 비타민 D 상태를 측정하거나 예측한 결과가 아니고, 영양소 예측에는 쓰지 않아요.</p>
              </Section>
            )}
            <Section icon="alert" title="꼭 알아 두세요">
              <p>참고용 정보예요. 나의 영양 상태를 진단한 결과가 아니고, 필요한 양을 알려 주지 않아요.</p>
              {personal && <p>건강기능식품은 질병의 예방 및 치료를 위한 의약품이 아닙니다.</p>}
              <p>임신·수유 중이거나 질환이 있거나 약을 먹고 있다면 식단과 건강기능식품은 의사·약사와 먼저 상의하세요.</p>
              <p>설문과 등록 제품은 이 탭에 임시 보관해요. 처음부터 다시 검사하면 삭제돼요. 직접 저장하거나 공유한 이미지는 별도로 남아요.</p>
            </Section>
          </div>
        </BottomSheet>
      )}
    </>
  )
}
