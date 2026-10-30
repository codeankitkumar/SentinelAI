import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, authError } from '../api/client'
import { SeverityBadge, StatusBadge, Spinner, ErrorBanner, formatTime } from '../components/ui'

const STATUS_OPTIONS = ['open', 'investigating', 'resolved', 'closed']
const SEV_OPTIONS = ['critical', 'high', 'medium', 'low']

export default function IncidentDetail() {
  const { id } = useParams()
  const [incident, setIncident] = useState(null)
  const [error, setError] = useState('')
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [pdfBusy, setPdfBusy] = useState(false)

  function load() {
    setError('')
    api
      .get(`/incidents/${id}`)
      .then((res) => setIncident(res.data))
      .catch((err) => setError(authError(err)))
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  async function update(payload) {
    const res = await api.patch(`/incidents/${id}`, payload)
    setIncident(res.data)
  }

  async function addNote(e) {
    e.preventDefault()
    if (!note.trim()) return
    setBusy(true)
    try {
      await api.post(`/incidents/${id}/notes`, { content: note.trim() })
      setNote('')
      load()
    } catch (err) {
      setError(authError(err))
    } finally {
      setBusy(false)
    }
  }

  async function exportPdf() {
    setPdfBusy(true)
    try {
      const token = localStorage.getItem('sentinel_token')
      const res = await api.get(`/incidents/${id}/export`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `incident-${id}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError(authError(err))
    } finally {
      setPdfBusy(false)
    }
  }

  if (error) return <div className="space-y-4"><ErrorBanner message={error} /><Link to="/incidents" className="text-sm text-accent hover:underline">← Back to incidents</Link></div>

  if (!incident) {
    return (
      <div className="grid min-h-[50vh] place-items-center">
        <Spinner className="h-10 w-10" />
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <Link to="/incidents" className="text-sm text-accent hover:underline">← Incidents</Link>
        <div className="flex gap-2">
          <button className="btn-ghost" onClick={exportPdf} disabled={pdfBusy}>
            {pdfBusy ? 'Exporting…' : 'Export PDF'}
          </button>
        </div>
      </div>

      <div className="card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs text-slate-500">#{incident.id}</span>
              <h1 className="text-xl font-bold text-slate-100">{incident.title}</h1>
            </div>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">{incident.description || 'No description.'}</p>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-slate-500">
              <SeverityBadge severity={incident.severity} />
              <StatusBadge status={incident.status} />
              <span>Assigned to <b className="text-slate-300">{incident.assignee || 'unassigned'}</b></span>
              <span>Created {formatTime(incident.created_at)}</span>
            </div>
          </div>
        </div>

        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <div>
            <label className="label">Status</label>
            <select className="input" value={incident.status} onChange={(e) => update({ status: e.target.value })}>
              {STATUS_OPTIONS.map((s) => <option key={s} value={s} className="capitalize">{s.replace(/_/g, ' ')}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Severity</label>
            <select className="input" value={incident.severity} onChange={(e) => update({ severity: e.target.value })}>
              {SEV_OPTIONS.map((s) => <option key={s} value={s} className="capitalize">{s}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 text-sm font-semibold text-slate-200">Linked Alerts ({incident.alerts?.length || 0})</h3>
          {(!incident.alerts || incident.alerts.length === 0) && <p className="text-sm text-slate-500">No linked alerts.</p>}
          <ul className="space-y-2">
            {(incident.alerts || []).map((a) => (
              <li key={a.id} className="flex items-center justify-between gap-3 rounded-lg border border-slate-800/60 bg-panel2/40 px-3 py-2">
                <div className="min-w-0">
                  <div className="truncate text-sm text-slate-200">{a.title}</div>
                  <div className="font-mono text-xs text-slate-500">{a.rule_name} · {a.source_ip || ''}</div>
                </div>
                <SeverityBadge severity={a.severity} />
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h3 className="mb-3 text-sm font-semibold text-slate-200">Investigation Notes</h3>
          <form onSubmit={addNote} className="mb-4 flex gap-2">
            <input className="input" placeholder="Add a note…" value={note} onChange={(e) => setNote(e.target.value)} />
            <button className="btn-primary shrink-0" disabled={busy || !note.trim()}>Add</button>
          </form>
          <div className="space-y-3">
            {(incident.notes || []).length === 0 && <p className="text-sm text-slate-500">No notes yet.</p>}
            {(incident.notes || []).map((n) => (
              <div key={n.id} className="rounded-lg border border-slate-800/60 bg-panel2/40 p-3">
                <div className="mb-1 flex items-center gap-2 text-xs text-slate-500">
                  <span className="font-medium text-slate-300">{n.author_name}</span>· {formatTime(n.created_at)}
                </div>
                <p className="whitespace-pre-wrap text-sm text-slate-300">{n.content}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}