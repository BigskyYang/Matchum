// 설문 문항 정의. 응답 → 모델 변수 변환은 lib/encode.js에서 한다.
// 문항 구성은 Jaejun/SURVEY_V3.md(설문 v3)를 바탕으로, 두 단계로 나눴다.
//   stage 1: 유형 분류에 쓰는 생활습관 (지연님 12개 유형 모델 입력 + 성별·나이) → 유형 결과
//   stage 2: 개인 결과에 쓰는 문항 (흡연·음주·채소·과일, mini-FFQ 5문항, 비타민 D 생활 4문항) → 개인 결과
//            비타민 D 4문항은 선택 문항(optional): '건너뛰기'로 넘어갈 수 있고, 영양 모델에는 넣지 않는다 (lib/vitaminD.js)
//            문항은 재준님 최종 설문(Jaejun/SURVEY_FINAL.md)을 따르되, 답하기 쉽게 줄였다 (흡연·음주 첫 문항 생략)
//            진단처럼 보이거나 건강기능식품 제품 추천에만 쓰이는 문항(PHQ-9, 질환·임신·약물, 지금 먹는 영양제)은 묻지 않는다
//            (의료법상 진단·처방으로 보일 소지, 건강기능식품 광고 규제, 민감정보 최소 수집)
//            2단계는 1단계 응답을 그대로 이어 쓴다 (재준님 개인 예측 모델도 1단계 변수를 입력으로 쓴다)
//
// type
//   choice   : 보기 중 하나 선택 (누르면 바로 다음 문항). 보기가 5개 이상이면 2열로 놓는다 (layout으로 바꿀 수 있다)
//   rows     : 여러 줄을 한 화면에서 고르기 { rows: [{ id, label }], options } → 응답은 { 줄 id: 값 }
//   number   : 숫자 휠 { unit, min, max, initial }
//   time     : 시각 'HH:MM' 휠 { initial, hourStart: 시 목록을 몇 시부터 보여줄지 }
//   duration : 시간 + 분 → 분 단위 숫자 휠 { per: '일주일에' | '하루', maxHours, initial(분) }
//   date     : 생년월일 'YYYY-MM-DD' 휠 (년·월·일) { minYear, maxYear, initial }
// layout (choice): 'list' 한 줄에 하나 | 'grid' 2열 | 'row' 한 줄에 모두 (짧은 숫자 보기)
// initial: 처음 화면에 맞춰져 있는 값 (많이 고르는 값을 기준으로)
// 문구: 제목은 짧은 말투로, 꼭 필요한 조건은 note 한 줄로, 예시·자세한 기준은 info로 (ⓘ 자세히 → 아래에서 올라오는 창)
//   note: 제목 아래 한 줄 안내, info: ['도움말 줄', ...], period: 응답 기간 ('최근 1년' 등, 제목 위 작은 표시)
//   모델 입력의 뜻(기간·포함·제외 기준)은 그대로 두고 표현만 줄였다
// showIf(answers): false면 해당 문항을 건너뛴다
// check(value): 다음으로 넘어갈 수 없는 값이면 안내 문구, 괜찮으면 null
//
// 팀 합의 (2026-11-04): 흡연은 궐련·전자담배 구분 없이 지금 피우는지만, 유산소는 중강도·고강도를 나눠 묻지 않음,
//   수면은 취침·기상 시각으로만 ('날마다 들쭉날쭉' 보기 없음), 나이는 생년월일로 계산한 만 나이
import { ageFromBirth } from '../lib/encode.js'
import { VITD_PREFIX, VITD_SURVEY } from '../lib/vitaminD.js'

// 채소·과일 9단계 (값이 클수록 자주)
const INTAKE_9 = [
  { label: '하루 3회 이상', value: 8 },
  { label: '하루 2회', value: 7 },
  { label: '하루 1회', value: 6 },
  { label: '주 5~6회', value: 5 },
  { label: '주 2~4회', value: 4 },
  { label: '주 1회', value: 3 },
  { label: '월 2~3회', value: 2 },
  { label: '월 1회', value: 1 },
  { label: '거의 안 먹어요', value: 0 },
]

// mini-FFQ 8단계 (값 = 재준님 Jaejun/src/mini_ffq.py의 FOOD_FREQ_ORD 0~7)
const FOOD_FREQ_8 = [
  { label: '거의 안 먹어요', value: 0 },
  { label: '월 1~3회', value: 1 },
  { label: '주 1~2회', value: 2 },
  { label: '주 3~4회', value: 3 },
  { label: '주 5~6회', value: 4 },
  { label: '하루 1회', value: 5 },
  { label: '하루 2회', value: 6 },
  { label: '하루 3회 이상', value: 7 },
]

const isCurrentSmoker = (a) => a.smoke_now === 'yes'
const THIS_YEAR = new Date().getFullYear()
const ADULT = 19
// mini-FFQ 모델은 19~64세에서만 검증됐다 → 만 65세 이상은 묻지 않는다 (재준님 모델 규칙)
const ffqAge = (a) => Boolean(a.birth_date) && ageFromBirth(a.birth_date) >= 19 && ageFromBirth(a.birth_date) <= 64

export const SECTIONS = {
  basic: '기본정보',
  smoke: '흡연',
  drink: '음주',
  activity: '신체활동',
  sedentary: '좌식시간',
  sleep: '수면',
  stress: '스트레스',
  meal: '식사습관',
  veg: '채소·과일',
  food: '평소 식사',
  vitd: '비타민 D',
}

const weekendDiffers = (a) => a.weekend_same === 'no'

// 1단계: 유형 분류 (지연님 모델 입력: 유산소·근력·좌식·수면·스트레스·세 끼·외식 + 성별·나이)
const STAGE_1 = [
  // 1. 기본정보
  {
    id: 'sex',
    section: 'basic',
    title: '성별을 알려 주세요',
    note: '같은 성별·나이대의 식사와 비교할 때 사용해요.',
    type: 'choice',
    options: [
      { label: '남성', value: 1 },
      { label: '여성', value: 2 },
    ],
  },
  // 만 나이는 생년월일로 계산 (lib/encode.js ageFromBirth). 만 19세 이상 성인 대상
  {
    id: 'birth_date',
    section: 'basic',
    title: '생년월일을 알려 주세요',
    note: '만 나이로 계산해요',
    type: 'date',
    minYear: THIS_YEAR - 121,
    maxYear: THIS_YEAR - ADULT,
    initial: '1990-01-01',
    check: (v) => {
      if (!v || typeof v !== 'string') return '생년월일을 선택해 주세요.'
      const day = new Date(v + 'T00:00:00Z')
      if (!Number.isFinite(day.getTime()) || day.toISOString().slice(0, 10) !== v) return '날짜를 다시 확인해 주세요.'
      const age = ageFromBirth(v)
      return age >= ADULT && age <= 120 ? null : '만 19세 이상 120세 이하가 참여할 수 있어요.'
    },
  },

  // 4. 신체활동: 팀 합의로 중강도·고강도를 나눠 묻지 않고, 모두 합친 시간이 주 150분 이상인지만 본다 (고강도 ×2 없음)
  //   답하기 쉽게 시간(0~5)으로 묻고, 모델에는 3시간 이상 = 주 150분 이상(ML_aerobic 1)으로 넘긴다 (lib/encode.js AEROBIC_HOURS)
  //   2시간 반 안팎이면 '가장 가까운 시간'을 고르게 안내한다. 예전 응답 값(0 = 미만, 3 = 이상)도 같은 뜻으로 읽힌다
  {
    id: 'activity',
    section: 'activity',
    title: '일주일 기준 유산소 운동을 얼마나 하나요?',
    info: [
      '빠르게 걷기, 자전거, 계단 오르기, 달리기·등산 등 숨이 찰 정도의 유산소 운동 시간을 알려주세요.',
      '천천히 걷기, 숨쉬기 운동은 빼 주세요.',
      '딱 맞는 보기가 없으면 가장 가까운 시간을 골라 주세요.',
    ],
    period: '최근 1주일',
    type: 'choice',
    layout: 'grid',
    options: [
      { label: '1시간 미만', value: 0 },
      { label: '1시간', value: 1 },
      { label: '2시간', value: 2 },
      { label: '3시간', value: 3 },
      { label: '4시간', value: 4 },
      { label: '5시간 이상', value: 5 },
    ],
  },
  {
    id: 'strength_days',
    section: 'activity',
    title: '근력운동은 일주일에 며칠 하나요?',
    note: '팔굽혀펴기·윗몸일으키기·아령·역기·철봉 등',
    period: '최근 1주일',
    type: 'choice',
    layout: 'row',
    options: [
      { label: '0일', value: 0 },
      { label: '1일', value: 1 },
      { label: '2일', value: 2 },
      { label: '3일', value: 3 },
      { label: '4일', value: 4 },
      { label: '5일+', value: 5 },
    ],
  },
  // 5. 좌식시간
  {
    id: 'sedentary_min',
    section: 'sedentary',
    title: '하루에 앉아 있거나 누워 있는 시간은요?',
    note: '잠자는 시간은 빼 주세요',
    info: ['책상·이동·TV·게임·인터넷 등 하루 전체를 생각해 주세요.'],
    type: 'duration',
    per: '하루',
    maxHours: 24,
    initial: 8 * 60,
  },
  // 수면: 취침·기상 시각 (주말도 비슷하면 주중만). 팀 합의로 '날마다 들쭉날쭉' 보기는 두지 않는다
  { id: 'weekday_bed', section: 'sleep', title: '평일 기준 몇 시에 주무시나요?', type: 'time', initial: '22:00', hourStart: 18 },
  { id: 'weekday_wake', section: 'sleep', title: '평일 기준 몇 시에 일어나시나요?', type: 'time', initial: '07:00', hourStart: 3, check: (v, a) => v === a.weekday_bed ? '잠든 시각과 일어난 시각을 다시 확인해 주세요.' : null },
  {
    id: 'weekend_same',
    section: 'sleep',
    title: '주말에도 비슷한 시각에 자고 일어나나요?',
    type: 'choice',
    options: [
      { label: '네, 비슷해요', value: 'yes' },
      { label: '아니요, 달라요', value: 'no' },
    ],
  },
  { id: 'weekend_bed', section: 'sleep', title: '주말 기준 몇 시에 주무시나요?', type: 'time', initial: '22:00', hourStart: 18, showIf: weekendDiffers },
  { id: 'weekend_wake', section: 'sleep', title: '주말 기준 몇 시에 일어나시나요?', type: 'time', initial: '07:00', hourStart: 3, check: (v, a) => v === a.weekend_bed ? '잠든 시각과 일어난 시각을 다시 확인해 주세요.' : null, showIf: weekendDiffers },
  // 7. 스트레스
  {
    id: 'stress',
    section: 'stress',
    title: '평소 스트레스를 얼마나 느끼나요?',
    type: 'choice',
    // 값 = KNHANES BP1 (1·2 → 스트레스 높음)
    options: [
      { label: '아주 많이 느껴요', value: 1 },
      { label: '많이 느끼는 편이에요', value: 2 },
      { label: '조금 느끼는 편이에요', value: 3 },
      { label: '거의 느끼지 않아요', value: 4 },
    ],
  },
  // 8. 식사습관 (값 = ML_*_freq_ord). 세 끼를 한 화면에서 고른다
  {
    id: 'meals',
    section: 'meal',
    title: '일주일에 평균적으로 아침·점심·저녁은 얼마나 먹나요?',
    period: '최근 1년',
    type: 'rows',
    rows: [
      { id: 'breakfast', label: '아침' },
      { id: 'lunch', label: '점심' },
      { id: 'dinner', label: '저녁' },
    ],
    options: [
      { label: '5~7일', value: 3 },
      { label: '3~4일', value: 2 },
      { label: '1~2일', value: 1 },
      { label: '0일', value: 0 },
    ],
  },
  {
    id: 'eating_out',
    section: 'meal',
    title: '외식은 얼마나 자주 하나요?',
    note: '배달·포장 음식도 포함',
    info: ['집에서 만든 음식이 아니면 외식이에요. 음식점 식사, 배달·포장 음식도 포함해요.'],
    period: '최근 1년',
    type: 'choice',
    // 값 = ML_eatingout_freq_ord
    options: [
      { label: '하루 2회 이상', value: 6 },
      { label: '하루 1회', value: 5 },
      { label: '주 5~6회', value: 4 },
      { label: '주 3~4회', value: 3 },
      { label: '주 1~2회', value: 2 },
      { label: '월 1~3회', value: 1 },
      { label: '거의 안 해요 (월 1회 미만)', value: 0 },
    ],
  },
]

// 2단계: 개인 결과 (재준님 개인 예측 모델의 나머지 입력 + 건강기능식품 안전 문항, 선택 문항)
// 흡연·음주는 KNHANES처럼 '평생 100개비'·'평생 1잔' 문항을 먼저 묻지 않고 바로 지금 상태를 묻는다.
// 모델 입력(현재 흡연, 하루 개비 수, 음주 빈도·양)은 같고, 답하기만 쉬워진다.
const FFQ_ITEMS = [
  { id: 'ffq_meat', name: '고기를', help: '돼지·소·닭·오리고기, 햄·소시지 포함' },
  { id: 'ffq_fish', name: '생선·해산물을', help: '생선, 오징어, 게, 멸치, 어묵 등' },
  { id: 'ffq_egg', name: '달걀을', help: '프라이, 찜, 삶은 달걀 등' },
  { id: 'ffq_legume', name: '두부·콩을', help: '두부, 콩자반, 두유 등' },
  { id: 'ffq_dairy', name: '우유·유제품을', help: '우유, 요구르트, 가공우유 등' },
]

const STAGE_2 = [
  // 흡연 (값 'yes' → ML_smoker 1). 팀 합의: 궐련(일반 담배)·전자담배를 구분하지 않고 지금 피우는지만 묻는다
  {
    id: 'smoke_now',
    section: 'smoke',
    title: '요즘 담배를 피우나요?',
    type: 'choice',
    options: [
      { label: '네, 피워요', value: 'yes' },
      { label: '아니요, 안 피워요', value: 'no' },
    ],
  },
  {
    id: 'cigarettes',
    section: 'smoke',
    title: '피우는 날에는 하루 몇 개비 정도 피우나요?',
    type: 'number',
    unit: '개비',
    min: 1,
    max: 60,
    initial: 10,
    showIf: isCurrentSmoker,
  },
  // 음주 (값 = ML_drink_freq_ord, ML_drink_amount_ord)
  {
    id: 'drink_freq',
    section: 'drink',
    title: '술은 얼마나 자주 마시나요?',
    period: '최근 1년',
    type: 'choice',
    options: [
      { label: '최근 1년 안 마셨어요', value: 0 },
      { label: '한 달에 1번 미만', value: 1 },
      { label: '한 달에 1번 정도', value: 2 },
      { label: '한 달에 2~4번', value: 3 },
      { label: '일주일에 2~3번', value: 4 },
      { label: '일주일에 4번 이상', value: 5 },
    ],
  },
  {
    id: 'drink_amount',
    section: 'drink',
    title: '마시는 날에는 한 번에 몇 잔 정도 마시나요?',
    note: '그 술의 잔으로 세어 주세요',
    info: ['술 종류와 상관없이 그 술의 잔 기준이에요.', '맥주 1캔은 약 1.5잔, 소주 1병은 약 7잔이에요.'],
    type: 'choice',
    layout: 'list',
    options: [
      { label: '1~2잔 (맥주 1캔 정도)', value: 1 },
      { label: '3~4잔 (소주 반 병 정도)', value: 2 },
      { label: '5~6잔', value: 3 },
      { label: '7~9잔 (소주 1병 정도)', value: 4 },
      { label: '10잔 이상', value: 5 },
    ],
    showIf: (a) => a.drink_freq > 0,
  },

  // 9. 채소·과일
  {
    id: 'veg',
    section: 'veg',
    title: '채소·버섯·해조류는 얼마나 자주 먹나요?',
    note: '김치·장아찌는 빼 주세요',
    info: ['김치·장아찌류는 빼 주세요.', '반찬, 국, 찌개 등에 들어간 채소는 포함해요.'],
    period: '최근 1년',
    type: 'choice',
    options: INTAKE_9,
  },
  { id: 'fruit', section: 'veg', title: '과일은 얼마나 자주 먹나요?', period: '최근 1년', type: 'choice', options: INTAKE_9 },
  // 평소 식사 mini-FFQ 5문항 (재준님 mini-FFQ 모델 입력, 65세 이상은 생략)
  ...FFQ_ITEMS.map(({ id, name, help }) => ({
    id,
    section: 'food',
    title: `${name} 얼마나 자주 먹나요?`,
    note: help,
    period: '최근 1년',
    type: 'choice',
    options: FOOD_FREQ_8,
    showIf: ffqAge,
  })),
  // 비타민 D 생활 4문항 (재준님 v1.2.0, 선택). 음식·시간 계산 없이 생활 장면만
  ...VITD_SURVEY.questions.map((q, i) => ({
    id: VITD_PREFIX + q.id,
    section: 'vitd',
    title: q.label,
    ...(i === 0 && { note: '선택 문항이에요. 정확한 시간은 몰라도 괜찮아요.' }),
    type: 'choice',
    layout: 'list',
    optional: true,
    options: q.options.map(({ label, value }) => ({ label, value })),
  })),
]

export const QUESTIONS = [...STAGE_1.map((q) => ({ ...q, stage: 1 })), ...STAGE_2.map((q) => ({ ...q, stage: 2 }))]

// 지금 응답 기준으로 그 단계에서 보여줄 문항만 남긴다
export const visibleQuestions = (answers, stage = 1) =>
  QUESTIONS.filter((q) => q.stage === stage && (!q.showIf || q.showIf(answers)))
