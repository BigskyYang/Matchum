import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {buildVitaminDInfo,VERSION} from '../src/vitaminDInfo.mjs';
const schema=JSON.parse(readFileSync(new URL('../config/survey.ko.json',import.meta.url),'utf8'));
test('four optional single-choice lifestyle questions match version',()=>{
 assert.equal(schema.questions.length,4);assert.equal(schema.version,VERSION);
 for(const q of schema.questions){assert.equal(q.type,'single_select');assert.equal(q.required,false);}
 assert.equal(schema.questions.some(q=>/food|duration/.test(q.id)),false);
});
test('unanswered and partial responses are not inferred',()=>{
 const empty=buildVitaminDInfo();assert.equal(empty.completion,'unanswered');assert.equal(empty.summaryCards.length,0);
 assert.ok(Object.values(empty.normalizedAnswers).every(x=>x===null));
 const partial=buildVitaminDInfo({commute:'transit'});assert.equal(partial.completion,'partial');assert.equal(partial.summaryCards.length,1);
});
test('all 400 complete response combinations summarize without scores or gates',()=>{
 let count=0;
 for(const a of schema.questions[0].options)for(const b of schema.questions[1].options)for(const c of schema.questions[2].options)for(const d of schema.questions[3].options){
  const r=buildVitaminDInfo({commute:a.value,lunch_outing:b.value,exercise_setting:c.value,day_off_outing:d.value});
  assert.equal(r.completion,'complete');assert.equal(r.summaryCards.length,4);
  for(const k of ['score','grade','probability','recommendedDose','selectedNutrientIds'])assert.equal(Object.hasOwn(r,k),false);
  const p=r.actions.find(x=>x.id==='product_information');
  assert.equal(p.eligibility,'all_users');assert.equal(p.trigger,'explicit_user_action');assert.equal(p.defaultExpanded,false);count++;
 }
 assert.equal(count,400);
});
test('unknown and no activity have different summaries',()=>{
 const u=buildVitaminDInfo({exercise_setting:'unknown'}),n=buildVitaminDInfo({exercise_setting:'none'});
 assert.notEqual(u.summaryCards[0].text,n.summaryCards[0].text);
 assert.match(u.summaryCards[0].text,/모르겠/);assert.match(n.summaryCards[0].text,/운동을 하지/);
});
test('no commute does not assert no outdoors',()=>{
 assert.match(buildVitaminDInfo({commute:'no_regular_commute'}).summaryCards[0].text,/정기적인 출퇴근·통학이 없/);
});
test('old fields and invalid answers are rejected',()=>{
 for(const a of [null,[],{vitamin_d_foods:['fish']},{outdoor_days:'none'},{outdoor_duration:'lt15'},{commute:'BAD'},{commute:0}])assert.throws(()=>buildVitaminDInfo(a),TypeError);
});
test('same input produces same output without mutation',()=>{
 const a={commute:'transit',lunch_outing:'rarely'};const before=JSON.stringify(a);
 assert.deepEqual(buildVitaminDInfo(a),buildVitaminDInfo(a));assert.equal(JSON.stringify(a),before);
});
test('limited contexts lead with food information and factual evidence',()=>{
 const r=buildVitaminDInfo({commute:'car',lunch_outing:'rarely',exercise_setting:'indoor',day_off_outing:'rarely'});
 assert.equal(r.guidance.key,'limited_outing_contexts');assert.equal(r.actions[0].id,'food_information');
 assert.match(r.guidance.headline,/점심시간과 쉬는 날/);assert.match(r.guidance.summary,/실내/);
 assert.match(r.guidance.nextStep,/식품 정보/);
});
test('daytime exercise has precedence when other outings are rare',()=>{
 const r=buildVitaminDInfo({lunch_outing:'rarely',exercise_setting:'daytime_outdoor',day_off_outing:'rarely'});
 assert.equal(r.guidance.key,'daytime_exercise');assert.equal(r.actions[0].id,'outdoor_information');
 assert.match(r.guidance.summary,/거의 밖에 나가지/);assert.match(r.guidance.summary,/낮에 야외/);
});
test('day-off and lunch outings get their own supported headlines',()=>{
 assert.equal(buildVitaminDInfo({day_off_outing:'often'}).guidance.key,'day_off_outings');
 assert.equal(buildVitaminDInfo({lunch_outing:'often'}).guidance.key,'lunch_outings');
});
test('commute alone or unknown cannot produce limited exposure guidance',()=>{
 for(const commute of schema.questions[0].options){
  const r=buildVitaminDInfo({commute:commute.value,lunch_outing:'unknown',exercise_setting:'unknown',day_off_outing:'unknown'});
  assert.equal(r.guidance.key,'general_information');
 }
 const mixed=buildVitaminDInfo({lunch_outing:'rarely',exercise_setting:'unknown',day_off_outing:'rarely'});
 assert.equal(mixed.guidance.key,'varied_contexts');
});
test('action IDs match information and brief caveat remains visible',()=>{
 const r=buildVitaminDInfo();
 assert.ok(r.foodInformation.text);assert.ok(r.outdoorInformation.text);
 assert.deepEqual(r.actions.map(x=>x.id),['food_information','outdoor_information','product_information']);
 assert.equal(r.notices.length,1);assert.match(r.notices[0],/状態|상태를 측정한 결과는 아니/);
 assert.equal(r.presentation.noticeStyle,'secondary_visible');
 assert.deepEqual(r.presentation.order,['guidance.headline','guidance.summary','guidance.nextStep','actions','notices']);
});
