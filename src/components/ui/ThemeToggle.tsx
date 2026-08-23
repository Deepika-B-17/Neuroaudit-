import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'
import { cn } from '../../lib/cn'

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={cn(
        'inline-flex h-9 items-center gap-2 rounded-na border border-border px-2.5 text-xs font-medium text-muted transition-colors hover:bg-accent-soft hover:text-foreground',
        className,
      )}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {isDark ? <Sun size={14} aria-hidden /> : <Moon size={14} aria-hidden />}
      <span>{isDark ? 'Light' : 'Dark'}</span>
    </button>
  )
}
