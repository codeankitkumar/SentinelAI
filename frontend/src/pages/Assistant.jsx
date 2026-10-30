import { useState } from 'react'
import { api, authError } from '../api/client'
import { ErrorBanner } from '../components/ui'

const INTENTS = [
  { value: 'explain', label: 'Explain alert' },
  { value: 'summarize', label: 'Summarize' },
  { value: 'investigate', label: 'Investigate' },
  { value: 'remediate', label: 'Remediate' },
  { value: 'report', label: 'Report' },
]

export default function Assistant() {
  const [intent, setIntent] = useState('investigate')
  const [query, setQuery] = useState('')
  const [alertId, setAlertId] = useState('')
  const [incidentId, setIncidentId] = useState('')
  const [sourceIp, setSourceIp] = useState('')
  const [response, setResponse] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function ask(e) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const payload = {
        intent,
        query: query.trim(),
        alert_id: alertId ? Number(alertId) : undefined,
        incident_id: incidentId ? Number(incidentId) : undefined,
        source_ip: sourceIp.trim() || undefined,
      }
      const res = await api.post('/assistant/query', payload)
      setResponse(res.data)
    } catch (err) {
      setError(authError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div>
        <h1 className="text-xl font-bold text-slate-100">AI Assistant</h1>
        <p className="text-sm text-slate-500">Rule-based SOC copilot for explanations, investigations, and recommendations.</p>
      </div>

      <form onSubmit={ask} className="card space-y-4">
        <ErrorBanner message={error} />
        <div>
          <label className="label">Intent</label>
          <div className="flex flex-wrap gap-2">
            {INTENTS.map((i) => (
              <button
                key={i.value}
                type="button"
                onClick={() => setIntent(i.value)}
                className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                  intent === i.value
                    ? 'border-accent/60 bg-accent/10 text-accent'
                    : 'border-slate-700 bg-panel2 text-slate-400 hover:text-slate-200'
                }`}
              >
                {i.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="label">Question / context</label>
          <textarea
            className="input min-h-24"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. Why did this IP trigger a brute-force alert and what should I do?"
          />
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <div>
            <label className="label">Alert ID</label>
            <input className="input" type="number" min="1" value={alertId} onChange={(e) => setAlertId(e.target.value)} placeholder="e.g. 12" />
          </div>
          <div>
            <label className="label">Incident ID</label>
            <input className="input" type="number" min="1" value={incidentId} onChange={(e) => setIncidentId(e.target.value)} placeholder="e.g. 3" />
          </div>
          <div>
            <label className="label">Source IP</label>
            <input className="input" value={sourceIp} onChange={(e) => setSourceIp(e.target.value)} placeholder="e.g. 203.0.113.7" />
          </div>
        </div>

        <div className="flex justify-end">
          <button className="btn-primary" disabled={busy}>
            {busy ? 'Thinking…' : 'Ask assistant'}
          </button>
        </div>
      </form>

      {response && (
        <div className="card space-y-4">
          <div className="inline-flex items-center gap-2">
            <span className="rounded-md bg-accent/10 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-accent">
              {response.intent}
            </span>
          </div>

          <div className="whitespace-pre-wrap rounded-lg border border-slate-800/60 bg-panel2/40 p-4 text-sm leading-relaxed text-slate-300">
            {response.answer}
          </div>

          {response.steps && response.steps.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Recommended steps</h4>
              <ol className="list-decimal space-y-1 pl-5 text-sm text-slate-300">
                {response.steps.map((s, idx) => <li key={idx}>{s}</li>)}
              </ol>
            </div>
          )}

          {response.sources && response.sources.length > 0 && (
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Sources</h4>
              <div className="flex flex-wrap gap-2">
                {response.sources.map((s, idx) => (
                  <span key={idx} className="rounded bg-slate-800 px-2 py-0.5 font-mono text-xs text-slate-400">{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}