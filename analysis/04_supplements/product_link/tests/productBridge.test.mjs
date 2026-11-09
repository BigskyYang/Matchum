import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildProductResult, fromModelResponse, getNutrientDropdownOptions } from '../src/productBridge.mjs';
const c = JSON.parse(readFileSync(new URL('../data/nutritionProducts.json', import.meta.url)));

test('source catalog preserves confirmed counts and identifiers', () => {
  assert.equal(Object.keys(c.products).length, 2786);
  assert.equal(c.links.length, 3534);
  assert.ok(Object.keys(c.products).every(x => typeof x === 'string' && /^\d+$/.test(x)));
});
test('every source category/target can be paged without omissions, duplication or reordering', () => {
  for (const cat of c.categories) for (const target of c.targets) {
    const expected = c.links.filter(x => x.category_id === cat.category_id && x.target === target)
      .sort((a,b) => a.source_order-b.source_order).map(x => x.product_id);
    const ids = [];
    const nutrient = cat.category_id === 'vitamin_b' ? 'vitamin_b1' : cat.category_id;
    const args = cat.connection_kind === 'information_only'
      ? { informationCategoryIds: [cat.category_id] } : { selectedNutrientIds: [nutrient] };
    for (let p=1; p<=Math.max(1,Math.ceil(expected.length/20)); p++) {
      const g=buildProductResult(c,{...args,target,pages:{[cat.category_id]:p}}).groups[0];
      ids.push(...g.items.map(x=>x.product_id));
    }
    assert.deepEqual(ids,expected);
    assert.equal(new Set(ids).size,ids.length);
  }
});
test('B1+B2 merge into one B group and foods remain outside product lists', () => {
  const r=buildProductResult(c,{selectedNutrientIds:['vitamin_b1','vitamin_b2','sodium_excess','protein']});
  assert.equal(r.groups.length,1);
  assert.deepEqual(r.groups[0].linked_nutrient_ids,['vitamin_b1','vitamin_b2']);
  assert.deepEqual(r.food_only_nutrient_ids,['sodium_excess','protein']);
});
test('category order follows approved source and data count is independently deduplicated', () => {
  const r=buildProductResult(c,{selectedNutrientIds:['calcium','magnesium','vitamin_b2']});
  assert.deepEqual(r.groups.map(x=>x.category_id),['magnesium','vitamin_b','calcium']);
  const all=new Set(c.links.filter(x=>x.target==='일반'&&['magnesium','vitamin_b','calcium'].includes(x.category_id)).map(x=>x.product_id));
  assert.equal(r.unique_candidate_product_count,all.size);
});
test('D and multi are only displayed by explicit general-information requests', () => {
  assert.equal(buildProductResult(c,{selectedNutrientIds:['calcium']}).groups.length,1);
  const r=buildProductResult(c,{informationCategoryIds:['vitamin_d','multi_balance','multi_energy']});
  assert.ok(r.groups.every(x=>x.connection_kind==='information_only'));
});
test('target pools are separate; empty pools get no invented fallback', () => {
  assert.equal(buildProductResult(c,{selectedNutrientIds:['calcium'],target:'여성'}).groups[0].total_count,0);
  assert.ok(buildProductResult(c,{selectedNutrientIds:['magnesium'],target:'시니어'}).groups[0].items.every(x=>x.target==='시니어'));
});
test('display result exposes no product score, product grade, source rank or model probability', () => {
  const r=buildProductResult(c,{selectedNutrientIds:['calcium']});
  for(const p of r.groups[0].items) for(const key of ['점수','등급','score','grade','probability','source_order'])
    assert.equal(key in p,false);
});
test('empty model selections remain empty and selected objects map correctly', () => {
  assert.equal(fromModelResponse(c,{display_summary:{selected_nutrients:[]}}).groups.length,0);
  assert.equal(fromModelResponse(c,{display_summary:{selected_nutrients:[{nutrient_id:'calcium'}]}}).groups[0].category_id,'calcium');
});
test('form filters retain source ordering and recalculate counts', () => {
  const r=buildProductResult(c,{selectedNutrientIds:['calcium'],filters:{calcium:{forms:['젤리']}}});
  assert.ok(r.groups[0].items.every(x=>x.form==='젤리'));
  const expected=c.links.filter(x=>x.category_id==='calcium'&&x.target==='일반'&&c.products[x.product_id].form==='젤리');
  assert.equal(r.groups[0].total_count,expected.length);
});
test('invalid inputs fail explicitly and out-of-range pages return an empty page', () => {
  assert.throws(()=>buildProductResult(c,{pageSize:3}));
  assert.throws(()=>buildProductResult(c,{selectedNutrientIds:['made_up']}));
  assert.throws(()=>buildProductResult(c,{target:'unknown'}));
  assert.throws(()=>buildProductResult(c,{selectedNutrientIds:['calcium'],pages:{calcium:0}}));
  assert.equal(buildProductResult(c,{selectedNutrientIds:['calcium'],pages:{calcium:999}}).groups[0].items.length,0);
});

test('personal dropdown is restricted to selected model nutrients and merges B1/B2', () => {
  const r=buildProductResult(c,{selectedNutrientIds:['calcium','magnesium','vitamin_b1','vitamin_b2','sodium_excess'],informationCategoryIds:['vitamin_d','multi_balance']});
  const opts=getNutrientDropdownOptions(r);
  assert.deepEqual(opts.map(x=>x.value),['magnesium','vitamin_b','calcium']);
  assert.deepEqual(opts.map(x=>x.label),['마그네슘','비타민 B군','칼슘']);
  assert.deepEqual(opts[1].linked_nutrient_ids,['vitamin_b1','vitamin_b2']);
});
test('dropdown counts do not shrink when product-form filters are applied', () => {
  const r=buildProductResult(c,{selectedNutrientIds:['calcium'],filters:{calcium:{forms:['젤리']}}});
  const opts=getNutrientDropdownOptions(r);
  assert.equal(opts[0].count,334);
  assert.ok(r.groups[0].total_count<opts[0].count);
});
test('empty selected pools remain disabled and food-only selections give no dropdown', () => {
  const r=buildProductResult(c,{selectedNutrientIds:['calcium'],target:'여성'});
  assert.equal(getNutrientDropdownOptions(r)[0].disabled,true);
  assert.deepEqual(getNutrientDropdownOptions(buildProductResult(c,{selectedNutrientIds:['sodium_excess']})),[]);
});
