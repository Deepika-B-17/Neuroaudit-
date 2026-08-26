import type { AuditRecord, BenchmarkSample, RecentAudit, Recommendation } from '../types/audit'

const API_BASE = '/api'

function extractApiErrorMessage(errorData: any, fallback: string): string {
  if (!errorData) return fallback
  if (errorData.error && typeof errorData.error === 'object') {
    return errorData.error.message || errorData.error.details || fallback
  }
  if (typeof errorData.error === 'string') {
    return errorData.error
  }
  return errorData.details || errorData.message || fallback
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`)
    return res.ok
  } catch {
    return false
  }
}

export async function uploadEEGFile(
  file: File,
  auditName: string,
  description: string = '',
): Promise<AuditRecord> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('auditName', auditName)
  formData.append('description', description)

  const res = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(extractApiErrorMessage(errorData, 'Failed to upload and analyze EEG file'))
  }

  return res.json()
}

export async function loadBenchmarkSample(
  sampleId: string,
  auditName: string,
  description: string = '',
): Promise<AuditRecord> {
  const res = await fetch(`${API_BASE}/samples/load`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sample_id: sampleId,
      auditName,
      description,
    }),
  })

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(extractApiErrorMessage(errorData, 'Failed to load benchmark sample'))
  }

  return res.json()
}

export async function fetchAuditAnalysis(sessionId: string): Promise<AuditRecord> {
  const res = await fetch(`${API_BASE}/analysis/${sessionId}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch audit analysis for session ${sessionId}`)
  }
  return res.json()
}

export async function fetchAuditRecommendations(sessionId: string): Promise<Recommendation[]> {
  const res = await fetch(`${API_BASE}/recommendations/${sessionId}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch recommendations for session ${sessionId}`)
  }
  const data = await res.json()
  return data.recommendations || []
}

export async function fetchRecentAudits(): Promise<RecentAudit[]> {
  const res = await fetch(`${API_BASE}/audits`)
  if (!res.ok) {
    throw new Error('Failed to fetch recent audits')
  }
  const data = await res.json()
  return (data.audits || []).map((row: any) => ({
    id: row.session_id || row.id,
    name: row.auditName,
    date: row.analysisDate || row.createdAt,
    fileName: row.fileName,
    risk: row.overallRisk,
    level: row.riskLevel,
    status: row.status || 'Complete',
  }))
}

export async function fetchBenchmarkSamples(): Promise<BenchmarkSample[]> {
  const res = await fetch(`${API_BASE}/samples`)
  if (!res.ok) {
    throw new Error('Failed to fetch benchmark samples')
  }
  const data = await res.json()
  return data.samples || []
}

export async function downloadReportPdf(sessionId: string, fileName?: string): Promise<void> {
  const res = await fetch(`${API_BASE}/report/${sessionId}/download`)
  if (!res.ok) {
    throw new Error('Failed to download PDF audit report')
  }

  const blob = await res.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = fileName ? `NeuroAudit_Report_${fileName.replace('.edf', '')}.pdf` : `NeuroAudit_Report_${sessionId}.pdf`
  document.body.appendChild(a)
  a.click()
  window.URL.revokeObjectURL(url)
  document.body.removeChild(a)
}
