import {readFileSync} from 'node:fs';
import {buildVitaminDCard,appendVitaminDCard} from '../src/vitaminDCard.mjs';
const answers=JSON.parse(readFileSync(new URL('./answers.json',import.meta.url),'utf8'));
console.log(JSON.stringify({card:buildVitaminDCard(answers),cards:appendVitaminDCard([{nutrient_id:'calcium',name:'칼슘',assessment:{grade:'High',probability:0.8}}],answers)},null,2));
