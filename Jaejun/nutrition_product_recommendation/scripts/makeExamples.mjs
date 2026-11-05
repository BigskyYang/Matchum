import { readFileSync, writeFileSync } from 'node:fs';
import { buildProductResult, fromModelResponse, getNutrientDropdownOptions } from '../src/productBridge.mjs';
const root=new URL('../',import.meta.url);
const c=JSON.parse(readFileSync(new URL('data/nutritionProducts.json',root)));
const examples={
  'calcium_page_1': {selectedNutrientIds:['calcium'],pageSize:20},
  'multiple_nutrients': {selectedNutrientIds:['calcium','magnesium','vitamin_b1','vitamin_b2','sodium_excess'],pageSize:20},
  'general_information': {informationCategoryIds:['vitamin_d','multi_balance'],pageSize:20},
};
for(const [name,args] of Object.entries(examples)) {
 writeFileSync(new URL(`examples/${name}.json`,root),JSON.stringify({
  example_kind:'connection_demo_only_not_model_prediction',request:args,
  response:buildProductResult(c,args),
 },null,2));
}

const result=buildProductResult(c,{selectedNutrientIds:['calcium','magnesium','vitamin_b1','vitamin_b2','sodium_excess'],informationCategoryIds:['vitamin_d']});
writeFileSync(new URL('examples/personal_dropdown.json',root),JSON.stringify({
  example_kind:'connection_demo_only_not_model_prediction',
  selected_nutrient_ids:['calcium','magnesium','vitamin_b1','vitamin_b2','sodium_excess'],
  options:getNutrientDropdownOptions(result),
  selected_category_id:'magnesium',
  note:'비타민 D는 별도 일반 정보 영역에 분리함',
},null,2));
