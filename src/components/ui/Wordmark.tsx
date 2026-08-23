import { cn } from '../../lib/cn'

function BrandMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" aria-hidden>
      <path d="M6.5 19.5V4.5" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
      <path d="M17.5 4.5v15" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
      <path
        d="M6.5 4.5h1.6l1.5 5.2 1.5-5.2h1.4l1.6 8.4 1.4-5.2H17.5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export function Wordmark({ className, compact = false }: { className?: string; compact?: boolean }) {
  return (
    <span className={cn('inline-flex items-center gap-2.5', className)}>
      <span
        className="flex h-8 w-8 items-center justify-center rounded-md bg-accent-soft text-accent"
        aria-hidden
      >
        <BrandMark className="h-[18px] w-[18px]" />
      </span>
      {!compact && (
        <span className="text-[13px] font-extrabold tracking-[0.18em] text-foreground">
          NEUROAUDIT
        </span>
      )}
    </span>
  )
}
