import type { RiskLevel } from '../types/audit'

export function riskLevelFromScore(score: number): RiskLevel {
  if (score >= 70) return 'HIGH'
  if (score >= 40) return 'MEDIUM'
  return 'LOW'
}

export function riskLevelLabel(level: RiskLevel) {
  if (level === 'HIGH') return 'High'
  if (level === 'MEDIUM') return 'Medium'
  return 'Low'
}

export function riskColorVar(level: RiskLevel) {
  if (level === 'HIGH') return 'var(--na-risk-high)'
  if (level === 'MEDIUM') return 'var(--na-risk-medium)'
  return 'var(--na-risk-low)'
}

export function riskTextClass(level: RiskLevel) {
  if (level === 'HIGH') return 'text-risk-high'
  if (level === 'MEDIUM') return 'text-risk-medium'
  return 'text-risk-low'
}

export function riskBgClass(level: RiskLevel) {
  if (level === 'HIGH') return 'bg-risk-high/10'
  if (level === 'MEDIUM') return 'bg-risk-medium/10'
  return 'bg-risk-low/10'
}
