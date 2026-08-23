import { Menu } from 'lucide-react'
import { useAudit } from '../../context/AuditSessionContext'
import { RiskLevelBadge } from '../ui/Badge'

export function AppTopBar({ onMenu }: { onMenu: () => void }) {
  const audit = useAudit()

  return (
    <header className="no-print flex h-14 items-center justify-between gap-4 border-b border-border bg-surface px-4 lg:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          className="rounded-na border border-border p-2 text-muted lg:hidden"
          onClick={onMenu}
          aria-label="Open navigation"
        >
          <Menu size={18} />
        </button>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">{audit.auditName}</p>
          <p className="truncate text-xs text-muted">
            {audit.fileName} · {audit.analysisDate}
          </p>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="hidden text-xs text-muted sm:inline">Status</span>
        <span className="rounded-md bg-accent-soft px-2 py-0.5 text-[11px] font-semibold tracking-wide text-foreground">
          {audit.status}
        </span>
        <RiskLevelBadge level={audit.riskLevel} />
        <div
          className="hidden h-8 w-8 items-center justify-center rounded-full border border-border text-[11px] font-semibold text-muted sm:flex"
          aria-hidden
        >
          NA
        </div>
      </div>
    </header>
  )
}
