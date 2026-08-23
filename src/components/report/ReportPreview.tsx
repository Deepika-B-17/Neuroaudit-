import { RiskScore } from '../risk/RiskScore'
import { RiskBreakdown } from '../risk/RiskBreakdown'
import { Wordmark } from '../ui/Wordmark'
import { useAudit } from '../../context/AuditSessionContext'

export function ReportPreview() {
  const audit = useAudit()

  return (
    <article className="mx-auto max-w-3xl rounded-na border border-border bg-card px-8 py-10 shadow-elevated md:px-12">
      <header className="border-b border-border pb-8">
        <Wordmark />
        <p className="mt-4 text-xs font-semibold tracking-[0.18em] uppercase text-muted">
          Neural Data Privacy Risk Assessment
        </p>
        <dl className="mt-6 grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted">Audit</dt>
            <dd className="font-medium">{audit.auditName}</dd>
          </div>
          <div>
            <dt className="text-muted">EEG File</dt>
            <dd className="font-medium">{audit.fileName}</dd>
          </div>
          <div>
            <dt className="text-muted">Analysis Date</dt>
            <dd className="font-medium">{audit.analysisDate}</dd>
          </div>
          <div>
            <dt className="text-muted">Status</dt>
            <dd className="font-medium">{audit.status}</dd>
          </div>
        </dl>
      </header>

      <section className="border-b border-border py-8">
        <h2 className="text-sm font-semibold tracking-[0.14em] uppercase text-muted">Executive Summary</h2>
        <div className="mt-5 flex flex-col items-start gap-6 sm:flex-row sm:items-center">
          <RiskScore score={audit.overallRisk} level={audit.riskLevel} size={160} />
          <div>
            <p className="text-xs font-semibold tracking-[0.14em] uppercase text-muted">Overall Privacy Risk</p>
            <p className="mt-1 text-2xl font-bold">
              {audit.overallRisk} / 100
            </p>
            <p className="mt-3 text-sm leading-relaxed text-muted">{audit.executiveSummary}</p>
          </div>
        </div>
      </section>

      <section className="border-b border-border py-8">
        <h2 className="text-sm font-semibold tracking-[0.14em] uppercase text-muted">Risk Breakdown</h2>
        <div className="mt-5">
          <RiskBreakdown dimensions={audit.dimensions} />
        </div>
      </section>

      <section className="border-b border-border py-8">
        <h2 className="text-sm font-semibold tracking-[0.14em] uppercase text-muted">Potential Privacy Exposure</h2>
        <ul className="mt-4 space-y-3">
          {audit.keyFindings.map((finding) => (
            <li key={finding} className="text-sm leading-relaxed text-foreground">
              {finding}
            </li>
          ))}
        </ul>
      </section>

      <section className="border-b border-border py-8">
        <h2 className="text-sm font-semibold tracking-[0.14em] uppercase text-muted">Security Recommendations</h2>
        <ol className="mt-4 space-y-4">
          {audit.recommendations.slice(0, 4).map((item) => (
            <li key={item.id}>
              <p className="text-sm font-semibold">
                {item.number} {item.title}{' '}
                <span className="font-medium text-muted">({item.priority})</span>
              </p>
              <p className="mt-1 text-sm text-muted">{item.action}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="pt-8">
        <h2 className="text-sm font-semibold tracking-[0.14em] uppercase text-muted">Limitations</h2>
        <p className="mt-3 text-sm leading-relaxed text-muted">{audit.disclaimer}</p>
      </section>
    </article>
  )
}
