import { useNavigate } from 'react-router-dom'
import { EEGChart } from '../components/eeg/EEGChart'
import { RiskBreakdown } from '../components/risk/RiskBreakdown'
import { RiskScore } from '../components/risk/RiskScore'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { RiskLevelBadge } from '../components/ui/Badge'
import { useAudit } from '../context/AuditSessionContext'

export function Dashboard() {
  const navigate = useNavigate()
  const audit = useAudit()

  return (
    <div className="mx-auto max-w-6xl">
      <h1 className="text-2xl font-bold tracking-tight">Privacy Risk Dashboard</h1>
      <p className="mt-1 text-sm text-muted">
        Overview of potential privacy exposure identified in the analyzed EEG data.
      </p>

      <div className="mt-8 grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)]">
        <Card elevated className="p-5">
          <p className="text-center text-[11px] font-semibold tracking-[0.14em] uppercase text-muted">
            Overall Privacy Risk
          </p>
          <div className="mt-3">
            <RiskScore score={audit.overallRisk} level={audit.riskLevel} />
          </div>
        </Card>
        <Card className="p-5">
          <p className="text-[11px] font-semibold tracking-[0.14em] uppercase text-muted">Risk breakdown</p>
          <div className="mt-4">
            <RiskBreakdown dimensions={audit.dimensions} />
          </div>
        </Card>
      </div>

      <Card elevated className="mt-5 p-5">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold tracking-[0.14em] uppercase text-muted">EEG Signal Preview</p>
          <p className="text-xs text-muted">{audit.fileName}</p>
        </div>
        <div className="mt-3">
          <EEGChart height={260} customTraces={audit.features?.preview_traces} />
        </div>
      </Card>

      <div className="mt-5 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <Card className="p-5">
          <h2 className="text-sm font-semibold">Key Findings</h2>
          <ul className="mt-4 space-y-3">
            {audit.keyFindings.map((finding) => (
              <li key={finding} className="text-sm leading-relaxed text-muted">
                {finding}
              </li>
            ))}
          </ul>
        </Card>
        <Card className="p-5">
          <h2 className="text-sm font-semibold">Recent audits</h2>
          <div className="mt-3 overflow-x-auto">
            <table className="w-full min-w-[320px] text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-muted">
                <tr>
                  <th className="pb-2 font-medium">Audit</th>
                  <th className="pb-2 font-medium">Date</th>
                  <th className="pb-2 font-medium">Risk</th>
                  <th className="pb-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {audit.recentAudits.map((row) => (
                  <tr key={row.id} className="border-t border-border">
                    <td className="py-2.5 pr-3">{row.name}</td>
                    <td className="py-2.5 pr-3 text-muted">{row.date}</td>
                    <td className="py-2.5 pr-3">
                      <span className="mr-2">{row.risk}</span>
                      <RiskLevelBadge level={row.level} />
                    </td>
                    <td className="py-2.5 text-muted">{row.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Button onClick={() => navigate('/app/assessment')}>View Assessment</Button>
        <Button variant="secondary" onClick={() => navigate('/app/recommendations')}>
          View Recommendations
        </Button>
        <Button variant="secondary" onClick={() => navigate('/app/report')}>
          View Report
        </Button>
      </div>
    </div>
  )
}
