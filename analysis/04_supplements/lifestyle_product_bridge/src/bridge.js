/** 관심 선택으로 제품 정보를 탐색하는 규칙. 필요도/결핍/효능 예측 모델이 아님. */
export const VERSION = '1.0.0';
export const INTERESTS = Object.freeze([
  { id: 'gut', label: '장 건강', ingredient: '유산균' },
  { id: 'eye', label: '눈 건강', ingredient: '루테인' },
  { id: 'circulation', label: '혈행·중성지질', ingredient: '오메가3' },
  { id: 'liver', label: '간 건강', ingredient: '밀크씨슬' },
]);

function getInterest(id) {
  const interest = INTERESTS.find(x => x.id === id);
  if (!interest) throw new RangeError(`알 수 없는 관심 항목: ${id}`);
  return interest;
}
function compact(text) { return String(text ?? '').replace(/\s/g, ''); }

export function matchesInterest(product, interestId, { includeEyeOmega3 = false } = {}) {
  const interest = getInterest(interestId);
  const text = compact(product.functionText);
  if (interestId === 'eye') {
    if (product.ingredient === '루테인') return true;
    // 오메가3 자체의 인정 문구에 건조한 눈 개선이 표시된 경우만 추가.
    // 함께 든 다른 원료의 일반적인 '눈 건강' 문구만으로 연결하지 않음.
    return includeEyeOmega3 && product.ingredient === '오메가3'
      && /건조한눈(?:을)?개선/.test(text);
  }
  if (product.ingredient !== interest.ingredient) return false;
  if (interestId === 'circulation') return /혈행|중성지질/.test(text);
  return true;
}

/** 사용자 선택만 사용. 생활습관/영양 등급으로 관심 항목을 자동 생성하지 않음. */
export function buildInterestCards(selectedIds = []) {
  if (!Array.isArray(selectedIds)) throw new TypeError('selectedIds는 배열이어야 함');
  const ids = [...new Set(selectedIds)];
  return ids.map(id => {
    const item = getInterest(id);
    return { ...item, source: 'user_interest', sourceLabel: '내가 관심 있어 선택한 항목',
      title: `${item.label} 제품 정보`, probability: null, grade: null };
  });
}

/** 기존 웹에서 판정한 생활습관 플래그를 받아 생활 안내만 생성함.
 * 플래그의 기준값/질문은 이 모듈에서 새로 만들지 않음. 제품군을 반환하지 않음.
 */
export function buildLifestyleNotes({ monthlyDrinking = false, prolongedSitting = false,
  irregularMeals = false } = {}) {
  const notes = [];
  if (monthlyDrinking === true) notes.push({ id: 'alcohol',
    text: '음주 응답을 바탕으로 음주 빈도와 양을 돌아볼 수 있어요. 제품 정보는 음주의 영향을 보완한다는 의미가 아니에요.' });
  if (prolongedSitting === true) notes.push({ id: 'sitting',
    text: '앉아 있는 시간이 긴 편이라는 기존 설문 결과가 있어요. 활동과 휴식에 관한 생활 안내를 함께 살펴보세요.' });
  if (irregularMeals === true) notes.push({ id: 'meals',
    text: '끼니가 불규칙하다는 기존 설문 결과가 있어요. 제품 정보와 함께 식사 습관 안내를 살펴보세요.' });
  return notes;
}

function compareProducts(a, b) {
  const compared = String(a.name).localeCompare(String(b.name), 'ko');
  // 동률도 고정 정렬. 서버/브라우저 간 엄밀한 동일 순서가 필요하면 id 정렬 사용.
  return compared || String(a.id).localeCompare(String(b.id), 'en');
}

/** 이 목록은 원본의 '남은 제품'만 사용. 추가 품질 평가/점수/광고 순위 없음. */
export function listProducts(products, { interestId, includeEyeOmega3 = false,
  form = '', pool = '', maxDailyUnits = null, search = '',
  page = 1, pageSize = 12, sort = 'name' } = {}) {
  getInterest(interestId);
  if (![12, 16, 20].includes(pageSize)) throw new RangeError('pageSize는 12, 16, 20 중 선택');
  if (!Number.isInteger(page) || page < 1) throw new RangeError('page는 1 이상의 정수');
  if (!['name', 'id'].includes(sort)) throw new RangeError('지원하지 않는 정렬');
  if (maxDailyUnits !== null && (!Number.isFinite(maxDailyUnits) || maxDailyUnits <= 0)) {
    throw new RangeError('maxDailyUnits는 양수 또는 null');
  }
  const q = compact(search).toLocaleLowerCase('ko');
  const filtered = products.filter(p => matchesInterest(p, interestId, { includeEyeOmega3 }))
    .filter(p => !form || p.form === form)
    .filter(p => !pool || p.pool === pool)
    .filter(p => maxDailyUnits === null ||
      (Number.isFinite(p.dailyUnits) && p.dailyUnits <= maxDailyUnits))
    .filter(p => !q || compact(`${p.name} ${p.manufacturer} ${p.id}`).toLocaleLowerCase('ko').includes(q));
  const facets = {
    forms: [...new Set(products.filter(p => matchesInterest(p, interestId, { includeEyeOmega3 })).map(p => p.form))].filter(Boolean).sort(),
    pools: [...new Set(products.filter(p => matchesInterest(p, interestId, { includeEyeOmega3 })).map(p => p.pool))].filter(Boolean).sort(),
  };
  filtered.sort(sort === 'id' ? (a, b) => String(a.id).localeCompare(String(b.id), 'en') : compareProducts);
  const total = filtered.length;
  const totalPages = Math.ceil(total / pageSize);
  const currentPage = totalPages ? Math.min(page, totalPages) : 1;
  return { items: filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize),
    total, totalPages, page: currentPage, pageSize, facets,
    sortLabel: sort === 'id' ? '품목제조신고번호순' : '제품명순',
    sourceLabel: '사용자가 선택한 관심 항목에 따른 제품 정보' };
}
