// 모바일 폭(최대 430px)으로 가운데 정렬. PC에서는 양옆이 body의 연한 배경으로 보인다.
export default function MobileFrame({ children }) {
  return (
    <div className="mx-auto flex min-h-dvh w-full max-w-app flex-col bg-cream min-[431px]:shadow-soft">
      {children}
    </div>
  )
}
