import type { Recommendation } from '../../types/audit'
import { Card } from '../ui/Card'
import { cn } from '../../lib/cn'

export function RecommendationCard({ item }: { item: Recommendation }) {
  const high = item.priority === 'HIGH'
  return (
    <Card className="p-6">
      <div className="flex items-start justify-between gap-4">
        <p className="text-xs font-semibold tracking-[0.16em] text-muted">{item.number}</p>
        <span
          className={cn(
            'rounded-md px-2 py-0.5 text-[11px] font-semibold tracking-[0.12em]',
            high ? 'bg-risk-high/10 text-risk-high' : 'bg-risk-medium/10 text-risk-medium',
          )}
        >
          {item.priority}
        </span>
      </div>
      <h3 className="mt-3 text-lg font-semibold tracking-tight">{item.title}</h3>
      <p className="mt-4 text-[11px] font-semibold tracking-[0.12em] uppercase text-muted">Why it matters</p>
      <p className="mt-1.5 text-sm leading-relaxed text-muted">{item.why}</p>
      <p className="mt-4 text-[11px] font-semibold tracking-[0.12em] uppercase text-muted">Recommended action</p>
      <p className="mt-1.5 text-sm leading-relaxed text-foreground">{item.action}</p>
    </Card>
  )
}
