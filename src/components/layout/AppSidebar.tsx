import { NavLink } from 'react-router-dom'
import {
  FilePlus2,
  Gauge,
  LayoutDashboard,
  ScrollText,
  ShieldCheck,
  ShieldEllipsis,
  X,
} from 'lucide-react'
import { Wordmark } from '../ui/Wordmark'
import { ThemeToggle } from '../ui/ThemeToggle'
import { cn } from '../../lib/cn'

const overview = [{ to: '/app/dashboard', label: 'Overview', icon: LayoutDashboard }]

const audit = [{ to: '/audit/new', label: 'New Audit', icon: FilePlus2 }]

const results = [
  { to: '/app/dashboard', label: 'Dashboard', icon: Gauge },
  { to: '/app/assessment', label: 'Privacy Assessment', icon: ShieldEllipsis },
  { to: '/app/recommendations', label: 'Recommendations', icon: ShieldCheck },
  { to: '/app/report', label: 'Report', icon: ScrollText },
]

function NavGroup({
  title,
  items,
  onNavigate,
}: {
  title: string
  items: { to: string; label: string; icon: typeof Gauge }[]
  onNavigate?: () => void
}) {
  return (
    <div className="mt-6">
      <p className="px-3 text-[10px] font-semibold tracking-[0.16em] uppercase text-muted">{title}</p>
      <ul className="mt-2 space-y-0.5">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <li key={item.label}>
              <NavLink
                to={item.to}
                end={item.to === '/app/dashboard' && title === 'Overview'}
                onClick={onNavigate}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-2.5 rounded-na px-3 py-2 text-sm transition-colors',
                    isActive
                      ? 'bg-accent-soft font-semibold text-foreground'
                      : 'text-muted hover:bg-accent-soft/60 hover:text-foreground',
                  )
                }
              >
                <Icon size={16} aria-hidden />
                {item.label}
              </NavLink>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export function AppSidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <>
      {open && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-background/60 lg:hidden"
          aria-label="Close navigation"
          onClick={onClose}
        />
      )}
      <aside
        className={cn(
          'no-print fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-border bg-surface px-3 py-4 transition-transform lg:static lg:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        )}
      >
        <div className="flex items-center justify-between px-2">
          <Wordmark />
          <button type="button" className="rounded-md p-1 text-muted lg:hidden" onClick={onClose} aria-label="Close sidebar">
            <X size={18} />
          </button>
        </div>
        <nav className="mt-4 flex-1 overflow-y-auto">
          <NavGroup title="Overview" items={overview} onNavigate={onClose} />
          <NavGroup title="Audit" items={audit} onNavigate={onClose} />
          <NavGroup title="Results" items={results} onNavigate={onClose} />
        </nav>
        <div className="border-t border-border px-2 pt-4">
          <ThemeToggle className="w-full justify-center" />
        </div>
      </aside>
    </>
  )
}
