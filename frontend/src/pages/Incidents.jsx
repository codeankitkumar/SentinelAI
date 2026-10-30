import { useCallback, useEffect, useState } from 'react'
import { api, authError } from '../api/client'
import { SeverityBadge, StatusBadge, Spinner, ErrorBanner, EmptyState, formatTime } from '../components/ui'

const PAGE = 15
const STATUS_OPTIONS = ['open', 'investigating', 'resolved', 'closed']
const SEV_OPTIONS = ['critical', 'high', 'medium', 'low']

export default function Incidents() {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [severity, setSeverity] = useState('')
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ title: '', description: '', severity: 'medium' })
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    setLoading(true)
    setError('')
    api
      .get('/incidents', { params: { page, page_size: PAGE, severity: severity || undefined, status: status || undefined } })
      .then((res) => {
        setItems(res.data.items)
        setTotal(res.data.total)
      })
      .catch((err) => setError(authError(err)))
      .finally(() => setLoading(false))
  }, [page, severity, status])

  useEffect(() => {
    load()
  }, [load])

  async function createIncident(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await api.post('/incidents', form)
      setShowCreate(false)
      setForm({ title: '', description: '', severity: 'medium' })
      setPage(1)
      load()
    } catch (err) {
      setError(authError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-100">Incidents</h1>
        <button className="btn-primary" onClick={() => setShowCreate((v) => !v)}>
          {showCreate ? 'Close' : '+ New incident'}
        </button>
      </div>

      {showCreate && (
        <form onSubmit={createIncident} className="card space-y-3">
          <div>
            <label className="label">Title</label>
            <input className="input" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Describe the incident" />
          </div>
          <div>
            <label className="label">Severity</label>
            <select className="input" value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })}>
              {SEV_OPTIONS.map((s) => <option key={s} value={s} className="capitalize">{s}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Description</label>
            <textarea className="input min-h-20" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Summary of the investigation" />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setShowCreate(false)}>Cancel</button>
            <button className="btn-primary" disabled={busy || !form.title}>Create</button>
          </div>
        </form>
      )}

      <div className="flex flex-wrap gap-3">
        <select className="input w-auto" value={severity} onChange={(e) => { setSeverity(e.target.value); setPage(1) }}>
          <option value="">All severities</option>
          {SEV_OPTIONS.map((s) => <option key={s} value={s} className="capitalize">{s}</option>)}
        </select>
        <select className="input w-auto" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }}>
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => <option key={s} value={s} className="capitalize">{s.replace(/_/g, ' ')}</option>)}
        </select>
        <span className="self-center text-sm text-slate-500 tabular">{total} incidents</span>
      </div>

      <div className="card overflow-hidden p-0">
        {loading ? (
          <div className="grid place-items-center p-16"><Spinner /></div>
        ) : items.length === 0 ? (
          <div className="p-6"><EmptyState message="No incidents yet." /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-panel2 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">Severity</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Assignee</th>
                  <th className="px-4 py-3 text-right">Alerts</th>
                  <th className="px-4 py-3">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {items.map((i) => (
                  <tr key={i.id} className="cursor-pointer hover:bg-slate-800/30" onClick={() => { window.location.href = `/incidents/${i.id}` }}>
                    <td className="px-4 py-3 font-mono text-xs text-slate-400">#{i.id}</td>
                    <td className="max-w-md px-4 py-3">
                      <span className="font-medium text-slate-100 hover:text-accent">{i.title}</span>
                      <div className="truncate text-xs text-slate-500">{i.description}</div>
                    </td>
                    <td className="px-4 py-3"><SeverityBadge severity={i.severity} /></td>
                    <td className="px-4 py-3"><StatusBadge status={i.status} /></td>
                    <td className="px-4 py-3 text-xs text-slate-400">{i.assignee || '—'}</td>
                    <td className="px-4 py-3 text-right tabular text-slate-300">{i.alert_count}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-slate-500">{formatTime(i.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <button className="btn-ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</button>
        <span className="text-sm text-slate-500 tabular">Page {page} · {Math.max(1, Math.ceil(total / PAGE))}</span>
        <button className="btn-ghost" disabled={page * PAGE >= total} onClick={() => setPage((p) => p + 1)}>Next</button>
      </div>
    </div>
  )
}