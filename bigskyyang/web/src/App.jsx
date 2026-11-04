import { Navigate, Route, Routes } from 'react-router-dom'
import MobileFrame from './components/MobileFrame.jsx'
import PersonalResultPage from './pages/PersonalResultPage.jsx'
import ResultPage from './pages/ResultPage.jsx'
import StartPage from './pages/StartPage.jsx'
import SurveyPage from './pages/SurveyPage.jsx'
import { loadSurvey } from './lib/storage.js'

// 1단계: /survey → /result (유형 결과), 2단계: /survey2 → /result2 (개인 결과, 1단계를 마쳐야 들어갈 수 있다)
function Stage2Survey() {
  return loadSurvey().done[1] ? <SurveyPage key="stage2" stage={2} /> : <Navigate to="/survey" replace />
}

export default function App() {
  return (
    <MobileFrame>
      <Routes>
        <Route path="/" element={<StartPage />} />
        <Route path="/survey" element={<SurveyPage key="stage1" stage={1} />} />
        <Route path="/result" element={<ResultPage />} />
        <Route path="/survey2" element={<Stage2Survey />} />
        <Route path="/result2" element={<PersonalResultPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </MobileFrame>
  )
}
