import { useCallback, useEffect, useState } from 'react'
import { api, authError } from '../api/client'
import { Spinner, ErrorBanner, Badge } from '../components/ui'
import { useAuth } from '../store/auth'

export default function Monitor() {
  const { isAdmin } = useAuth()
  const [capture, setCapture] = useState(null)
  const [summary, setSummary] = useState({ total_events: 0 })
  const [error, setError] = useState('')
  const [simBusy, setSimBusy] = useState(false)

  const load = useCallback(() => {
    setError('')
    api.get('/monitor/capture').then((res) => setCapture(res.data)).catch((err) => setError(authError(err)))
    api.get('/monitor/summary').then((res) => setSummary(res.data)).catch((err) => setError(authError(err)))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function simulate(e) {
    e.preventDefault()
    setSimBusy(true)
    setError('')
    try {
      const payload = {
        src_ip: e.target.src_ip.value,
        dst_ip: e.target.dst_ip.value,
        src_port: Number(e.target.src_port.value) || 0,
        dst_port: Number(e.target.dst_port.value) || 0,
        protocol: e.target.protocol.value,
        duration: Number(e.target.duration.value) || 0,
        packet_count: Number(e.target.packet_count.value) || 1,
        bytes_sent: Number(e.target.bytes_sent.value) || 0,
        bytes_recv: Number(e.target.bytes_recv.value) || 0,
      }
      const res = await api.post('/monitor/simulate', payload)
      setSummary((s) => ({ ...s, total_events: (s.total_events || 0) + 1, last_ingest: res.data }))
    } catch (err) {
      setError(authError(err))
    } finally {
      setSimBusy(false)
    }
  }

  async function startCapture() {
    setError('')
    try {
      const res = await api.post('/monitor/capture/start', {})
      setCapture({ ...capture, message: res.data.note || 'Capture started' })
    } catch (err) {
      setError(authError(err))
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-100">Network Monitor</h1>
        <p className="text-sm text-slate-500">Live capture configuration and synthetic flow simulation.</p>
      </div>

      <ErrorBanner message={error} />

      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-200">Capture status</h3>
            <p className="mt-1 text-xs text-slate-500">Interface: <code className="text-slate-300">{capture.interface || '—'}</code></p>
          </div>
          <Badge color={capture.enabled ? 'green' : 'amber'}>{capture.enabled ? 'Enabled' : 'Disabled (lab)'}</Badge>
        </div>
        <p className="mt-3 rounded-lg border border-slate-800/60 bg-panel2/40 p-3 text-xs text-slate-400">{capture.message}</p>
        {isAdmin && (
          <button className="btn-ghost mt-3" onClick={startCapture} disabled={!capture.enabled || !capture.available}>
            Start capture
          </button>
        )}
      </div>

      <div className="card">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">Database summary</h3>
          <span className="text-sm tabular text-slate-300">{summary.total_events.toLocaleString()} events</span>
        </div>
        {summary.last_ingest && (
          <p className="text-xs text-slate-500">
            Last ingest: event #{summary.last_ingest.event_id} — classified as <b className="text-slate-300">{summary.last_ingest.threat}</b>
          </p>
        )}
      </div>

      {isAdmin && (
        <form onSubmit={simulate} className="card space-y-4">
          <h3 className="text-sm font-semibold text-slate-200">Simulate synthetic flow</h3>
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="label">Source IP</label>
              <input name="src_ip" className="input" defaultValue="203.0.113.7" required />
            </div>
            <div>
              <label className="label">Destination IP</label>
              <input name="dst_ip" className="input" defaultValue="10.0.0.5" required />
            </div>
            <div>
              <label className="label">Source port</label>
              <input name="src_port" className="input" type="number" min="0" max="65535" defaultValue="59200" />
            </div>
            <div>
              <label className="label">Destination port</label>
              <input name="dst_port" className="input" type="number" min="0" max="65535" defaultValue="22" />
            </div>
            <div>
              <label className="label">Protocol</label>
              <select name="protocol" className="input" defaultValue="tcp">
                <option value="tcp">TCP</option>
                <option value="udp">UDP</option>
                <option value="icmp">ICMP</option>
              </select>
            </div>
            <div>
              <label className="label">Duration (s)</label>
              <input name="duration" className="input" type="number" min="0" step="any" defaultValue="120" />
            </div>
            <div>
              <label className="label">Packet count</label>
              <input name="packet_count" className="input" type="number" min="1" defaultValue="420" />
            </div>
            <div>
              <label className="label">Bytes sent / received</label>
              <div className="flex gap-2">
                <input name="bytes_sent" className="input" type="number" min="0" defaultValue="68000" placeholder="sent" />
                <input name="bytes_recv" className="input" type="number" min="0" defaultValue="1200" placeholder="recv" />
              </div>
            </div>
          </div>
          <div className="flex justify-end">
            <button className="btn-primary" disabled={simBusy}>
              {simBusy ? 'Ingesting…' : 'Simulate ingest'}
            </button>
          </div>
        </form>
      )}

      {!isAdmin && (
        <p className="rounded-lg border border-slate-800/60 bg-panel2/40 p-3 text-xs text-slate-500">
          Only admins can trigger simulated flow ingestion.
        </p>
      )}
    </div>
  )
}