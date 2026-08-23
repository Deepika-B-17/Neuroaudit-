import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Sparkles, Activity } from 'lucide-react'
import { UploadZone } from '../components/upload/UploadZone'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { useAuditSession } from '../context/AuditSessionContext'
import { formatFileSize } from '../lib/cn'
import { fetchBenchmarkSamples } from '../api/auditApi'
import type { BenchmarkSample } from '../types/audit'

export function NewAudit() {
  const navigate = useNavigate()
  const {
    auditName,
    description,
    file,
    setAuditName,
    setDescription,
    setFile,
    setSampleId,
    resetScan,
  } = useAuditSession()

  const [samples, setSamples] = useState<BenchmarkSample[]>([])

  useEffect(() => {
    fetchBenchmarkSamples()
      .then((data) => setSamples(data))
      .catch(() => {
        // Fallback default samples if offline
        setSamples([
          {
            id: 'session_a_rest_eeg.edf',
            name: 'Clinical cohort session A',
            fileName: 'session_a_rest_eeg.edf',
            description: 'Resting-state baseline recording (8 channels, 30s) exhibiting individual alpha rhythm.',
            duration: '30s',
            profile: 'Resting Baseline',
          },
          {
            id: 'pilot_rest_02.edf',
            name: 'Pilot study — rest-state',
            fileName: 'pilot_rest_02.edf',
            description: 'High-arousal stress protocol (8 channels, 25s) with elevated beta activity.',
            duration: '25s',
            profile: 'Stress / Affective',
          },
          {
            id: 'dual_task_block3.edf',
            name: 'Workload dual-task trial',
            fileName: 'dual_task_block3.edf',
            description: 'Cognitive dual-task recording (8 channels, 35s) demonstrating theta surge.',
            duration: '35s',
            profile: 'Cognitive Workload',
          },
        ])
      })
  }, [])

  const handleSelectSample = (sample: BenchmarkSample) => {
    resetScan()
    setAuditName(sample.name)
    setDescription(sample.description)
    setSampleId(sample.id)
    setFile({
      name: sample.fileName,
      size: 1024 * 128, // approx 128 KB
      type: 'EDF',
    })
  }

  return (
    <div className="mx-auto max-w-3xl px-5 py-12">
      <p className="text-[11px] font-semibold tracking-[0.18em] uppercase text-muted">New audit</p>
      <h1 className="mt-2 text-3xl font-bold tracking-tight">Start a New Privacy Audit</h1>
      <p className="mt-3 max-w-xl text-sm leading-relaxed text-muted">
        Upload an EEG recording (.edf) or select a benchmark dataset to begin the neural-data privacy risk assessment.
      </p>

      <Card elevated className="mt-8 p-6">
        <h2 className="text-sm font-semibold">Audit information</h2>
        <div className="mt-4 grid gap-4">
          <label className="block text-sm">
            <span className="mb-1.5 block text-muted">Audit name</span>
            <input
              value={auditName}
              onChange={(e) => setAuditName(e.target.value)}
              placeholder="e.g. Clinical cohort session A"
              className="w-full rounded-na border border-border bg-background px-3 py-2.5 text-sm text-foreground"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1.5 block text-muted">Description (optional)</span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full resize-y rounded-na border border-border bg-background px-3 py-2.5 text-sm text-foreground"
              placeholder="Study context, protocol, or notes for this audit"
            />
          </label>
        </div>
      </Card>

      <div className="mt-6">
        {!file ? (
          <div>
            <UploadZone
              onFile={(selected) => {
                resetScan()
                setSampleId(null)
                setFile({
                  name: selected.name,
                  size: selected.size,
                  type: selected.type || selected.name.split('.').pop()?.toUpperCase() || 'EDF',
                  rawFile: selected,
                })
                if (!auditName || auditName === 'Clinical cohort session A') {
                  setAuditName(`Audit — ${selected.name.replace(/\.[^/.]+$/, '')}`)
                }
              }}
            />

            {samples.length > 0 && (
              <div className="mt-8">
                <div className="mb-3 flex items-center gap-2">
                  <Sparkles size={16} className="text-accent" />
                  <h3 className="text-xs font-semibold tracking-[0.14em] uppercase text-muted">
                    Or select a pre-loaded benchmark EEG dataset
                  </h3>
                </div>
                <div className="grid gap-3 sm:grid-cols-3">
                  {samples.map((sample) => (
                    <button
                      key={sample.id}
                      type="button"
                      onClick={() => handleSelectSample(sample)}
                      className="group flex flex-col justify-between rounded-na border border-border bg-card p-4 text-left transition-all hover:border-accent hover:shadow-sm"
                    >
                      <div>
                        <div className="flex items-center justify-between">
                          <span className="inline-flex items-center gap-1 rounded bg-accent-soft px-1.5 py-0.5 text-[10px] font-semibold text-accent">
                            <Activity size={12} /> {sample.profile}
                          </span>
                          <span className="text-[11px] text-muted">{sample.duration}</span>
                        </div>
                        <p className="mt-2 text-sm font-semibold text-foreground group-hover:text-accent">
                          {sample.name}
                        </p>
                        <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-muted">
                          {sample.description}
                        </p>
                      </div>
                      <p className="mt-3 text-[11px] font-medium text-accent">Use Sample →</p>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <Card elevated className="p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-start gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-na bg-accent-soft text-accent">
                  <FileText size={18} aria-hidden />
                </span>
                <div>
                  <p className="font-semibold">{file.name}</p>
                  <p className="mt-1 text-sm text-muted">
                    {formatFileSize(file.size)} · {file.type || 'EDF'} · Ready to analyze
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="danger"
                  onClick={() => {
                    setFile(null)
                    setSampleId(null)
                    resetScan()
                  }}
                >
                  Remove
                </Button>
                <Button
                  onClick={() => {
                    resetScan()
                    navigate('/audit/scan')
                  }}
                >
                  Analyze EEG →
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}
