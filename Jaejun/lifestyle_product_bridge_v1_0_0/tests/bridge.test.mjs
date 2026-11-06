import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildInterestCards, buildLifestyleNotes, matchesInterest, listProducts } from '../src/bridge.js';
const products = JSON.parse(readFileSync(new URL('../data/products.json', import.meta.url), 'utf8'));

test('원본 최종 목록 전체를 보존하고 신고번호가 중복되지 않는다', () => {
  assert.equal(products.length, 2188);
  assert.equal(new Set(products.map(p => p.id)).size, 2188);
  for (const [group, count] of Object.entries({'유산균':964,'오메가3':523,'루테인':394,'밀크씨슬':307})) {
    assert.equal(products.filter(p => p.ingredient === group).length, count);
  }
});
test('관심 선택 없음은 카드 없음, 중복 선택은 한 번만', () => {
  assert.deepEqual(buildInterestCards(), []);
  const cards = buildInterestCards(['eye', 'eye']);
  assert.equal(cards.length, 1);
  assert.equal(cards[0].source, 'user_interest');
  assert.equal(cards[0].probability, null);
  assert.equal(cards[0].grade, null);
  assert.throws(() => buildInterestCards(['unknown']), RangeError);
});
test('생활습관 안내는 제품 선택을 만들어내지 않는다', () => {
  const notes = buildLifestyleNotes({monthlyDrinking:true, prolongedSitting:true});
  assert.equal(notes.length, 2);
  assert(notes.every(n => !('ingredient' in n) && !('interestId' in n)));
  assert.equal(buildLifestyleNotes({monthlyDrinking:false}).length, 0);
});
test('눈 건강 기본은 루테인, 오메가3는 명시한 추가 기능만', () => {
  const base = listProducts(products, {interestId:'eye'});
  assert.equal(base.total, 394);
  assert(base.items.every(p => p.ingredient === '루테인'));
  const generalEye = {ingredient:'오메가3', functionText:'헤마토코쿠스: 눈 건강에 도움'};
  assert.equal(matchesInterest(generalEye, 'eye', {includeEyeOmega3:true}), false);
  assert.equal(matchesInterest({ingredient:'오메가3', functionText:'건조한 눈을 개선하여 눈 건강에 도움'}, 'eye', {includeEyeOmega3:true}), true);
  assert.equal(matchesInterest({ingredient:'오메가3', functionText:'기억력 개선'}, 'circulation'), false);
});
test('페이지를 순회하면 중복·누락 없이 전체 목록이 나온다', () => {
  const first = listProducts(products, {interestId:'gut', pageSize:20});
  const ids = [];
  for (let page=1; page<=first.totalPages; page++) ids.push(...listProducts(products,{interestId:'gut',pageSize:20,page}).items.map(p=>p.id));
  assert.equal(ids.length, 964);
  assert.equal(new Set(ids).size, 964);
  assert.deepEqual(listProducts(products,{interestId:'gut'}), listProducts(products,{interestId:'gut'}));
});
test('조건 검색·빈 결과·페이지 보정과 원본 불변성', () => {
  const before = JSON.stringify(products);
  const got = listProducts(products,{interestId:'gut',form:'분말',pool:'단일',maxDailyUnits:1,page:999});
  assert(got.items.every(p => p.form==='분말' && p.pool==='단일' && p.dailyUnits<=1));
  assert.equal(got.page, Math.max(1,got.totalPages));
  const empty = listProducts(products,{interestId:'gut',search:'no_product_987654321'});
  assert.equal(empty.total, 0); assert.equal(empty.totalPages,0); assert.equal(empty.page,1);
  assert.equal(JSON.stringify(products),before);
  assert.throws(()=>listProducts(products,{interestId:'gut',pageSize:1000}),RangeError);
});
