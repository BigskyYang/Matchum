import { useState } from 'react'
import { NUTRIENT_GUIDE } from '../../data/nutrientGuide.js'
import BottomSheet from '../BottomSheet.jsx'
import Illust from '../Illust.jsx'
import NutrientArt from '../NutrientArt.jsx'

// 챙겨 먹으면 좋은 음식 타일: 그림과 이름만. 그림은 public/illust/food_{이름}
//   누르면 아래 창에 왜 골랐는지(내 응답), 들어 있는 영양소(내 식사에서 살펴볼 영양소면 표시), 먹는 방법
//   음식·이유·영양소는 data/tips.js의 foods (효능이 아니라 일반적인 식품 정보로만 쓴다)
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

const GUIDE = Object.fromEntries(NUTRIENT_GUIDE.map((n) => [n.key, n]))
const art = (f) => FILE[f.label] && `food_${FILE[f.label]}`

function FoodSheet({ f, watchKeys, onClose }) {
  const nutrients = (f.nutrients ?? []).map((k) => GUIDE[k]).filter(Boolean)
  return (
    <BottomSheet
      title={
        <>
          <Illust name={art(f)} emoji={f.emoji} className="size-7" emojiClass="text-xl" />
          {f.label}
        </>
      }
      onClose={onClose}
    >
      <dl className="space-y-2 text-sm leading-relaxed">
        {f.reason && (
          <div className="rounded-card bg-cream px-4 py-3">
            <dt className="font-bold">왜 골랐나요</dt>
            <dd className="mt-0.5 text-ink-soft">{f.reason}</dd>
          </div>
        )}
        {nutrients.length > 0 && (
          <div className="rounded-card bg-cream px-4 py-3">
            <dt className="font-bold">이런 영양소가 들어 있어요</dt>
            <dd className="mt-2">
              <ul className="flex flex-wrap gap-1.5">
                {nutrients.map((n) => {
                  const mine = watchKeys.includes(n.key)
                  return (
                    <li
                      key={n.key}
                      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${mine ? 'bg-primary-soft text-primary-shade' : 'bg-white'}`}
                    >
                      <NutrientArt n={n} className="size-5" />
                      {n.label}
                      {mine && <span className="font-normal">· 살펴볼 영양소</span>}
                    </li>
                  )
                })}
              </ul>
            </dd>
          </div>
        )}
        {f.why && (
          <div className="rounded-card bg-cream px-4 py-3">
            <dt className="font-bold">이렇게 먹어 보세요</dt>
            <dd className="mt-0.5 text-ink-soft">{f.why}</dd>
          </div>
        )}
      </dl>
    </BottomSheet>
  )
}

export default function FoodGrid({ foods, watchKeys = [] }) {
  const [open, setOpen] = useState(null)
  return (
    <>
      <ul className="grid grid-cols-3 gap-2.5">
        {foods.map((f) => (
          <li key={f.label}>
            <button
              type="button"
              onClick={() => setOpen(f)}
              aria-label={`${f.label} 왜 좋은지 보기`}
              className="flex h-full w-full flex-col items-center rounded-card bg-cream px-1 py-3 text-center active:scale-95"
            >
              <Illust name={art(f)} emoji={f.emoji} className="size-14" emojiClass="text-3xl" />
              <span className="mt-1.5 text-xs leading-tight font-bold whitespace-pre-line min-[375px]:text-sm">{LINES[f.label] ?? f.label}</span>
            </button>
          </li>
        ))}
      </ul>
      <p className="mt-2 text-center text-xs text-ink-faint">음식을 누르면 왜 좋은지 볼 수 있어요</p>
      {open && <FoodSheet f={open} watchKeys={watchKeys} onClose={() => setOpen(null)} />}
    </>
  )
}
