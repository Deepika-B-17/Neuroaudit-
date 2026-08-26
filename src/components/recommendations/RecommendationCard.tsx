import type { Recommendation } from '../../types/audit'
import { Card } from '../ui/Card'
import { cn } from '../../lib/cn'

function priorityBadgeClass(priority: string) {
  switch (priority.toUpperCase()) {
    case 'CRITICAL':
      return 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-200 dark:border-purple-900/40'
    case 'HIGH':
      return 'bg-risk-high/10 text-risk-high border border-red-200 dark:border-red-900/40'
    case 'MEDIUM':
      return 'bg-risk-medium/10 text-risk-medium border border-amber-200 dark:border-amber-900/40'
    case 'LOW':
      return 'bg-risk-low/10 text-risk-low border border-emerald-200 dark:border-emerald-900/40'
    default:
      return 'bg-muted/10 text-muted border border-border'
  }
}

export function RecommendationCard({ item }: { item: Recommendation }) {
  const priority = item.priority || 'MEDIUM'
  const whyText = item.why || item.reason
  const actionText = item.action || item.control

  return (
    <Card className="p-6">
      {/* Header: Number, Dimension, and Priority */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold tracking-[0.16em] text-muted">{item.number}</span>
          {item.risk_dimension && (
            <span className="rounded bg-surface px-2 py-0.5 text-[10px] font-semibold tracking-wider uppercase text-muted border border-border">
              {item.risk_dimension}
            </span>
          )}
        </div>
        <span
          className={cn(
            'rounded-md px-2.5 py-0.5 text-[11px] font-semibold tracking-[0.12em] uppercase',
            priorityBadgeClass(priority),
          )}
        >
          {priority} Priority
        </span>
      </div>

      {/* Title */}
      <h3 className="mt-3 text-lg font-semibold tracking-tight text-foreground">{item.title}</h3>

      {/* Threat Scenario (if available) */}
      {item.threat && (
        <div className="mt-3.5 rounded-md bg-surface/60 p-3 border border-border/60">
          <p className="text-[11px] font-semibold tracking-[0.12em] uppercase text-muted">Threat Scenario</p>
          <p className="mt-1 text-xs leading-relaxed text-foreground">{item.threat}</p>
        </div>
      )}

      {/* Supporting Evidence (if available) */}
      {item.evidence && item.evidence.length > 0 && (
        <div className="mt-4">
          <p className="text-[11px] font-semibold tracking-[0.12em] uppercase text-muted">Supporting Evidence</p>
          <ul className="mt-1.5 space-y-1">
            {item.evidence.map((ev, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-muted">
                <span className="text-accent">•</span>
                <span>{ev}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Finding / Why it matters */}
      {whyText && (
        <div className="mt-4">
          <p className="text-[11px] font-semibold tracking-[0.12em] uppercase text-muted">Why it matters</p>
          <p className="mt-1 text-sm leading-relaxed text-muted">{whyText}</p>
        </div>
      )}

      {/* Recommended Action */}
      {actionText && (
        <div className="mt-4">
          <p className="text-[11px] font-semibold tracking-[0.12em] uppercase text-muted">Recommended action</p>
          <p className="mt-1 text-sm leading-relaxed font-medium text-foreground">{actionText}</p>
        </div>
      )}

      {/* Concrete Implementation Steps (if available) */}
      {item.implementation && item.implementation.length > 0 && (
        <div className="mt-4">
          <p className="text-[11px] font-semibold tracking-[0.12em] uppercase text-muted">Implementation Steps</p>
          <ol className="mt-2 space-y-1.5">
            {item.implementation.map((step, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-foreground/90">
                <span className="font-semibold text-accent">{idx + 1}.</span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Expected Impact & Residual Risk Footer */}
      {(item.expected_impact || item.residual_risk || item.evidence_status) && (
        <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-border pt-4 text-[11px] text-muted">
          {item.expected_impact && (
            <span>
              <strong className="text-foreground">Expected Impact:</strong>{' '}
              <span className="font-medium text-accent">{item.expected_impact}</span>
            </span>
          )}
          {item.residual_risk && (
            <span>
              <strong className="text-foreground">Residual Risk:</strong>{' '}
              <span className="font-medium">{item.residual_risk}</span>
            </span>
          )}
          {item.evidence_status && (
            <span className="rounded bg-surface px-1.5 py-0.5 text-[10px] text-muted border border-border">
              {item.evidence_status}
            </span>
          )}
        </div>
      )}
    </Card>
  )
}
