import { useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { AppSidebar } from '../components/layout/AppSidebar'
import { AppTopBar } from '../components/layout/AppTopBar'
import { useAuditSession } from '../context/AuditSessionContext'

export function AppLayout() {
  const { scanComplete } = useAuditSession()
  const [open, setOpen] = useState(false)

  if (!scanComplete) {
    return <Navigate to="/audit/new" replace />
  }

  return (
    <div className="flex min-h-screen bg-background">
      <AppSidebar open={open} onClose={() => setOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <AppTopBar onMenu={() => setOpen(true)} />
        <main className="flex-1 px-4 py-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
