/** Adapter to existing product bridge; no category scoring or catalog mutation. */
export function buildProductsForResultCards(buildProductResult,catalog,cards,options={}) {
  if(typeof buildProductResult!=='function') throw new TypeError('buildProductResult is required');
  if(!Array.isArray(cards)) throw new TypeError('cards must be an array');
  const showD=cards.some(c=>c?.nutrient_id==='vitamin_d' && c?.source?.id==='lifestyle_questionnaire');
  const information=options.informationCategoryIds??[];
  if(!Array.isArray(information) || information.some(x=>typeof x!=='string')) throw new TypeError('informationCategoryIds must be a string array');
  return buildProductResult(catalog,{
    ...options,
    informationCategoryIds:[...new Set([...information,...(showD?['vitamin_d']:[])])],
  });
}

/** Same dropdown, preserving model categories and adding D only when its card exists. */
export function getResultDropdownOptions(result,cards) {
  if(!Array.isArray(result?.groups)||!Array.isArray(cards)) throw new TypeError('groups and cards must be arrays');
  const showD=cards.some(c=>c?.nutrient_id==='vitamin_d' && c?.source?.id==='lifestyle_questionnaire');
  return result.groups.filter(g=>g.connection_kind==='model_nutrient'||(showD && g.category_id==='vitamin_d')).map(g=>({
    value:g.category_id,label:g.label,count:g.unfiltered_count,disabled:g.unfiltered_count===0,
    linked_nutrient_ids:[...g.linked_nutrient_ids],
    source:g.category_id==='vitamin_d'?'추가 생활문항 기반 안내':'model',
  }));
}
