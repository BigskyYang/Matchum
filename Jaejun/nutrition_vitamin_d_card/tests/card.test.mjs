import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {buildVitaminDCard,appendVitaminDCard,VERSION} from '../src/vitaminDCard.mjs';
import {buildProductsForResultCards,getResultDropdownOptions} from '../src/productAdapter.mjs';
import {buildProductResult} from '../compat/productBridge.v1.0.1.mjs';
const schema=JSON.parse(readFileSync(new URL('../config/survey.ko.json',import.meta.url),'utf8'));
const low={commute:'car',lunch_outing:'rarely',exercise_setting:'indoor',day_off_outing:'rarely'};
const pattern=a=>buildVitaminDCard(a)?.reason.patternKey;
const catalog={targets:['일반'],catalog_version:'test',categories:[{category_id:'calcium',label:'칼슘',order:1},{category_id:'vitamin_d',label:'비타민 D',order:2}],products:{c:{product_id:'c',form:'정'},d:{product_id:'d',form:'캡슐'}},links:[{category_id:'calcium',target:'일반',product_id:'c',source_order:1},{category_id:'vitamin_d',target:'일반',product_id:'d',source_order:2}]};
test('same four optional question IDs and values remain supported',()=>{
 assert.equal(schema.version,VERSION);assert.equal(schema.questions.length,4);
 assert.ok(schema.questions.every(q=>q.type==='single_select'&&!q.required));
});
test('all 400 response combinations generate valid nullable cards',()=>{
 let count=0;
 for(const a of schema.questions[0].options)for(const b of schema.questions[1].options)for(const c of schema.questions[2].options)for(const d of schema.questions[3].options){
  const card=buildVitaminDCard({commute:a.value,lunch_outing:b.value,exercise_setting:c.value,day_off_outing:d.value});
  if(card){assert.equal(card.nutrient_id,'vitamin_d');assert.equal(card.assessment.grade,null);assert.equal(card.assessment.probability,null);assert.ok(card.reason.title&&card.reason.text&&card.foodGuidance.text);assert.equal(card.productLink.categoryId,'vitamin_d');assert.equal(Object.hasOwn(card,'score'),false);}
  count++;
 }
 assert.equal(count,400);
});
test('no usable lifestyle evidence does not fabricate a personal card',()=>{
 assert.equal(buildVitaminDCard(),null);assert.equal(buildVitaminDCard({commute:'walk_cycle'}),null);
 assert.equal(buildVitaminDCard({commute:'car',lunch_outing:'unknown',exercise_setting:'unknown',day_off_outing:'unknown'}),null);
});
test('combined patterns produce distinct interpretations',()=>{
 assert.equal(pattern(low),'limited_contexts');
 assert.equal(pattern({...low,day_off_outing:'often'}),'day_off_contact');
 assert.equal(pattern({...low,lunch_outing:'often'}),'lunch_contact');
 assert.equal(pattern({...low,exercise_setting:'daytime_outdoor'}),'exercise_contact');
 assert.equal(pattern({...low,exercise_setting:'other_time_outdoor'}),'time_context');
 assert.equal(pattern({...low,lunch_outing:'often',day_off_outing:'often'}),'multiple_contacts');
});
test('unknown exercise is not treated as indoor or no exercise',()=>{
 assert.equal(pattern({...low,exercise_setting:'unknown'}),'varied_contexts');
});
test('commute does not change the interpretation of three activity answers',()=>{
 for(const o of schema.questions[0].options) assert.equal(pattern({...low,commute:o.value}),'limited_contexts');
});
test('append preserves existing five model cards without mutation',()=>{
 const base=Array.from({length:5},(_,i)=>({nutrient_id:'model_'+i,grade:'High',probability:.8}));const before=JSON.stringify(base);
 const out=appendVitaminDCard(base,low);assert.equal(out.length,6);assert.deepEqual(out.slice(0,5),base);assert.equal(JSON.stringify(base),before);
 assert.equal(out[5].source.label,'추가 생활문항 기반 안내');
});
test('repeated update does not duplicate D and cleared answers remove only D',()=>{
 const base=[{nutrient_id:'calcium'}];const out=appendVitaminDCard(appendVitaminDCard(base,low),low);
 assert.equal(out.length,2);assert.deepEqual(appendVitaminDCard(out,{}),base);
});
test('existing bridge receives D as explicit information request, never model ID',()=>{
 const cards=appendVitaminDCard([{nutrient_id:'calcium'}],low),o={selectedNutrientIds:['calcium']},before=JSON.stringify(o);
 const r=buildProductsForResultCards(buildProductResult,catalog,cards,o);
 assert.equal(JSON.stringify(o),before);assert.equal(r.groups.length,2);
 assert.equal(r.groups.find(g=>g.category_id==='vitamin_d').connection_kind,'information_only');
 assert.equal(r.groups[1].page_size,20);
 assert.deepEqual(getResultDropdownOptions(r,cards).map(x=>x.value),['calcium','vitamin_d']);
});
test('no D card does not automatically request D or expose unrelated info categories',()=>{
 const r=buildProductsForResultCards(buildProductResult,catalog,[{nutrient_id:'calcium'}],{selectedNutrientIds:['calcium']});
 assert.deepEqual(r.groups.map(x=>x.category_id),['calcium']);
 const infoOnly=buildProductResult(catalog,{informationCategoryIds:['vitamin_d']});
 assert.deepEqual(getResultDropdownOptions(infoOnly,[]),[]);
});
test('existing form filtering and source order are retained',()=>{
 const cards=appendVitaminDCard([],low);
 const r=buildProductsForResultCards(buildProductResult,catalog,cards,{filters:{vitamin_d:{forms:['정']}}});
 assert.equal(r.groups[0].total_count,0);assert.equal(getResultDropdownOptions(r,cards)[0].disabled,false);
});
test('invalid input is rejected instead of silently changing answers',()=>{
 for(const a of [null,[],{score:3},{outdoor_days:'none'},{vitamin_d_foods:['fish']},{lunch_outing:'BAD'}]) assert.throws(()=>buildVitaminDCard(a));
 assert.throws(()=>appendVitaminDCard([null],low));
});
