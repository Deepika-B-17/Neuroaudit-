import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { RiskScore } from '../components/risk/RiskScore'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { RiskLevelBadge } from '../components/ui/Badge'
import { EEGChart } from '../components/eeg/EEGChart'
import { useAudit } from '../context/AuditSessionContext'
import { cn } from '../lib/cn'
import type { RiskDimensionKey } from '../types/audit'

const preferredDimensionChannels: Record<RiskDimensionKey, readonly string[]> = {
  identity: ['FP1', 'FP2', 'O1', 'O2', 'CZ', 'PZ', 'F3', 'F4'],
  emotion: ['FP1', 'FP2', 'F3', 'F4', 'F7', 'F8', 'C3', 'C4'],
  stress: ['C3', 'C4', 'P3', 'P4', 'T3', 'T4', 'FP1', 'FP2'],
  workload: ['F3', 'F4', 'C3', 'C4', 'FZ', 'CZ', 'P3', 'P4'],
}

function resolveDimensionChannels(
  dimKey: RiskDimensionKey,
  availableChannels?: string[]
): string[] {
  const preferred = preferredDimensionChannels[dimKey] || ['FP1', 'FP2', 'F3', 'F4']
  if (!availableChannels || availableChannels.length === 0) {
    return [...preferred.slice(0, 4)]
  }
  const matched = preferred.filter((ch) => availableChannels.includes(ch))
  if (matched.length > 0) {
    return matched.slice(0, 4)
  }
  return availableChannels.slice(0, 4)
}

export function Assessment() {
  const navigate = useNavigate()
  const audit = useAudit()
  const [open, setOpen] = useState<string | null>(audit.dimensions[0]?.key ?? null)
  const availableChannels = audit.features?.preview_traces
    ? Object.keys(audit.features.preview_traces)
    : []

  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="text-2xl font-bold tracking-tight">Privacy Assessment</h1>
      <p className="mt-1 text-sm text-muted">
        Detailed analysis of potential privacy exposure across neural-data dimensions for {audit.fileName}.
      </p>

      <Card elevated className="mt-8 flex flex-col items-start gap-6 p-6 sm:flex-row sm:items-center">
        <RiskScore score={audit.overallRisk} level={audit.riskLevel} size={168} />
        <div>
          <p className="text-[11px] font-semibold tracking-[0.14em] uppercase text-muted">Overall Risk</p>
          <p className="mt-1 text-xl font-bold">
            {audit.overallRisk} / 100 · {audit.riskLevel}
          </p>
          <p className="mt-3 text-sm leading-relaxed text-muted">{audit.overallSummary}</p>
        </div>
      </Card>

      <div className="mt-6 space-y-4">
        {audit.dimensions.map((dim) => {
          const expanded = open === dim.key
          return (
            <Card key={dim.key} className="overflow-hidden">
              <button
                type="button"
                className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                onClick={() => setOpen(expanded ? null : dim.key)}
                aria-expanded={expanded}
              >
                <div>
                  <p className="text-[11px] font-semibold tracking-[0.14em] uppercase text-muted">{dim.label}</p>
                  <p className="mt-1 font-semibold">{dim.summary}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm font-semibold">{dim.score}</span>
                  <RiskLevelBadge level={dim.level} />
                  <ChevronDown className={cn('h-4 w-4 text-muted transition-transform', expanded && 'rotate-180')} />
                </div>
              </button>
              {expanded && (
                <div className="border-t border-border px-5 py-4">
                  <p className="text-sm leading-relaxed text-muted">{dim.explanation}</p>
                  <p className="mt-3 text-sm leading-relaxed text-foreground">
                    <span className="font-semibold">Potential privacy concern. </span>
                    {dim.concern}
                  </p>
                  <div className="mt-4">
                    <EEGChart
                      channels={resolveDimensionChannels(dim.key, availableChannels)}
                      customTraces={audit.features?.preview_traces}
                      height={120}
                      compact
                    />
                  </div>
                </div>
              )}
            </Card>
          )
        })}
      </div>

      <p className="mt-8 text-xs leading-relaxed text-muted">{audit.disclaimer}</p>

      <div className="mt-8">
        <Button onClick={() => navigate('/app/recommendations')}>View Recommendations →</Button>
      </div>
    </div>
  )
}
