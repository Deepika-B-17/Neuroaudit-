import { Outlet } from 'react-router-dom'
import { MarketingNav } from '../components/layout/MarketingNav'

export function MarketingLayout() {
  return (
    <div className="min-h-screen bg-background">
      <MarketingNav />
      <Outlet />
    </div>
  )
}
