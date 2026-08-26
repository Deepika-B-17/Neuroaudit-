export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH'

export type Priority = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

export type RiskDimensionKey = 'identity' | 'emotion' | 'stress' | 'workload'

export interface RiskContributor {
  feature: string
  raw_value: number
  normalized_value: number
  weight: number
  contribution: number
}

export interface RiskDimension {
  key: RiskDimensionKey
  label: string
  score: number
  level: RiskLevel
  summary: string
  explanation: string
  concern: string
  contributing_indicators?: string[]
  contributors?: RiskContributor[]
  model_type?: string
  quality_qualified?: boolean
}

export interface Recommendation {
  id: string
  number: string
  title: string
  priority: Priority
  severity?: RiskLevel | string
  risk_dimension?: string
  threat?: string
  evidence?: string[]
  why?: string
  reason?: string
  control?: string
  action?: string
  implementation?: string[]
  expected_impact?: string
  residual_risk?: string
  evidence_status?: string
}

export interface RecentAudit {
  id: string
  name: string
  date: string
  fileName: string
  risk: number
  level: RiskLevel
  status: string
}

export interface EEGSignalFeatures {
  global_band_powers?: {
    delta?: number
    theta?: number
    alpha?: number
    beta?: number
    gamma?: number
  }
  frontal_alpha_asymmetry?: number
  theta_beta_ratio?: number
  theta_alpha_ratio?: number
  engagement_index?: number
  iapf_hz?: number
  preview_traces?: Record<string, number[]>
  metadata?: {
    sfreq?: number
    n_channels?: number
    duration_sec?: number
    channel_names?: string[]
    file_size?: number
  }
  [key: string]: unknown
}

export interface AuditRecord {
  id?: string
  session_id?: string
  auditName: string
  fileName: string
  fileSize?: number
  description?: string
  analysisDate: string
  status: string
  overallRisk: number
  riskLevel: RiskLevel
  overallSummary: string
  executiveSummary: string
  keyFindings: string[]
  dimensions: RiskDimension[]
  recommendations: Recommendation[]
  recentAudits: RecentAudit[]
  disclaimer: string
  features?: EEGSignalFeatures
}

export interface UploadedFileMeta {
  name: string
  size: number
  type: string
  rawFile?: File
}

export interface BenchmarkSample {
  id: string
  name: string
  fileName: string
  description: string
  duration: string
  profile: string
}
