import test from 'node:test';
import assert from 'node:assert/strict';
import {buildVitaminDInfo, VERSION} from '../src/vitaminDInfo.mjs';

test('unanswered data stays unknown and preserves optional access', () => {
  const r=buildVitaminDInfo();
  assert.equal(r.completion,'unanswered');
  assert.deepEqual(r.normalizedAnswers,{outdoor_days:null,outdoor_duration:null,vitamin_d_foods:null});
  assert.equal(r.summaryCards.length,0);
  assert.equal(r.actions[1].eligibility,'all_users');
});
test('none skips duration without inferring vitamin D status', () => {
  const r=buildVitaminDInfo({outdoor_days:'none',outdoor_duration:'ge60',vitamin_d_foods:['none']});
  assert.equal(r.normalizedAnswers.outdoor_duration,null);
  assert.equal(r.completion,'complete');
  assert.equal(r.summaryCards[0].detail,null);
});
test('incomplete follow-up remains partial', () => {
  assert.equal(buildVitaminDInfo({outdoor_days:'days_3_4',vitamin_d_foods:['fish']}).completion,'partial');
});
test('unknown is not none', () => {
  const r=buildVitaminDInfo({outdoor_days:'irregular',outdoor_duration:'unknown',vitamin_d_foods:['unknown']});
  assert.match(r.summaryCards[1].text,/잘 모르겠/);
  assert.equal(r.normalizedAnswers.vitamin_d_foods[0],'unknown');
});
test('multiple foods use deterministic display order without mutating input', () => {
  const a={outdoor_days:'days_5_7',outdoor_duration:'lt15',vitamin_d_foods:['fortified','fish']};
  const before=JSON.stringify(a); const r=buildVitaminDInfo(a);
  assert.equal(JSON.stringify(a),before);
  assert.deepEqual(r.normalizedAnswers.vitamin_d_foods,['fish','fortified']);
});
test('exclusive and duplicate answers are rejected', () => {
  for(const v of [['none','fish'],['unknown','fish'],['none','unknown'],['fish','fish'],[],['BAD']]) {
    assert.throws(()=>buildVitaminDInfo({vitamin_d_foods:v}),TypeError);
  }
});
test('invalid payloads and enum codes are rejected', () => {
  for(const a of [null,[],{score:3},{outdoor_days:'BAD'},{outdoor_duration:15},{vitamin_d_foods:'fish'}]) assert.throws(()=>buildVitaminDInfo(a),TypeError);
});
test('all 189 complete answer combinations work and never gate product information', () => {
  const fs=['none','days_1_2','days_3_4','days_5_7','irregular'];
  const ds=['lt15','min15_30','min30_60','ge60','unknown'];
  const foodsets=[['none'],['unknown'],['fish'],['egg_yolk'],['fortified'],['fish','egg_yolk'],['fish','fortified'],['egg_yolk','fortified'],['fish','egg_yolk','fortified']];
  let count=0;
  for(const f of fs)for(const d of f==='none'?[null]:ds)for(const food of foodsets){
    const r=buildVitaminDInfo({outdoor_days:f,outdoor_duration:d,vitamin_d_foods:food});
    assert.equal(r.completion,'complete'); assert.equal(r.version,VERSION);
    assert.equal(r.actions[1].defaultExpanded,false);
    assert.equal(r.actions[1].trigger,'explicit_user_action');
    assert.equal(r.actions[1].eligibility,'all_users');
    for(const k of ['score','grade','probability','recommendedDose','selectedNutrientIds'])assert.equal(Object.hasOwn(r,k),false);
    count++;
  }
  assert.equal(count,189);
});
test('repeat calls yield identical output', () => {
  const a={outdoor_days:'days_1_2',outdoor_duration:'min15_30',vitamin_d_foods:['fish']};
  assert.deepEqual(buildVitaminDInfo(a),buildVitaminDInfo(a));
});
