export const VERSION = '1.2.0';
const QUESTIONS = {
  "commute": {
    "title": "출퇴근·통학은 주로 어떻게 하나요?",
    "choices": {
      "walk_cycle": "출퇴근·통학 때 걷거나 자전거를 이용한다고 답했어요.",
      "transit": "출퇴근·통학 때 대중교통을 이용한다고 답했어요.",
      "car": "출퇴근·통학 때 자가용을 이용한다고 답했어요.",
      "no_regular_commute": "정기적인 출퇴근·통학이 없다고 답했어요.",
      "unknown": "출퇴근·통학 방식이 일정하지 않거나 잘 모르겠다고 답했어요."
    }
  },
  "lunch_outing": {
    "title": "점심시간에 잠깐 밖에 나가나요?",
    "choices": {
      "often": "점심시간에 거의 매일 밖에 나간다고 답했어요.",
      "sometimes": "점심시간에 가끔 밖에 나간다고 답했어요.",
      "rarely": "점심시간에 거의 밖에 나가지 않는다고 답했어요.",
      "unknown": "점심시간 외출은 해당하지 않거나 잘 모르겠다고 답했어요."
    }
  },
  "exercise_setting": {
    "title": "운동은 주로 언제, 어디서 하나요?",
    "choices": {
      "daytime_outdoor": "운동할 때 주로 낮에 야외에서 한다고 답했어요.",
      "other_time_outdoor": "운동할 때 주로 아침·저녁·밤에 야외에서 한다고 답했어요.",
      "indoor": "운동할 때 주로 실내에서 한다고 답했어요.",
      "none": "요즘 운동을 하지 않는다고 답했어요.",
      "unknown": "운동 시간·장소가 일정하지 않거나 잘 모르겠다고 답했어요."
    }
  },
  "day_off_outing": {
    "title": "주말이나 쉬는 날, 낮에 밖에서 시간을 보내나요?",
    "choices": {
      "often": "쉬는 날 낮에 야외에서 자주 시간을 보낸다고 답했어요.",
      "sometimes": "쉬는 날 낮에 야외에서 가끔 시간을 보낸다고 답했어요.",
      "rarely": "쉬는 날 낮에 야외에서 거의 시간을 보내지 않는다고 답했어요.",
      "unknown": "쉬는 날 낮의 야외활동이 일정하지 않거나 잘 모르겠다고 답했어요."
    }
  }
};

// These are display branches, not vitamin D status or exposure grades.
function selectGuidance(a, cards) {
  const relevant=cards.filter(c=>c.id!=='commute');
  const summary=relevant.length ? relevant.map(c=>c.text).join(' ') : cards.map(c=>c.text).join(' ');
  const base={summary,primaryActionId:'food_information'};
  if(a.exercise_setting==='daytime_outdoor') return {...base,key:'daytime_exercise',headline:'낮에 야외에서 운동하는 시간이 있네요',nextStep:'야외활동 시 참고할 점과 비타민 D 식품 정보를 함께 확인해 보세요.',primaryActionId:'outdoor_information'};
  if(a.day_off_outing==='often') return {...base,key:'day_off_outings',headline:'쉬는 날 낮에 야외에서 시간을 보내는군요',nextStep:'야외활동 시 참고할 점과 비타민 D 식품 정보를 함께 확인해 보세요.',primaryActionId:'outdoor_information'};
  if(a.lunch_outing==='often') return {...base,key:'lunch_outings',headline:'점심시간에 밖에 나가는 습관이 있네요',nextStep:'야외활동 시 참고할 점과 비타민 D 식품 정보를 함께 확인해 보세요.',primaryActionId:'outdoor_information'};
  if(a.lunch_outing==='rarely' && a.day_off_outing==='rarely' && ['indoor','none'].includes(a.exercise_setting)) return {...base,key:'limited_outing_contexts',headline:'점심시간과 쉬는 날에는 외출이 드문 편이네요',nextStep:'비타민 D를 얻을 수 있는 식품 정보를 먼저 살펴보세요.'};
  const hasKnownContext=[a.lunch_outing,a.exercise_setting,a.day_off_outing].some(v=>v!==null && v!=='unknown');
  if(hasKnownContext) return {...base,key:'varied_contexts',headline:'생활 속 야외활동 장면을 살펴봤어요',nextStep:'응답한 생활 패턴과 함께 비타민 D 식품 정보와 야외활동 시 참고할 점을 확인해 보세요.'};
  return {...base,key:'general_information',headline:'비타민 D를 알아두는 간단한 방법',nextStep:'식품으로 얻는 방법과 야외활동 시 참고할 점을 확인해 보세요.'};
}

/** Optional self-reported context; no food questions, scores or prediction. */
export function buildVitaminDInfo(answers = {}) {
  if (!answers || typeof answers !== 'object' || Array.isArray(answers)) throw new TypeError('answers must be an object');
  if (Object.keys(answers).some(k => !Object.hasOwn(QUESTIONS,k))) throw new TypeError('Unknown answer key; migrate v1.0.0 fields before calling');
  const normalizedAnswers = {}, summaryCards = [];
  for (const [key,q] of Object.entries(QUESTIONS)) {
    const value=answers[key] ?? null;
    if (value !== null && (typeof value !== 'string' || !Object.hasOwn(q.choices,value))) throw new TypeError(`Invalid ${key}`);
    normalizedAnswers[key]=value;
    if (value !== null) summaryCards.push({id:key,title:q.title,text:q.choices[value]});
  }
  const guidance=selectGuidance(normalizedAnswers,summaryCards);
  const foodAction={id:'food_information',label:'식품으로 챙기는 방법',defaultExpanded:false};
  const outdoorAction={id:'outdoor_information',label:'야외활동 시 참고할 점',defaultExpanded:false};
  return {
    version:VERSION,module:'vitamin_d_information',method:'self_report_rules',
    title:'비타민 D 생활 정보',
    completion:summaryCards.length===0?'unanswered':summaryCards.length===4?'complete':'partial',
    normalizedAnswers,summaryCards,guidance,
    presentation:{order:['guidance.headline','guidance.summary','guidance.nextStep','actions','notices'],summaryCardsPlacement:'optional_details',noticeStyle:'secondary_visible'},
    emptyMessage:summaryCards.length===0?'생활 문항에 답하면 응답을 간단히 정리해 드려요. 건너뛰어도 일반 정보를 볼 수 있어요.':null,
    notices:['생활 응답에 따른 참고 안내이며, 비타민 D 상태를 측정한 결과는 아니에요.'],
    outdoorInformation:{title:'야외활동 시 참고할 점',text:'햇빛을 통한 비타민 D 합성은 계절·지역·나이 등 여러 조건에 따라 달라질 수 있어요. 비타민 D를 위해 햇빛 노출 시간을 늘리도록 권하지 않아요. 야외에서는 자외선 보호 수칙을 지켜 주세요.'},
    foodInformation:{title:'비타민 D 식품 정보',text:'연어·고등어 같은 생선, 달걀노른자 등에 비타민 D가 들어 있어요. 강화식품은 영양표시에서 비타민 D 함유 여부를 확인해 주세요.'},
    actions:[
      ...(guidance.primaryActionId==='outdoor_information'?[outdoorAction,foodAction]:[foodAction,outdoorAction]),
      {id:'product_information',label:'관련 제품 정보',defaultExpanded:false,trigger:'explicit_user_action',nutrientId:'vitamin_d',scope:'general_information',eligibility:'all_users'}
    ],
    productNotice:'관련 제품의 일반 정보이며, 개인의 복용 필요성이나 적합성을 확인한 결과는 아니에요.'
  };
}
