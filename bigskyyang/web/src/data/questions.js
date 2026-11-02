// 설문 문항 정의 (bigskyyang/사용자_설문조사_초안.html 기준)
// 문항을 빼거나 순서를 바꾸려면 이 배열만 고치면 된다. 응답 → 모델 변수 변환은 lib/encode.js에서 한다.
// 문항 구성은 Jaejun/SURVEY_V3.md(설문 v3)를 따른다. 단, 만 나이는 생년월일로 받는다.
//
// 핵심 문항(생활습관·식습관)이 끝나면 'extra' 문항에서 선택 문항(PHQ-9·대사건강)을 더 할지 고른다.
// 선택 문항은 군집·영양 판정에 쓰지 않고 결과 화면의 간단한 안내에만 쓴다.
//
// type (choice 외에는 모두 휴대폰에서 위아래로 드래그해 고르는 휠 선택기)
//   choice   : 보기 중 하나 선택 (누르면 바로 다음 문항)
//   date     : 생년월일 'YYYY-MM-DD' { initial }
//   number   : 숫자 { unit, min, max, initial }
//   time     : 시각 'HH:MM' { initial, hourStart: 시 목록을 몇 시부터 보여줄지 }
//   duration : 시간 + 분 → 분 단위 숫자 { per: '일주일에' | '하루', maxHours, initial(분) }
// initial: 처음 화면에 맞춰져 있는 값 (많이 고르는 값을 기준으로)
// showIf(answers): false면 해당 문항을 건너뛴다

const MEAL = [
  { label: '주 5~7회', value: 3 },
  { label: '주 3~4회', value: 2 },
  { label: '주 1~2회', value: 1 },
  { label: '거의 안 한다 (주 0회)', value: 0 },
]

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
  { label: '거의 안 한다 (월 1회 미만)', value: 0 },
]

const isCurrentSmoker = (a) => a.smoke_now === 'daily' || a.smoke_now === 'sometimes'

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
  food: '주요 식품',
  extra: '선택 문항',
  mind: '마음 건강',
  metabolic: '대사 건강',
}

// 선택 문항 영역 (진행률을 핵심 문항과 따로 센다)
export const OPTIONAL_SECTIONS = ['mind', 'metabolic']

const wantsExtra = (a) => a.extra === 'more'

// PHQ-9 응답 (값 = 점수 0~3)
const PHQ_OPTIONS = [
  { label: '전혀 아니다', value: 0 },
  { label: '여러 날 동안', value: 1 },
  { label: '일주일 이상', value: 2 },
  { label: '거의 매일', value: 3 },
]

// 국민건강영양조사 PHQ-9 한국어판 문항
const PHQ_ITEMS = [
  '일 또는 여가 활동을 하는 데 흥미나 즐거움을 느끼지 못함',
  '기분이 가라앉거나, 우울하거나, 희망이 없음',
  '잠이 들거나 계속 잠을 자는 것이 어려움, 또는 잠을 너무 많이 잠',
  '피곤하다고 느끼거나 기운이 거의 없음',
  '입맛이 없거나 과식을 함',
  '자신을 부정적으로 봄. 혹은 자신이 실패자라고 느끼거나 자신 또는 가족을 실망시킴',
  '신문을 읽거나 텔레비전을 보는 것과 같은 일에 집중하는 것이 어려움',
  '다른 사람들이 주목할 정도로 너무 느리게 움직이거나 말을 함. 또는 반대로 평상시보다 많이 움직여서 너무 안절부절못하거나 들떠 있음',
  '차라리 죽는 것이 더 낫겠다고 생각하거나 어떤 식으로든 자신을 해칠 것이라고 생각함',
]

const YES_NO = [
  { label: '예', value: 'yes' },
  { label: '아니오', value: 'no' },
]

export const QUESTIONS = [
  // 1. 기본정보
  {
    id: 'sex',
    section: 'basic',
    title: '성별을 선택해주세요.',
    type: 'choice',
    options: [
      { label: '남성', value: 1 },
      { label: '여성', value: 2 },
    ],
  },
  // 만 나이는 생년월일로 자동 계산 (lib/encode.js)
  { id: 'birth', section: 'basic', title: '생년월일을 선택해주세요.', type: 'date', initial: '2000-01-01' },

  // 2. 흡연
  {
    id: 'smoke_100',
    section: 'smoke',
    title: '지금까지 살아오는 동안 일반담배(궐련)를 총 5갑(100개비) 이상 피운 적이 있습니까?',
    type: 'choice',
    options: [
      { label: '예', value: 'yes' },
      { label: '아니오', value: 'no' },
    ],
  },
  {
    id: 'smoke_now',
    section: 'smoke',
    title: '현재 담배를 피우십니까?',
    type: 'choice',
    options: [
      { label: '매일 피움', value: 'daily' },
      { label: '가끔 피움', value: 'sometimes' },
      { label: '과거에는 피웠으나 현재 피우지 않음', value: 'past' },
    ],
    showIf: (a) => a.smoke_100 === 'yes',
  },
  {
    id: 'cigarettes',
    section: 'smoke',
    title: '담배를 피우는 날에는 하루 평균 몇 개비 정도 피우십니까?',
    type: 'number',
    unit: '개비',
    min: 1,
    max: 60,
    initial: 10,
    showIf: isCurrentSmoker,
  },

  // 3. 음주
  {
    id: 'drink_ever',
    section: 'drink',
    title: '지금까지 살아오면서 1잔 이상의 술을 마신 적이 있습니까?',
    help: ['제사·차례 때 몇 모금 마셔본 것은 제외합니다.'],
    type: 'choice',
    options: [
      { label: '있음', value: 'yes' },
      { label: '술을 마셔 본 적 없음', value: 'no' },
    ],
  },
  {
    id: 'drink_freq',
    section: 'drink',
    title: '최근 1년 동안 술을 얼마나 자주 마셨습니까?',
    type: 'choice',
    // 값 = ML_drink_freq_ord
    options: [
      { label: '최근 1년간 전혀 마시지 않았다', value: 0 },
      { label: '한 달에 1번 미만', value: 1 },
      { label: '한 달에 1번 정도', value: 2 },
      { label: '한 달에 2~4번', value: 3 },
      { label: '일주일에 2~3번 정도', value: 4 },
      { label: '일주일에 4번 이상', value: 5 },
    ],
    showIf: (a) => a.drink_ever === 'yes',
  },
  {
    id: 'drink_amount',
    section: 'drink',
    title: '술을 마시는 날에는 한 번에 보통 얼마나 마십니까?',
    help: ['술 종류에 관계없이 그 술의 일반적인 잔을 기준으로 합니다.', '캔맥주 1개(355mL)는 약 1.5잔, 소주 1병은 약 7잔입니다.'],
    type: 'choice',
    // 값 = ML_drink_amount_ord
    options: [
      { label: '1~2잔', value: 1 },
      { label: '3~4잔', value: 2 },
      { label: '5~6잔', value: 3 },
      { label: '7~9잔', value: 4 },
      { label: '10잔 이상', value: 5 },
    ],
    showIf: (a) => a.drink_ever === 'yes' && a.drink_freq > 0,
  },

  // 4. 신체활동
  {
    id: 'moderate_min',
    section: 'activity',
    title: '평소 일주일 동안 중강도 신체활동을 총 얼마나 하십니까?',
    help: ['숨이 약간 차거나 심장이 약간 빠르게 뛰는 정도의 활동이에요.', '예: 빠르게 걷기, 자전거 타기, 몸을 쓰는 업무 등 (일·이동·여가 모두 포함)'],
    type: 'duration',
    per: '일주일에',
    maxHours: 40,
    initial: 0,
  },
  {
    id: 'vigorous_min',
    section: 'activity',
    title: '평소 일주일 동안 고강도 신체활동을 총 얼마나 하십니까?',
    help: ['숨이 많이 차거나 심장이 매우 빠르게 뛰는 정도의 활동이에요.', '예: 달리기, 등산, 수영, 농구, 줄넘기, 무거운 물건 나르기 등'],
    type: 'duration',
    per: '일주일에',
    maxHours: 40,
    initial: 0,
  },
  {
    id: 'strength_days',
    section: 'activity',
    title: '최근 1주일 동안 팔굽혀펴기, 윗몸일으키기, 아령, 역기, 철봉 등의 근력운동을 한 날은 며칠입니까?',
    type: 'choice',
    options: [
      { label: '전혀 하지 않음', value: 0 },
      { label: '1일', value: 1 },
      { label: '2일', value: 2 },
      { label: '3일', value: 3 },
      { label: '4일', value: 4 },
      { label: '5일 이상', value: 5 },
    ],
  },

  // 5. 좌식시간
  {
    id: 'sedentary_min',
    section: 'sedentary',
    title: '평소 하루에 앉아 있거나 누워 있는 시간은 총 얼마나 됩니까?',
    help: ['잠자는 시간은 빼 주세요.', '책상·이동·TV·게임·인터넷 등 하루 전체를 생각해 주세요.'],
    type: 'duration',
    per: '하루',
    maxHours: 20,
    initial: 8 * 60,
  },

  // 6. 수면
  { id: 'weekday_bed', section: 'sleep', title: '평소 주중(또는 주로 일하는 날)에 잠자리에 드는 시각은 언제입니까?', type: 'time', initial: '22:00', hourStart: 18 },
  { id: 'weekday_wake', section: 'sleep', title: '평소 주중(또는 주로 일하는 날)에 일어나는 시각은 언제입니까?', type: 'time', initial: '07:00', hourStart: 3 },
  { id: 'weekend_bed', section: 'sleep', title: '평소 주말(또는 주로 쉬는 날)에 잠자리에 드는 시각은 언제입니까?', type: 'time', initial: '22:00', hourStart: 18 },
  { id: 'weekend_wake', section: 'sleep', title: '평소 주말(또는 주로 쉬는 날)에 일어나는 시각은 언제입니까?', type: 'time', initial: '07:00', hourStart: 3 },
  {
    id: 'shift_work',
    section: 'sleep',
    title: '야간·교대·불규칙 근무를 하고 있습니까?',
    type: 'choice',
    // 생활패턴 해석용 (모델 입력 아님)
    options: [
      { label: '아니오', value: 'no' },
      { label: '야간근무', value: 'night' },
      { label: '정기적 교대근무', value: 'shift' },
      { label: '24시간 교대근무', value: 'shift24' },
      { label: '불규칙 근무', value: 'irregular' },
      { label: '기타', value: 'other' },
    ],
  },

  // 7. 스트레스
  {
    id: 'stress',
    section: 'stress',
    title: '평소 일상생활 중에 스트레스를 어느 정도 느끼고 있습니까?',
    type: 'choice',
    // 값 = KNHANES BP1 (1·2 → 스트레스 높음)
    options: [
      { label: '대단히 많이 느낀다', value: 1 },
      { label: '많이 느끼는 편이다', value: 2 },
      { label: '조금 느끼는 편이다', value: 3 },
      { label: '거의 느끼지 않는다', value: 4 },
    ],
  },

  // 8. 식사습관 (값 = ML_*_freq_ord)
  { id: 'breakfast', section: 'meal', title: '최근 1년 동안 아침식사를 1주일에 몇 회 하셨습니까?', type: 'choice', options: MEAL },
  { id: 'lunch', section: 'meal', title: '최근 1년 동안 점심식사를 1주일에 몇 회 하셨습니까?', type: 'choice', options: MEAL },
  { id: 'dinner', section: 'meal', title: '최근 1년 동안 저녁식사를 1주일에 몇 회 하셨습니까?', type: 'choice', options: MEAL },
  {
    id: 'eating_out',
    section: 'meal',
    title: '최근 1년 동안 평균적으로 외식을 얼마나 자주 하셨습니까?',
    help: ['음식점 식사뿐 아니라 배달·포장 음식, 급식도 포함합니다.'],
    type: 'choice',
    // 값 = ML_eatingout_freq_ord
    options: [
      { label: '하루 2회 이상', value: 6 },
      { label: '하루 1회', value: 5 },
      { label: '주 5~6회', value: 4 },
      { label: '주 3~4회', value: 3 },
      { label: '주 1~2회', value: 2 },
      { label: '월 1~3회', value: 1 },
      { label: '거의 안 한다 (월 1회 미만)', value: 0 },
    ],
  },

  // 9. 채소·과일
  {
    id: 'veg',
    section: 'veg',
    title: '최근 1년 동안 평균적으로 채소류, 버섯류, 해조류를 얼마나 자주 드셨습니까?',
    help: ['김치·장아찌류는 빼 주세요.', '반찬, 국, 찌개 등에 들어간 채소는 포함합니다.'],
    type: 'choice',
    options: INTAKE_9,
  },
  { id: 'fruit', section: 'veg', title: '최근 1년 동안 평균적으로 과일을 얼마나 자주 드셨습니까?', type: 'choice', options: INTAKE_9 },

  // 10. 주요 식품 (값 = 하루 평균 섭취 횟수 servings/day)
  {
    id: 'protein',
    section: 'food',
    title: '평소 일주일 동안 고기·생선·달걀·콩류를 몇 회 정도 드십니까?',
    help: ['1회 기준: 고기 1접시, 생선 1토막, 달걀 1~2개, 두부 1/5모, 콩류 1/2컵'],
    type: 'choice',
    options: [
      { label: '거의 먹지 않는다', value: 0 },
      { label: '주 1~2회', value: 0.21 },
      { label: '주 3~4회', value: 0.5 },
      { label: '주 5~7회', value: 0.86 },
      { label: '하루 1회 정도', value: 1 },
      { label: '하루 2회 정도', value: 2 },
      { label: '하루 3회 이상', value: 3 },
    ],
  },
  {
    id: 'dairy',
    section: 'food',
    title: '평소 일주일 동안 우유 및 유제품을 몇 회 정도 드십니까?',
    help: ['1회 기준: 우유 1컵, 요구르트 1개, 떠먹는 요구르트 1개, 치즈 1~2장'],
    type: 'choice',
    options: [
      { label: '거의 먹지 않는다', value: 0 },
      { label: '주 1~2회', value: 0.21 },
      { label: '주 3~4회', value: 0.5 },
      { label: '주 5~7회', value: 0.86 },
      { label: '하루 1회 정도', value: 1 },
      { label: '하루 2회 이상', value: 2 },
    ],
  },

  // 11. 선택 문항 여부
  {
    id: 'extra',
    section: 'extra',
    title: '핵심 질문이 끝났어요! 마음 건강·대사 건강 질문도 답해 볼까요?',
    help: ['선택 문항 12개예요. 유형 판정에는 쓰지 않고, 결과 화면에서 간단한 안내만 드려요.', '응답은 이 휴대폰에만 잠시 저장되고 어디에도 전송되지 않아요.'],
    type: 'choice',
    options: [
      { label: '결과 바로 보기', value: 'skip' },
      { label: '추가 질문 답하기 (선택)', value: 'more' },
    ],
  },

  // 12. 마음 건강 (PHQ-9)
  ...PHQ_ITEMS.map((text, i) => ({
    id: `phq${i + 1}`,
    section: 'mind',
    title: text,
    help: ['지난 2주 동안 이런 문제를 얼마나 자주 겪었는지 골라 주세요.'],
    type: 'choice',
    options: PHQ_OPTIONS,
    showIf: wantsExtra,
  })),

  // 13. 대사 건강 (결과 해석용)
  { id: 'dx_hypertension', section: 'metabolic', title: '의사에게 고혈압 진단을 받은 적이 있습니까?', type: 'choice', options: YES_NO, showIf: wantsExtra },
  { id: 'dx_diabetes', section: 'metabolic', title: '의사에게 당뇨병 진단을 받은 적이 있습니까?', type: 'choice', options: YES_NO, showIf: wantsExtra },
  {
    id: 'dx_dyslipidemia',
    section: 'metabolic',
    title: '의사에게 이상지질혈증(고지혈증) 진단을 받은 적이 있습니까?',
    type: 'choice',
    options: YES_NO,
    showIf: wantsExtra,
  },
]

// 지금 응답 기준으로 보여줄 문항만 남긴다
export const visibleQuestions = (answers) => QUESTIONS.filter((q) => !q.showIf || q.showIf(answers))
