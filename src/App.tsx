import { Navigate, Route, Routes } from 'react-router-dom'
import { MarketingLayout } from './layouts/MarketingLayout'
import { AppLayout } from './layouts/AppLayout'
import { Home } from './pages/Home'
import { NewAudit } from './pages/NewAudit'
import { Scan } from './pages/Scan'
import { Dashboard } from './pages/Dashboard'
import { Assessment } from './pages/Assessment'
import { Recommendations } from './pages/Recommendations'
import { Report } from './pages/Report'

export default function App() {
  return (
    <Routes>
      <Route element={<MarketingLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/audit/new" element={<NewAudit />} />
        <Route path="/audit/scan" element={<Scan />} />
      </Route>
      <Route element={<AppLayout />}>
        <Route path="/app/dashboard" element={<Dashboard />} />
        <Route path="/app/assessment" element={<Assessment />} />
        <Route path="/app/recommendations" element={<Recommendations />} />
        <Route path="/app/report" element={<Report />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
