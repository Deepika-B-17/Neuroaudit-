import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { MOCK_AUDIT } from '../data/mockAudit'
import type { AuditRecord, RecentAudit, UploadedFileMeta } from '../types/audit'
import { fetchRecentAudits, loadBenchmarkSample, uploadEEGFile } from '../api/auditApi'

interface AuditSessionContextValue {
  auditName: string
  description: string
  file: UploadedFileMeta | null
  sampleId: string | null
  scanComplete: boolean
  isAnalyzing: boolean
  scanError: string | null
  analysisDate: string
  auditRecord: AuditRecord | null
  recentAuditsList: RecentAudit[]
  setAuditName: (value: string) => void
  setDescription: (value: string) => void
  setFile: (file: UploadedFileMeta | null) => void
  setSampleId: (id: string | null) => void
  setAuditRecord: (record: AuditRecord | null) => void
  completeScan: () => void
  resetScan: () => void
  runAnalysis: () => Promise<AuditRecord>
  refreshRecentAudits: () => Promise<void>
}

const AuditSessionContext = createContext<AuditSessionContextValue | null>(null)

function formatToday() {
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date())
}

export function AuditSessionProvider({ children }: { children: ReactNode }) {
  const [auditName, setAuditName] = useState('Clinical cohort session A')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState<UploadedFileMeta | null>(null)
  const [sampleId, setSampleId] = useState<string | null>(null)
  const [scanComplete, setScanComplete] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)
  const [analysisDate, setAnalysisDate] = useState(MOCK_AUDIT.analysisDate)
  const [auditRecord, setAuditRecord] = useState<AuditRecord | null>(null)
  const [recentAuditsList, setRecentAuditsList] = useState<RecentAudit[]>(MOCK_AUDIT.recentAudits)

  const refreshRecentAudits = useCallback(async () => {
    try {
      const audits = await fetchRecentAudits()
      if (audits && audits.length > 0) {
        setRecentAuditsList(audits)
      }
    } catch {
      // Fallback to initial mock audits
    }
  }, [])

  useEffect(() => {
    refreshRecentAudits()
  }, [refreshRecentAudits])

  const completeScan = useCallback(() => {
    setScanComplete(true)
    setAnalysisDate(formatToday())
  }, [])

  const resetScan = useCallback(() => {
    setScanComplete(false)
    setScanError(null)
    setIsAnalyzing(false)
  }, [])

  const runAnalysis = useCallback(async (): Promise<AuditRecord> => {
    setIsAnalyzing(true)
    setScanError(null)
    try {
      let record: AuditRecord

      if (file?.rawFile) {
        // Upload actual user EEG file
        record = await uploadEEGFile(file.rawFile, auditName || file.name, description)
      } else if (sampleId) {
        // Load benchmark sample
        record = await loadBenchmarkSample(sampleId, auditName, description)
      } else if (file?.name) {
        // Use sample or file name
        record = await loadBenchmarkSample(file.name, auditName, description).catch(async () => {
          // If sample file not matched, load default benchmark
          return await loadBenchmarkSample('session_a_rest_eeg.edf', auditName, description)
        })
      } else {
        record = await loadBenchmarkSample('session_a_rest_eeg.edf', auditName, description)
      }

      setAuditRecord(record)
      setAnalysisDate(record.analysisDate || formatToday())
      setScanComplete(true)
      setIsAnalyzing(false)
      refreshRecentAudits()
      return record
    } catch (err: any) {
      const message = err?.message || 'Failed to complete EEG privacy analysis'
      setScanError(message)
      setIsAnalyzing(false)
      throw err
    }
  }, [file, sampleId, auditName, description, refreshRecentAudits])

  const value = useMemo(
    () => ({
      auditName,
      description,
      file,
      sampleId,
      scanComplete,
      isAnalyzing,
      scanError,
      analysisDate,
      auditRecord,
      recentAuditsList,
      setAuditName,
      setDescription,
      setFile,
      setSampleId,
      setAuditRecord,
      completeScan,
      resetScan,
      runAnalysis,
      refreshRecentAudits,
    }),
    [
      auditName,
      description,
      file,
      sampleId,
      scanComplete,
      isAnalyzing,
      scanError,
      analysisDate,
      auditRecord,
      recentAuditsList,
      completeScan,
      resetScan,
      runAnalysis,
      refreshRecentAudits,
    ],
  )

  return <AuditSessionContext.Provider value={value}>{children}</AuditSessionContext.Provider>
}

export function useAuditSession() {
  const ctx = useContext(AuditSessionContext)
  if (!ctx) throw new Error('useAuditSession must be used within AuditSessionProvider')
  return ctx
}

/** Returns the active audit record with session overlay and recent audits fallback */
export function useAudit(): AuditRecord & { description: string } {
  const session = useAuditSession()
  const base = session.auditRecord || MOCK_AUDIT

  return {
    ...base,
    auditName: session.auditName.trim() || base.auditName,
    fileName: session.file?.name || base.fileName,
    analysisDate: session.scanComplete ? session.analysisDate : base.analysisDate,
    description: session.description || base.description || '',
    recentAudits: session.recentAuditsList.length > 0 ? session.recentAuditsList : base.recentAudits,
  }
}
