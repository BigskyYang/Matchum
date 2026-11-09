import { useEffect, useState } from 'react'

// 화면에서 나중에 불러오는 큰 자료 (첫 화면을 가볍게: 개인 결과·건강기능식품 화면에서만 받는다)
//   nutritionModels.json: 재준님 모델 (약 1.3MB), supplementCatalog.json: 준혁님 제품 목록 (약 3MB, 압축 약 260KB)
function useLazy(load) {
  const [data, setData] = useState(null)
  useEffect(() => {
    let alive = true
    load().then((m) => alive && setData(m.default))
    return () => {
      alive = false
    }
  }, [load])
  return data
}

const loadModels = () => import('../data/nutritionModels.json')
const loadCatalog = () => import('../data/supplementCatalog.json')

export const useModels = () => useLazy(loadModels)
export const useCatalog = () => useLazy(loadCatalog)
