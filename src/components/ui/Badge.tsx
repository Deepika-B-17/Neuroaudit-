import type { RiskLevel } from '../../types/audit'
import { cn } from '../../lib/cn'
import { riskBgClass, riskLevelLabel, riskTextClass } from '../../lib/risk'

export function RiskLevelBadge({ level, className }: { level: RiskLevel; className?: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold tracking-[0.12em] uppercase',
        riskBgClass(level),
        riskTextClass(level),
        className,
      )}
    >
      {riskLevelLabel(level)}
    </span>
  )
}
