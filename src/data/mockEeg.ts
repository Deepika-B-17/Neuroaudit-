export const EEG_CHANNELS = ['FP1', 'FP2', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4', 'O1', 'O2'] as const

export type EegChannel = (typeof EEG_CHANNELS)[number]

const CHANNEL_PROFILES: Record<EegChannel, { a: number; b: number; c: number; phase: number }> = {
  FP1: { a: 0.9, b: 0.35, c: 0.18, phase: 0.2 },
  FP2: { a: 0.85, b: 0.32, c: 0.2, phase: 0.6 },
  F3: { a: 0.7, b: 0.45, c: 0.15, phase: 1.1 },
  F4: { a: 0.72, b: 0.4, c: 0.16, phase: 1.4 },
  C3: { a: 0.55, b: 0.5, c: 0.22, phase: 0.4 },
  C4: { a: 0.58, b: 0.48, c: 0.2, phase: 0.9 },
  P3: { a: 0.62, b: 0.38, c: 0.28, phase: 1.8 },
  P4: { a: 0.6, b: 0.36, c: 0.26, phase: 2.1 },
  O1: { a: 0.48, b: 0.55, c: 0.12, phase: 0.3 },
  O2: { a: 0.5, b: 0.52, c: 0.14, phase: 0.7 },
}

export function sampleChannel(
  channel: EegChannel,
  t: number,
  timeOffset = 0,
) {
  const p = CHANNEL_PROFILES[channel]
  const x = t + timeOffset
  return (
    p.a * Math.sin(2.1 * x + p.phase) +
    p.b * Math.sin(5.4 * x + p.phase * 1.7) +
    p.c * Math.sin(11.2 * x + p.phase * 0.5) +
    0.08 * Math.sin(0.35 * x)
  )
}

export function buildChannelSeries(
  channel: EegChannel,
  points: number,
  timeOffset = 0,
) {
  const values: number[] = []
  for (let i = 0; i < points; i += 1) {
    const t = (i / points) * Math.PI * 2
    values.push(sampleChannel(channel, t, timeOffset))
  }
  return values
}

export function seriesToPath(
  values: number[],
  width: number,
  height: number,
  yOffset: number,
) {
  if (values.length === 0) return ''
  const max = Math.max(...values.map((v) => Math.abs(v)), 0.001)
  const step = width / Math.max(values.length - 1, 1)
  return values
    .map((v, i) => {
      const x = i * step
      const y = yOffset + (v / max) * (height * 0.38)
      return `${i === 0 ? 'M' : 'L'} ${x.toFixed(2)} ${y.toFixed(2)}`
    })
    .join(' ')
}
