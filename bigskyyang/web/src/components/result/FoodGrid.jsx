import Illust from '../Illust.jsx'

// 챙겨 먹으면 좋은 음식 타일: 그림과 이름만. 그림은 public/illust/food_{이름}
const FILE = {
  '귤·키위': 'tangerine_kiwi',
  '두부·생선 안주': 'tofu_fish',
  '우유·요구르트': 'milk_yogurt',
  바나나: 'banana',
  // '채소'는 기본 음식(골고루, data/tips.js BALANCED_FOODS)에만 쓰여 샐러드 그림
  채소: 'salad',
  '채소 반찬': 'vegetables',
  '채소·나물': 'vegetables',
  과일: 'fruit',
  달걀: 'egg',
  '콩·두부': 'bean_tofu',
  '치즈·요구르트': 'cheese_yogurt',
  잡곡밥: 'multigrain_rice',
  생선: 'fish',
}

// 3열 타일에서 긴 이름이 어색하게 끊기지 않도록 표시 이름과 줄바꿈을 정한다
const LINES = {
  '치즈·요구르트': '치즈/요거트',
  '우유·요구르트': '우유\n요구르트',
  '두부·생선 안주': '두부·생선\n안주',
}

export default function FoodGrid({ foods }) {
  return (
    <ul className="grid grid-cols-3 gap-2.5">
      {foods.map((f) => (
        <li key={f.label} className="flex flex-col items-center rounded-card bg-cream px-1 py-3 text-center">
          <Illust name={FILE[f.label] && `food_${FILE[f.label]}`} emoji={f.emoji} className="size-14" emojiClass="text-3xl" />
          <span className="mt-1.5 text-xs leading-tight font-bold whitespace-pre-line min-[375px]:text-sm">{LINES[f.label] ?? f.label}</span>
        </li>
      ))}
    </ul>
  )
}
