// 재준님 비타민 D 기존 영양소 카드 연결 v1.3.0 사본 (analysis/03_personal_prediction/vitamin_d_card/src/vitaminDCard.mjs)
// 본문은 고치지 않는다. 재준님 파일이 바뀌면 그대로 다시 복사한다 (vitaminD.test.js가 같은지 확인)
export const VERSION = '1.3.0';
const CHOICES = {
  commute:['walk_cycle','transit','car','no_regular_commute','unknown'],
  lunch_outing:['often','sometimes','rarely','unknown'],
  exercise_setting:['daytime_outdoor','other_time_outdoor','indoor','none','unknown'],
  day_off_outing:['often','sometimes','rarely','unknown'],
};

function normalize(answers) {
  if (!answers || typeof answers!=='object' || Array.isArray(answers)) throw new TypeError('answers must be an object');
  if (Object.keys(answers).some(k=>!Object.hasOwn(CHOICES,k))) throw new TypeError('Unknown answer field');
  return Object.fromEntries(Object.entries(CHOICES).map(([k,values])=>{
    const v=answers[k]??null;
    if(v!==null && !values.includes(v)) throw new TypeError(`Invalid ${k}`);
    return [k,v];
  }));
}

// Display interpretations only: no exposure dose, deficiency probability or grade.
function interpret(a) {
  const l=a.lunch_outing, w=a.day_off_outing, e=a.exercise_setting;
  if(l==='rarely' && w==='rarely' && e==='daytime_outdoor') return {
    key:'exercise_contact',title:'낮 야외활동은 운동을 할 때 주로 나타나요',
    text:'점심과 쉬는 날의 외출은 드물지만, 운동은 낮에 야외에서 하는 조합이에요. 응답한 생활 장면에서는 운동이 낮 야외활동의 주요 접점으로 나타나요.',
    next:'야외운동 여부와 별개로, 비타민 D를 얻는 식품 경로도 함께 살펴보세요.'};
  if(l==='rarely' && w==='rarely' && ['indoor','none'].includes(e)) return {
    key:'limited_contexts',title:'일상에서 낮 야외활동의 접점이 적게 나타나요',
    text:'점심과 쉬는 날 모두 외출이 드물고, 낮 야외운동도 선택하지 않았어요. 한 장면만의 문제가 아니라 응답한 여러 생활 장면에서 낮 야외활동 기회가 제한적으로 나타나는 패턴이에요.',
    next:'햇빛을 통한 확보를 당연하게 전제하기보다, 비타민 D 식품 등 다른 공급 경로를 함께 확인해 보세요.'};
  if(l==='rarely' && w==='rarely' && e==='other_time_outdoor') return {
    key:'time_context',title:'야외운동과 낮시간 외출을 구분해 볼 패턴이에요',
    text:'야외운동은 하지만 선택한 시간대는 아침·저녁·밤이고, 점심과 쉬는 날 외출은 드문 조합이에요. 야외에서 운동한다는 사실만으로 낮시간 활동 기회까지 충분히 확인되는 것은 아니에요.',
    next:'비타민 D 식품 정보를 함께 확인하고, 야외활동 때는 자외선 보호 수칙을 지켜 주세요.'};
  if(l==='rarely' && w==='often' && e!=='daytime_outdoor') return {
    key:'day_off_contact',title:'낮 야외활동의 접점이 쉬는 날에 나타나요',
    text:'점심 외출은 드물지만 쉬는 날 낮 외출은 잦은 조합이에요. 두 외출 장면을 비교하면 쉬는 날이 낮 야외활동의 주된 접점이에요.',
    next:'활동하는 날의 유무만으로 비타민 D 확보를 판단하기보다 식품 공급원도 함께 살펴보세요.'};
  if(l==='often' && w==='rarely') return {
    key:'lunch_contact',title:'평일 점심 외출이 반복적인 야외활동 접점이에요',
    text:'쉬는 날 낮 외출은 드물지만 점심에는 거의 매일 외출하는 조합이에요. 두 외출 장면에서는 평일 점심이 반복적인 야외활동 접점으로 나타나요.',
    next:'이 생활 특징과 함께 비타민 D 식품 정보를 확인해 보세요.'};
  if(l==='often' && w==='often') return {
    key:'multiple_contacts',title:'평일과 쉬는 날 모두 외출 접점이 있어요',
    text:'점심 외출과 쉬는 날 낮 외출이 모두 잦은 조합이에요. 야외활동의 접점이 한 장면에만 몰려 있지 않은 패턴이에요.',
    next:'야외활동 시 자외선 보호를 지키고, 식품으로 얻는 비타민 D 정보도 함께 확인해 보세요.'};
  if(e==='daytime_outdoor') return {
    key:'exercise_contact',title:'낮 야외운동이 생활 속 접점으로 나타나요',
    text:'운동을 하는 장면에서 낮 야외활동 기회가 확인돼요. 점심·쉬는 날 외출과 다른 경로로 야외활동을 하고 있는 것으로 해석할 수 있어요.',
    next:'야외활동과 함께 식품을 통한 비타민 D 공급 경로도 살펴보세요.'};
  if(l==='often' || w==='often') return {
    key:'outing_contact',title:'자주 외출하는 생활 장면이 있어요',
    text:l==='often'?'점심 외출이 반복적인 야외활동 접점으로 나타나요. 쉬는 날과 운동 응답까지 고려하더라도 실제 노출량을 환산할 수는 없어요.':'쉬는 날 낮 외출이 야외활동의 접점으로 나타나요. 점심과 운동 응답만으로 평일 전체의 활동을 단정하지는 않아요.',
    next:'확인된 활동 장면과 함께 비타민 D 식품 정보를 살펴보세요.'};
  return {key:'varied_contexts',title:'생활 장면에 따라 야외활동 기회가 달라요',
    text:'응답에서 낮 외출이 늘 반복되는 하나의 패턴으로 모이지는 않았어요. 외출·운동의 상황별 차이를 살펴보고, 식품 등 다른 비타민 D 공급 경로도 함께 확인할 수 있어요.',
    next:'아래 식품 정보와 관련 제품 정보를 참고해 보세요.'};
}

/** Card contract for the same nutrient result list, not a standalone screen. */
export function buildVitaminDCard(answers={}) {
  const a=normalize(answers);
  const meaningful=['lunch_outing','exercise_setting','day_off_outing'].some(k=>a[k]!==null && a[k]!=='unknown');
  if(!meaningful) return null;
  const reason=interpret(a);
  const evidence=Object.entries(a).filter(([,v])=>v!==null).map(([questionId,value])=>({questionId,value}));
  return {
    id:'vitamin_d',nutrient_id:'vitamin_d',name:'비타민 D',version:VERSION,
    cardType:'nutrient_guidance',source:{id:'lifestyle_questionnaire',label:'추가 생활문항 기반 안내'},
    assessment:{type:'guidance',grade:null,probability:null},
    reason:{title:reason.title,text:reason.text,nextStep:reason.next,patternKey:reason.key,evidence},
    foodGuidance:{title:'식품으로 챙기는 방법',text:'연어·고등어 같은 생선과 달걀노른자 등에 비타민 D가 들어 있어요. 강화식품은 영양표시에서 비타민 D 함유 여부를 확인해 주세요.'},
    productLink:{categoryId:'vitamin_d',label:'관련 제품 정보',mode:'related_information',reuseExistingList:true,pageSize:20},
    note:'생활 응답을 해석한 참고 안내이며, 비타민 D 상태를 측정한 결과는 아니에요.',
    activityNote:'비타민 D를 위해 햇빛 노출 시간을 늘리도록 권하지 않아요. 야외에서는 자외선 보호 수칙을 지켜 주세요.',
    productNotice:'관련 제품의 정보이며, 개인의 복용 필요성이나 적합성을 확인한 결과는 아니에요.',
  };
}

/** Preserve existing card order/data, replace existing D at its place, never duplicate. */
export function appendVitaminDCard(existingCards,answers={}) {
  if(!Array.isArray(existingCards) || existingCards.some(x=>!x || typeof x!=='object' || Array.isArray(x))) throw new TypeError('existingCards must be an object array');
  const card=buildVitaminDCard(answers), out=[]; let placed=false;
  for(const c of existingCards){
    if((c.nutrient_id??c.id)==='vitamin_d') {if(card && !placed){out.push(card);placed=true;}}
    else out.push(c);
  }
  if(card && !placed) out.push(card);
  return out;
}
