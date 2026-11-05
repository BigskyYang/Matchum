export const VERSION = '1.0.0';
const frequencies = {
  none: '낮시간 야외활동이 거의 없다고 답했어요.',
  days_1_2: '낮시간 야외활동을 주 1~2일 한다고 답했어요.',
  days_3_4: '낮시간 야외활동을 주 3~4일 한다고 답했어요.',
  days_5_7: '낮시간 야외활동을 주 5~7일 한다고 답했어요.',
  irregular: '낮시간 야외활동 일정이 일정하지 않다고 답했어요.',
};
const durations = { lt15:'15분 미만', min15_30:'15~30분 미만', min30_60:'30~60분 미만', ge60:'60분 이상', unknown:'잘 모르겠음' };
const foods = { fish:'생선류', egg_yolk:'달걀노른자', fortified:'비타민 D 강화 표시가 있는 식품', none:'해당 식품을 거의 먹지 않음', unknown:'잘 모르겠음' };
const own = (obj, key) => Object.hasOwn(obj, key);
const enumValue = (v, choices, key) => {
  if (v === undefined || v === null) return null;
  if (typeof v !== 'string' || !own(choices, v)) throw new TypeError(`Invalid ${key}`);
  return v;
};

/** Self-reported context only. No vitamin D status, score, probability, or dose. */
export function buildVitaminDInfo(answers = {}) {
  if (!answers || typeof answers !== 'object' || Array.isArray(answers)) throw new TypeError('answers must be an object');
  const allowed = ['outdoor_days', 'outdoor_duration', 'vitamin_d_foods'];
  if (Object.keys(answers).some(k => !allowed.includes(k))) throw new TypeError('Unknown answer key');
  const days = enumValue(answers.outdoor_days, frequencies, 'outdoor_days');
  const submittedDuration = enumValue(answers.outdoor_duration, durations, 'outdoor_duration');
  // A hidden follow-up never contributes stale data to the summary.
  const duration = days === null || days === 'none' ? null : submittedDuration;
  let selected = answers.vitamin_d_foods ?? null;
  if (selected !== null) {
    if (!Array.isArray(selected) || !selected.length || selected.some(v => typeof v !== 'string' || !own(foods, v))) throw new TypeError('Invalid vitamin_d_foods');
    if (new Set(selected).size !== selected.length) throw new TypeError('Duplicate food choice');
    if (selected.length > 1 && (selected.includes('none') || selected.includes('unknown'))) throw new TypeError('none and unknown are exclusive choices');
    selected = Object.keys(foods).filter(k => selected.includes(k));
  }
  const cards = [];
  if (days !== null) {
    cards.push({ id:'outdoors', title:'낮시간 야외활동 응답', text:frequencies[days],
      detail:duration === null ? null : duration === 'unknown' ? '야외활동 시간은 잘 모르겠다고 답했어요.' : `야외활동을 하는 날에는 하루 총 ${durations[duration]}이라고 답했어요.` });
  }
  if (selected !== null) {
    const text = selected[0] === 'none' ? '제시한 비타민 D 함유 식품을 거의 먹지 않는다고 답했어요.'
      : selected[0] === 'unknown' ? '제시한 식품을 먹는지 잘 모르겠다고 답했어요.'
      : `먹는다고 답한 식품: ${selected.map(k => foods[k]).join(', ')}.`;
    cards.push({ id:'foods', title:'식품 응답', text, detail:'식품 종류에 대한 응답이며, 섭취량이나 충분 여부를 계산한 결과는 아니에요.' });
  }
  return {
    version:VERSION, module:'vitamin_d_information', method:'self_report_rules',
    title:'비타민 D 생활·식사 정보',
    completion:cards.length === 0 ? 'unanswered' : days !== null && (days === 'none' || duration !== null) && selected !== null ? 'complete' : 'partial',
    normalizedAnswers:{ outdoor_days:days, outdoor_duration:duration, vitamin_d_foods:selected },
    summaryCards:cards,
    emptyMessage:cards.length === 0 ? '선택 문항에 답하면 야외활동과 식품 응답을 정리해 드려요. 응답하지 않아도 일반 정보를 볼 수 있어요.' : null,
    notices:[
      '설문 응답을 정리한 참고 정보예요. 비타민 D 부족 여부, 혈중 수치, 필요한 복용량을 판단하지 않아요.',
      '야외활동 시간만으로 비타민 D가 충분한지 알 수 없어요. 계절·지역·나이·피부 노출 등 여러 조건에 따라 달라질 수 있어요.',
      '비타민 D를 위해 햇빛 노출 시간을 늘리도록 권하지 않아요. 야외에서는 자외선 보호 수칙을 지켜 주세요.',
    ],
    foodInformation:{ title:'비타민 D 식품 정보', text:'연어·고등어 같은 생선, 달걀노른자 등에 비타민 D가 들어 있어요. 강화식품은 영양표시에서 비타민 D 함유 여부를 확인해 주세요.' },
    actions:[
      { id:'food_information', label:'비타민 D 식품 정보 보기', defaultExpanded:false },
      { id:'product_information', label:'비타민 D 제품 정보 보기', defaultExpanded:false, trigger:'explicit_user_action', nutrientId:'vitamin_d', scope:'general_information', eligibility:'all_users' },
    ],
    productNotice:'관련 제품의 일반 정보이며, 개인의 복용 필요성이나 적합성을 확인한 결과는 아니에요.',
  };
}
