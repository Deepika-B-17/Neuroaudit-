import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/cn'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  elevated?: boolean
}

export function Card({ className, children, elevated = false, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-na border border-border bg-card shadow-na',
        elevated && 'shadow-elevated',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}
