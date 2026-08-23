import { useState } from 'react'
import { Download, Printer, Share2 } from 'lucide-react'
import { ReportPreview } from '../components/report/ReportPreview'
import { Button } from '../components/ui/Button'
import { useToast } from '../components/ui/Toast'
import { useAudit } from '../context/AuditSessionContext'
import { downloadReportPdf } from '../api/auditApi'

export function Report() {
  const { notify } = useToast()
  const audit = useAudit()
  const [downloading, setDownloading] = useState(false)

  const handleDownloadPdf = async () => {
    setDownloading(true)
    try {
      const sessionId = audit.session_id || 'session_a_rest_eeg.edf'
      await downloadReportPdf(sessionId, audit.fileName)
      notify('PDF audit report generated and downloaded successfully.')
    } catch (err: any) {
      notify(`PDF generation failed: ${err.message || 'Server error'}`)
    } finally {
      setDownloading(false)
    }
  }

  const handleShare = async () => {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(
        `NeuroAudit Report: ${audit.auditName} (${audit.overallRisk}/100 - ${audit.riskLevel} Risk)\n` +
        `Summary: ${audit.executiveSummary}`,
      )
      notify('Audit summary copied to clipboard!')
    } else {
      notify('Sharing: Audit record is available in local database.')
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Privacy Risk Assessment Report</h1>
          <p className="mt-1 text-sm text-muted">
            Official neural data privacy assessment report for {audit.auditName}.
          </p>
        </div>
        <div className="no-print flex flex-wrap gap-2">
          <Button
            onClick={handleDownloadPdf}
            disabled={downloading}
            className="inline-flex items-center gap-2"
          >
            <Download size={16} />
            {downloading ? 'Generating PDF...' : 'Download PDF Report'}
          </Button>
          <Button
            variant="secondary"
            onClick={() => {
              window.print()
            }}
            className="inline-flex items-center gap-2"
          >
            <Printer size={16} />
            Print Report
          </Button>
          <Button
            variant="secondary"
            onClick={handleShare}
            className="inline-flex items-center gap-2"
          >
            <Share2 size={16} />
            Share Summary
          </Button>
        </div>
      </div>
      <ReportPreview />
    </div>
  )
}
