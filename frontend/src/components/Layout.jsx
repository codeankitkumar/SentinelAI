import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../store/auth'

const nav = [
  { to: '/', label: 'Dashboard', icon: 'M3 12l9-9 9 9M5 10v10h5v-6h4v6h5V10' },
  { to: '/events', label: 'Flow Events', icon: 'M3 17l6-6 4 4 8-8M3 21h18' },
  { to: '/alerts', label: 'Alerts', icon: 'M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5a6 6 0 10-12 0v5l-2 2h16l-2-2z' },
  { to: '/incidents', label: 'Incidents', icon: 'M4 5h16v16H4zM4 9h16M9 1v4M15 1v4' },
  { to: '/assistant', label: 'AI Assistant', icon: 'M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z' },
]

function Icon({ d }) {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  )
}

export function Layout({ children }) {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()

  const onLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-slate-800 bg-panel md:flex">
        <div className="flex items-center gap-2 border-b border-slate-800 px-5 py-4">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-accent text-slate-900">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
              <path d="M12 2l2.4 4.6L19.5 8l-3.2 4.4.7 5.3L12 20.5l-5-2.8.7-5.3L4.5 8l5.1-1.4L12 2z" />
            </svg>
          </span>
          <div>
            <div className="text-sm font-bold tracking-tight text-slate-100">SentinelAI</div>
            <div className="text-[10px] uppercase tracking-widest text-slate-500">SOC Platform</div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-accent/10 text-accent'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-100'
                }`
              }
            >
              <Icon d={item.icon} />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-slate-800 px-4 py-4">
          <div className="flex items-center gap-3">
            <span className="grid h-9 w-9 place-items-center rounded-full bg-panel2 text-sm font-bold text-accent">
              {(user?.username || '?').slice(0, 2).toUpperCase()}
            </span>
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm font-medium text-slate-200">{user?.full_name || user?.username}</div>
              <div className="text-xs text-slate-500">{user?.role || 'analyst'}</div>
            </div>
            <button onClick={onLogout} title="Log out" className="text-slate-500 hover:text-rose-400">
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
          {isAdmin && (
            <div className="mt-2 inline-flex items-center gap-1 rounded-md bg-violet-500/15 px-1.5 py-0.5 text-[10px] font-medium text-violet-300">
              ADMIN
            </div>
          )}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-800 bg-surface/90 px-6 py-3 backdrop-blur md:hidden">
          <div className="flex items-center gap-2">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-accent text-slate-900">
              <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor">
                <path d="M12 2l2.4 4.6L19.5 8l-3.2 4.4.7 5.3L12 20.5l-5-2.8.7-5.3L4.5 8l5.1-1.4L12 2z" />
              </svg>
            </span>
            <span className="text-sm font-bold text-slate-100">SentinelAI</span>
          </div>
          <button onClick={onLogout} className="text-sm font-medium text-rose-400">Log out</button>
        </header>

        <main className="flex-1 px-4 py-6 md:px-8">{children}</main>
      </div>
    </div>
  )
}