import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { riskColorVar } from '../../lib/risk'
import type { RiskDimension } from '../../types/audit'
import { RiskLevelBadge } from '../ui/Badge'

export function RiskBreakdown({ dimensions }: { dimensions: RiskDimension[] }) {
  const data = dimensions.map((d) => ({
    name: d.label,
    score: d.score,
    level: d.level,
    fill: riskColorVar(d.level),
  }))

  return (
    <div className="grid gap-5 md:grid-cols-[1fr_auto] md:items-center">
      <div className="h-[188px] min-w-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 12, left: 8, bottom: 0 }}>
            <XAxis type="number" domain={[0, 100]} tick={{ fill: 'var(--na-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis
              type="category"
              dataKey="name"
              width={108}
              tick={{ fill: 'var(--na-text)', fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: 'var(--na-accent-soft)' }}
              content={({ payload }) => {
                const item = payload?.[0]?.payload as (typeof data)[number] | undefined
                if (!item) return null
                return (
                  <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-na">
                    <p className="font-semibold text-foreground">{item.name}</p>
                    <p className="text-muted">
                      {item.score} / 100 · {item.level}
                    </p>
                  </div>
                )
              }}
            />
            <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={14}>
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ul className="grid grid-cols-2 gap-3 md:w-40 md:grid-cols-1">
        {dimensions.map((d) => (
          <li key={d.key} className="flex items-center justify-between gap-3">
            <span className="text-sm text-muted">{d.score}</span>
            <RiskLevelBadge level={d.level} />
          </li>
        ))}
      </ul>
    </div>
  )
}
