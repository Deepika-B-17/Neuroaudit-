import { riskColorVar, riskLevelLabel } from '../../lib/risk'
import type { RiskLevel } from '../../types/audit'

interface RiskScoreProps {
  score: number
  level: RiskLevel
  size?: number
}

export function RiskScore({ score, level, size = 188 }: RiskScoreProps) {
  const stroke = 11
  const inset = 8
  const radius = (size - stroke) / 2 - inset
  const circumference = 2 * Math.PI * radius
  const progress = Math.min(100, Math.max(0, score)) / 100
  const color = riskColorVar(level)
  const center = size / 2

  return (
    <div
      className="relative shrink-0"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Overall privacy risk ${score} out of 100, ${riskLevelLabel(level)}`}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="block">
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="var(--na-border)"
          strokeWidth={stroke}
        />
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - progress)}
          transform={`rotate(-90 ${center} ${center})`}
        />
      </svg>
      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <div className="flex items-end gap-0.5">
          <span className="text-4xl font-bold leading-none tracking-tight">{score}</span>
          <span className="mb-0.5 text-sm text-muted">/100</span>
        </div>
        <span
          className="mt-1.5 text-[11px] font-semibold tracking-[0.14em] uppercase"
          style={{ color }}
        >
          {riskLevelLabel(level)}
        </span>
      </div>
    </div>
  )
}
