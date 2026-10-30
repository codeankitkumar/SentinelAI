export function Spinner({ className = 'h-6 w-6' }) {
  return (
    <svg className={`animate-spin text-accent ${className}`} viewBox="0 0 24 24" fill="none">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
    </svg>
  )
}

export function Badge({ children, color }) {
  const map = {
    green: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
    amber: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
    red: 'bg-rose-500/15 text-rose-300 border-rose-500/40',
    sky: 'bg-sky-500/15 text-sky-300 border-sky-500/40',
    slate: 'bg-slate-500/15 text-slate-300 border-slate-500/40',
    violet: 'bg-violet-500/15 text-violet-300 border-violet-500/40',
  }
  const cls = map[color] || map.slate
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${cls}`}>
      {children}
    </span>
  )
}

// SeverityBadge picks a Tailwind color class statically so JIT keeps them.
const sevClass = {
  critical: 'bg-rose-500/20 text-rose-300 border-rose-500/50',
  high: 'bg-orange-500/20 text-orange-300 border-orange-500/50',
  medium: 'bg-amber-500/20 text-amber-300 border-amber-500/50',
  low: 'bg-sky-500/20 text-sky-300 border-sky-500/50',
  info: 'bg-slate-500/20 text-slate-300 border-slate-500/50',
}

export function SeverityBadge({ severity }) {
  const cls = sevClass[(severity || 'info').toLowerCase()] || sevClass.info
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-bold uppercase ${cls}`}>
      {severity}
    </span>
  )
}

const statusClass = {
  open: 'bg-red-500/15 text-red-300 border-red-500/40',
  acknowledged: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
  investigating: 'bg-sky-500/15 text-sky-300 border-sky-500/40',
  resolved: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40',
  closed: 'bg-slate-500/15 text-slate-300 border-slate-500/40',
  false_positive: 'bg-slate-500/15 text-slate-300 border-slate-500/40',
}

export function StatusBadge({ status }) {
  const cls = statusClass[(status || '').toLowerCase()] || statusClass.open
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium capitalize ${cls}`}>
      {String(status || '').replace(/_/g, ' ')}
    </span>
  )
}

export function EmptyState({ message }) {
  return (
    <div className="card text-center text-slate-400">
      <p className="text-sm">{message || 'Nothing to show yet.'}</p>
    </div>
  )
}

export function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div className="rounded-lg border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">
      {message}
    </div>
  )
}

export function Panel({ title, children, actions }) {
  return (
    <div className="card">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-200">{title}</h3>
        {actions}
      </div>
      {children}
    </div>
  )
}

export function formatTime(value) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  return d.toLocaleString(undefined, {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}