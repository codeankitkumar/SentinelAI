import { useCallback, useEffect, useState } from 'react'
import { api, authError } from '../api/client'
import { Spinner, ErrorBanner, Badge } from '../components/ui'

export default function MLStatus() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(() => {
    setError('')
    api
      .get('/ml/status')
      .then((res) => setStatus(res.data))
      .catch((err) => setError(authError(err)))
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function retrain() {
    setBusy(true)
    setError('')
    try {
      await api.post('/ml/retrain', {})
      load()
    } catch (err) {
      setError(authError(err))
    } finally {
      setBusy(false)
    }
  }

  if (error) return <ErrorBanner message={error} />
  if (!status) {
    return (
      <div className="grid min-h-[50vh] place-items-center">
        <Spinner className="h-10 w-10" />
      </div>
    )
  }

  const metrics = status.metrics || {}
  const accuracy = metrics.accuracy !== undefined ? Math.round(metrics.accuracy * 100) : null

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-bold text-slate-100">ML Engine</h1>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-400">Mode</div>
          <div className="mt-1 text-xl font-semibold text-slate-100">{status.mode}</div>
          <div className="mt-2">
            <Badge color={status.model_loaded ? 'green' : 'amber'}>
              {status.model_loaded ? 'Model loaded' : 'No model'}
            </Badge>
          </div>
        </div>
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-400">Accuracy (synthetic)</div>
          <div className="mt-1 text-xl font-semibold text-slate-100 tabular">
            {accuracy === null ? '—' : `${accuracy}%`}
          </div>
          <div className="mt-1 text-xs text-slate-500">Trained on labeled synthetic flows</div>
        </div>
        <div className="card">
          <div className="text-xs uppercase tracking-wide text-slate-400">Training report</div>
          <div className="mt-1 text-xl font-semibold text-slate-100">
            {status.training_report_available ? 'Available' : 'Pending'}
          </div>
        </div>
      </div>

      {metrics && Object.keys(metrics).length > 0 && (
        <div className="card">
          <h3 className="mb-3 text-sm font-semibold text-slate-200">Training Metrics</h3>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {Object.entries(metrics)
              .filter(([k]) => typeof k === 'string' && k !== 'metrics')
              .map(([key, val]) => (
                <div key={key} className="rounded-lg border border-slate-800/60 bg-panel2/40 px-3 py-2">
                  <div className="text-[11px] uppercase tracking-wide text-slate-500">{key.replace(/_/g, ' ')}</div>
                  <div className="mt-0.5 text-lg font-semibold tabular text-slate-100">
                    {typeof val === 'number' ? (val > 0 && val < 1 ? (val * 100).toFixed(1) + '%' : val.toLocaleString()) : String(val)}
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      <div className="card flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">Retrain model</h3>
          <p className="text-xs text-slate-500">Re-trains on the bundled synthetic dataset and reloads artifacts.</p>
        </div>
        <button className="btn-primary" onClick={retrain} disabled={busy}>
          {busy ? 'Training…' : 'Retrain'}
        </button>
      </div>
    </div>
  )
}