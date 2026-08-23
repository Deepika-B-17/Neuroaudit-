import { NavLink, useLocation } from 'react-router-dom'
import { Wordmark } from '../ui/Wordmark'
import { ThemeToggle } from '../ui/ThemeToggle'
import { Button } from '../ui/Button'
import { useNavigate } from 'react-router-dom'

export function MarketingNav() {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const home = pathname === '/'

  return (
    <header className="no-print sticky top-0 z-40 border-b border-border/80 bg-nav/90 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-5">
        <NavLink to="/" aria-label="NeuroAudit home">
          <Wordmark />
        </NavLink>
        <nav className="hidden items-center gap-6 text-sm md:flex">
          <NavLink
            to="/"
            className={({ isActive }) =>
              isActive ? 'font-semibold text-foreground' : 'text-muted hover:text-foreground'
            }
          >
            Home
          </NavLink>
          <a
            href={home ? '#how-it-works' : '/#how-it-works'}
            className="text-muted hover:text-foreground"
          >
            How It Works
          </a>
        </nav>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button onClick={() => navigate('/audit/new')}>
            Start Audit →
          </Button>
        </div>
      </div>
    </header>
  )
}
