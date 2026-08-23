import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/cn'

type Variant = 'primary' | 'secondary' | 'tertiary' | 'danger'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  children: ReactNode
}

const variants: Record<Variant, string> = {
  primary:
    'bg-accent text-accent-foreground hover:brightness-110 disabled:hover:brightness-100',
  secondary:
    'border border-border bg-transparent text-foreground hover:bg-accent-soft',
  tertiary: 'bg-transparent text-muted hover:text-foreground',
  danger: 'border border-risk-high/40 text-risk-high hover:bg-risk-high/10',
}

export function Button({
  variant = 'primary',
  className,
  children,
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-na px-4 py-2.5 text-sm font-semibold tracking-tight transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-45',
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
