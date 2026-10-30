import { Navigate, Route, Routes } from 'react-router-dom'
import MobileFrame from './components/MobileFrame.jsx'
import StartPage from './pages/StartPage.jsx'
import SurveyPage from './pages/SurveyPage.jsx'

export default function App() {
  return (
    <MobileFrame>
      <Routes>
        <Route path="/" element={<StartPage />} />
        <Route path="/survey" element={<SurveyPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </MobileFrame>
  )
}
