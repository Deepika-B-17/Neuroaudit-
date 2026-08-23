import { useEffect, useMemo, useState } from 'react'
import { EEG_CHANNELS, buildChannelSeries, seriesToPath, type EegChannel } from '../../data/mockEeg'
import { cn } from '../../lib/cn'

interface EEGChartProps {
  channels?: readonly string[] | readonly EegChannel[]
  customTraces?: Record<string, number[]>
  height?: number
  animated?: boolean
  className?: string
  showTimeAxis?: boolean
  compact?: boolean
}

export function EEGChart({
  channels = EEG_CHANNELS,
  customTraces,
  height = 360,
  animated = false,
  className,
  showTimeAxis = true,
  compact = false,
}: EEGChartProps) {
  const [offset, setOffset] = useState(0)
  const width = 920
  const labelWidth = compact ? 36 : 44
  const axisHeight = showTimeAxis ? 22 : 8
  const plotHeight = height - axisHeight
  const rowH = plotHeight / Math.max(channels.length, 1)

  useEffect(() => {
    if (!animated) return undefined
    let frame = 0
    const tick = () => {
      setOffset((o) => o + 0.018)
      frame = window.requestAnimationFrame(tick)
    }
    frame = window.requestAnimationFrame(tick)
    return () => window.cancelAnimationFrame(frame)
  }, [animated])

  const paths = useMemo(
    () =>
      channels.map((channel) => {
        let values: number[] = []
        if (customTraces && customTraces[channel]) {
          const rawValues = customTraces[channel]
          if (animated) {
            // Apply slight cyclic offset shift for animation
            const shift = Math.floor((offset * 20) % rawValues.length)
            values = [...rawValues.slice(shift), ...rawValues.slice(0, shift)]
          } else {
            values = rawValues
          }
        } else {
          values = buildChannelSeries(channel as EegChannel, compact ? 140 : 220, offset)
        }

        return {
          channel,
          d: seriesToPath(values, width, rowH, rowH / 2),
        }
      }),
    [channels, customTraces, compact, offset, rowH, animated],
  )

  return (
    <div className={cn('w-full overflow-hidden', className)}>
      <svg
        viewBox={`0 0 ${width + labelWidth} ${height}`}
        className="h-auto w-full"
        role="img"
        aria-label="EEG signal preview with channel traces"
      >
        <rect
          x={labelWidth}
          y={0}
          width={width}
          height={plotHeight}
          fill="transparent"
          stroke="var(--na-border)"
          strokeWidth="1"
        />
        {Array.from({ length: 8 }).map((_, i) => (
          <line
            key={`v-${i}`}
            x1={labelWidth + (width / 8) * i}
            x2={labelWidth + (width / 8) * i}
            y1={0}
            y2={plotHeight}
            stroke="var(--na-grid)"
            strokeWidth="1"
          />
        ))}
        {channels.map((channel, i) => (
          <g key={channel}>
            <line
              x1={labelWidth}
              x2={labelWidth + width}
              y1={rowH * i}
              y2={rowH * i}
              stroke="var(--na-grid)"
              strokeWidth="1"
            />
            <text
              x={labelWidth - 8}
              y={rowH * i + rowH / 2 + 3}
              textAnchor="end"
              fill="var(--na-muted)"
              fontSize={compact ? 9 : 10}
              fontFamily="Manrope, sans-serif"
            >
              {channel}
            </text>
            <g transform={`translate(${labelWidth}, ${rowH * i})`}>
              <path
                d={paths[i]?.d || ''}
                fill="none"
                stroke="var(--na-eeg)"
                strokeWidth={compact ? 1 : 1.25}
                strokeLinecap="round"
                opacity={0.92}
              />
            </g>
          </g>
        ))}
        {showTimeAxis &&
          ['0 s', '2 s', '4 s', '6 s', '8 s'].map((label, i) => (
            <text
              key={label}
              x={labelWidth + (width / 4) * i}
              y={height - 4}
              fill="var(--na-muted)"
              fontSize="10"
              fontFamily="Manrope, sans-serif"
              textAnchor={i === 4 ? 'end' : 'middle'}
            >
              {label}
            </text>
          ))}
      </svg>
    </div>
  )
}
