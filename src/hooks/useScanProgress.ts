import { useEffect, useState } from 'react'
import { SCAN_STEPS } from '../data/mockAudit'

const STEP_MS = 1100

export function useScanProgress(active: boolean) {
  const [stepIndex, setStepIndex] = useState(0)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (!active) return undefined

    const stepTimer = window.setInterval(() => {
      setStepIndex((current) => {
        if (current >= SCAN_STEPS.length - 1) {
          window.clearInterval(stepTimer)
          return current
        }
        return current + 1
      })
    }, STEP_MS)

    const progressTimer = window.setInterval(() => {
      setProgress((current) => {
        if (current >= 100) {
          window.clearInterval(progressTimer)
          return 100
        }
        return Math.min(100, current + 4)
      })
    }, 280)

    return () => {
      window.clearInterval(stepTimer)
      window.clearInterval(progressTimer)
    }
  }, [active])

  const last = SCAN_STEPS.length - 1
  const complete = progress >= 100 && stepIndex >= last
  const currentStage = SCAN_STEPS[Math.min(stepIndex, last)]

  return { stepIndex, progress: complete ? 100 : progress, complete, currentStage }
}
