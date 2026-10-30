import { useCallback, useEffect, useState } from 'react'
import { api, authError } from '../api/client'
import { SeverityBadge, Spinner, ErrorBanner, EmptyState, formatTime } from '../components/ui'

const PAGE = 15

export default function Alerts() {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [severity, setSeverity] = useState('')
  const [status, setStatus] = useState('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    setError('')
    api
      .get('/alerts', { params: { page, page_size: PAGE, severity: severity || undefined, status: status || undefined, query: query || undefined } })
      .then((res) => {
        setItems(res.data.items)
        setTotal(res.data.total)
      })
      .catch((err) => setError(authError(err)))
      .finally(() => setLoading(false))
  }, [page, severity, status, query])

  useEffect(() => {
    load()
  }, [load])

  async function triage(alertId) {
    const res = await api.patch(`/alerts/${alertId}`, { status: 'acknowledged' })
    setItems((prev) => prev.map((a) => (a.id === alertId ? res.data : a)))
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-100">Alerts</h1>
        <button className="btn-ghost" onClick={() => { setSeverity(''); setStatus(''); setQuery('') }}>
          Reset filters
        </button>
      </div>

      <div className="flex flex-wrap gap-3">
        <input className="input max-w-xs" placeholder="Search title, rule, description…" value={query} onChange={(e) => { setQuery(e.target.value); setPage(1) }} />
        <select className="input w-auto" value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1) }}>
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="info">Info</option>
        </select>
        <select className="input w-auto" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }}>
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="acknowledged">Acknowledged</option>
        </select>
        <span className="self-center text-sm text-slate-500 tabular">{total} alerts</span>
      </div>

      <ErrorBanner message={error} />

      <div className="card overflow-hidden p-0">
        {loading ? (
          <div className="grid place-items-center p-16"><Spinner /></div>
        ) : items.length === 0 ? (
          <div className="p-6"><EmptyState message="No alerts match the current filters." /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-panel2 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Alert</th>
                  <th className="px-4 py-3">Rule</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Severity</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {items.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-800/30">
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-400">{formatTime(a.timestamp)}</td>
                    <td className="max-w-xs px-4 py-3">
                      <div className="truncate font-medium text-slate-100">{a.title}</div>
                      <div className="truncate text-xs text-slate-500">{a.description}</div>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-400">{a.rule_name}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-300">{a.source_ip || '—'}</td>
                    <td className="px-4 py-3"><SeverityBadge severity={a.severity} /></td>
                    <td className="px-4 py-3 capitalize text-xs text-slate-400">{a.status}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-right">
                      {a.status === 'open' ? (
                        <div className="flex justify-end gap-2">
                          <button className="btn-ghost !py-1 !px-2 text-xs" onClick={() => triage(a.id)}>Acknowledge</button>
                          <button className="btn-primary !py-1 !px-2 text-xs" onClick={() => createIncident(a.id)}>Incident</button>
                        </div>
                      ) : (
                        <span className="text-xs text-slate-500">Triaged</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <button className="btn-ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
        <span className="text-sm text-slate-500 tabular">Page {page} · {Math.max(1, Math.ceil(total / PAGE))} total</span>
        <button className="btn-ghost" disabled={page * PAGE >= total} onClick={() => setPage((p) => p + 1)}>Next</button>
      </div>
    </div>
  )
}