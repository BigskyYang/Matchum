import {readFileSync} from 'node:fs';
import {buildVitaminDInfo} from '../src/vitaminDInfo.mjs';
const answers=JSON.parse(readFileSync(new URL('./answers.json',import.meta.url),'utf8'));
console.log(JSON.stringify(buildVitaminDInfo(answers),null,2));
