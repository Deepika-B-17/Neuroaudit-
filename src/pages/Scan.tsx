import { useEffect, useRef } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'
import { EEGChart } from '../components/eeg/EEGChart'
import { ProgressStepper } from '../components/scan/ProgressStepper'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useAuditSession } from '../context/AuditSessionContext'
import { useScanProgress } from '../hooks/useScanProgress'
import { formatFileSize } from '../lib/cn'

export function Scan() {
  const navigate = useNavigate()
  const { file, completeScan, runAnalysis, scanError, resetScan } = useAuditSession()
  const { stepIndex, progress, complete, currentStage } = useScanProgress(Boolean(file))
  const startedRef = useRef(false)

  useEffect(() => {
    if (file && !startedRef.current) {
      startedRef.current = true
      runAnalysis().catch(() => {
        // Handled via scanError in context
      })
    }
  }, [file, runAnalysis])

  useEffect(() => {
    if (complete) completeScan()
  }, [complete, completeScan])

  if (!file) {
    return <Navigate to="/audit/new" replace />
  }

  return (
    <div className="mx-auto max-w-6xl px-5 py-10">
      <p className="text-[11px] font-semibold tracking-[0.18em] uppercase text-muted">Analysis</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight">Analyzing EEG Data</h1>
      <p className="mt-2 text-sm text-muted">
        Executing multi-task privacy risk pipeline for {file.name} ({formatFileSize(file.size)}).
      </p>

      {scanError && (
        <Card className="mt-6 border-red-300 bg-red-50 p-5 dark:border-red-900/50 dark:bg-red-950/20">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 text-red-600 dark:text-red-400" />
            <div>
              <p className="font-semibold text-red-900 dark:text-red-200">Analysis Error</p>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">{scanError}</p>
              <div className="mt-3 flex gap-3">
                <Button
                  variant="secondary"
                  onClick={() => {
                    resetScan()
                    navigate('/audit/new')
                  }}
                >
                  Return to New Audit
                </Button>
                <Button
                  onClick={() => {
                    resetScan()
                    startedRef.current = false
                    runAnalysis().catch(() => {})
                  }}
                >
                  Retry Analysis
                </Button>
              </div>
            </div>
          </div>
        </Card>
      )}

      <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
        <Card elevated className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs font-semibold tracking-[0.14em] uppercase text-muted">EEG Signal Stream</p>
            <p className="text-xs text-muted">{file.name}</p>
          </div>
          <EEGChart animated height={340} />
        </Card>

        <div className="space-y-6">
          <Card className="p-5">
            <p className="text-xs font-semibold tracking-[0.14em] uppercase text-muted">Status</p>
            <p className="mt-2 text-sm font-semibold">
              {scanError ? 'Analysis halted' : complete ? 'Analysis complete' : currentStage}
            </p>
            <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-border">
              <div
                className="h-full rounded-full bg-accent transition-[width] duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="mt-2 text-sm text-muted">
              {progress}% · {complete ? 'Complete' : 'AI pipeline processing signal'}
            </p>
          </Card>
          <Card className="p-5">
            <ProgressStepper stepIndex={stepIndex} complete={complete} />
          </Card>
          {complete && !scanError && (
            <div>
              <p className="mb-3 text-sm font-semibold">Analysis Complete</p>
              <Button className="w-full" onClick={() => navigate('/app/dashboard')}>
                View Privacy Dashboard →
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
