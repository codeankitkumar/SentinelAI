import { useState } from 'react'
import { api, authError } from '../api/client'
import { Spinner, ErrorBanner, Badge } from '../components/ui'

export default function ThreatIntel() {
  const [providers, setProviders] = useState(null)
  const [ip, setIp] = useState('')
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [loaded, setLoaded] = useState(false)

  async function loadProviders() {
    if (loaded) return
    try {
      const res = await api.get('/threatintel/providers')
      setProviders(res.data.configured)
    } catch (err) {
      setError(authError(err))
    }
    setLoaded(true)
  }
  loadProviders()

  async function lookup(e) {
    e.preventDefault()
    if (!ip.trim()) return
    setBusy(true)
    setError('')
    try {
      const res = await api.get(`/threatintel/lookup/${encodeURIComponent(ip.trim())}`)
      setResults(res.data)
    } catch (err) {
      setError(authError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <div>
        <h1 className="text-xl font-bold text-slate-100">Threat Intelligence</h1>
        <p className="text-sm text-slate-500">Reputation lookups against configured providers.</p>
      </div>

      <div className="card">
        <h3 className="mb-2 text-sm font-semibold text-slate-200">Configured providers</h3>
        <div className="flex flex-wrap gap-2">
          {!providers ? (
            <Spinner className="h-4 w-4" />
          ) : providers.length === 0 ? (
            <div>
              <Badge color="amber">None configured</Badge>
              <p className="mt-2 text-xs text-slate-500">
                Add AbuseIPDB or VirusTotal API keys via <code className="text-slate-300">ABUSEIPDB_API_KEY</code> / <code className="text-slate-300">VIRUSTOTAL_API_KEY</code>.
              </p>
            </div>
          ) : (
            providers.map((p) => <Badge key={p} color="sky">{p}</Badge>)
          )}
        </div>
      </div>

      <form onSubmit={lookup} className="card space-y-3">
        <ErrorBanner message={error} />
        <div>
          <label className="label">IP address</label>
          <div className="flex gap-2">
            <input className="input" value={ip} onChange={(e) => setIp(e.target.value)} placeholder="e.g. 203.0.113.7" />
            <button className="btn-primary shrink-0" disabled={busy || !ip.trim()}>
              {busy ? 'Looking up…' : 'Lookup'}
            </button>
          </div>
        </div>
      </form>

      {results && (
        <div className="space-y-3">
          {results.length === 0 && <p className="text-sm text-slate-500">No results returned.</p>}
          {results.map((r, idx) => (
            <div key={`${r.provider}-${idx}`} className="card">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm text-slate-200">{r.ip}</span>
                  <Badge color="sky">{r.provider}</Badge>
                </div>
                <Badge color={r.found ? 'red' : 'green'}>{r.found ? 'Reported' : 'Not found'}</Badge>
              </div>
              {r.note && <p className="mt-2 text-xs text-slate-500">{r.note}</p>}
              {r.queried_at && <p className="mt-1 text-xs text-slate-500">Queried {r.queried_at}</p>}
              {Object.keys(r.data || {}).length > 0 && (
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {Object.entries(r.data).map(([k, v]) => (
                    <div key={k} className="rounded-lg border border-slate-800/60 bg-panel2/40 px-3 py-2">
                      <div className="text-[11px] uppercase tracking-wide text-slate-500">{k.replace(/_/g, ' ')}</div>
                      <div className="mt-0.5 break-words text-sm tabular text-slate-200">{String(v)}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}