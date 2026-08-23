import { SCAN_STEPS } from '../../data/mockAudit'
import { cn } from '../../lib/cn'

export function ProgressStepper({ stepIndex, complete }: { stepIndex: number; complete: boolean }) {
  return (
    <ol className="space-y-3">
      {SCAN_STEPS.map((label, index) => {
        const done = complete || index < stepIndex
        const current = !complete && index === stepIndex
        return (
          <li key={label} className="flex items-start gap-3">
            <span
              className={cn(
                'mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] font-bold',
                done && 'border-accent bg-accent text-accent-foreground',
                current && 'border-accent text-accent',
                !done && !current && 'border-border text-muted',
              )}
              aria-hidden
            >
              {done ? '✓' : current ? '●' : '○'}
            </span>
            <span className={cn('text-sm', done || current ? 'text-foreground' : 'text-muted')}>{label}</span>
          </li>
        )
      })}
    </ol>
  )
}
