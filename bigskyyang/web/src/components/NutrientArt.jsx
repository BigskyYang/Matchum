import Illust from './Illust.jsx'

// 영양소 그림 (public/illust/nutrient_{key}). 그림이 없는 영양소는 이모지(n.icon)
// n: { key, icon }
const FILE = { sodium_excess: 'sodium', vitamin_b: 'vitamin_b1' }

export default function NutrientArt({ n, className, emojiClass }) {
  return <Illust name={`nutrient_${FILE[n.key] ?? n.key}`} emoji={n.icon} className={className} emojiClass={emojiClass} />
}
