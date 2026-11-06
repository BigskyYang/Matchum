// Example: replace imports/paths with those in the actual web project.
import {appendVitaminDCard} from '../src/vitaminDCard.mjs';
import {buildProductsForResultCards,getResultDropdownOptions} from '../src/productAdapter.mjs';
import {buildProductResult} from '../compat/productBridge.v1.0.1.mjs';

export function connectVitaminD({existingCards,vitaminDAnswers,catalog,selectedNutrientIds,productOptions={}}) {
  const cards=appendVitaminDCard(existingCards,vitaminDAnswers);
  const products=buildProductsForResultCards(buildProductResult,catalog,cards,{
    ...productOptions,selectedNutrientIds,
  });
  return {cards,products,dropdownOptions:getResultDropdownOptions(products,cards)};
}
