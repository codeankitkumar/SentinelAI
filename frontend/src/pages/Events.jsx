import { useCallback, useEffect, useState } from 'react'
import { api, authError } from '../api/client'
import { SeverityBadge, Spinner, ErrorBanner, EmptyState, formatTime } from '../components/ui'

const PAGE = 20
const THREAT_CLS = {
  normal: 'text-emerald-300',
  port_scan: 'text-sky-300',
  brute_force: 'text-amber-300',
  ddos: 'text-rose-300',
  abnormal: 'text-violet-300',
}

export default function Events() {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [threat, setThreat] = useState('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    setLoading(true)
    setError('')
    api
      .get('/events', { params: { page, page_size: PAGE, threat_type: threat || undefined, query: query || undefined } })
      .then((res) => {
        setItems(res.data.items)
        setTotal(res.data.total)
      })
      .catch((err) => setError(authError(err)))
      .finally(() => setLoading(false))
  }, [page, threat, query])

  useEffect(() => {
    load()
  }, [load])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-100">Flow Events</h1>
        <span className="text-sm text-slate-500 tabular">{total.toLocaleString()} total</span>
      </div>

      <div className="flex flex-wrap gap-3">
        <input className="input max-w-xs" placeholder="Search IP or protocol…" value={query} onChange={(e) => { setQuery(e.target.value); setPage(1) }} />
        <select className="input w-auto" value={threat} onChange={(e) => { setThreat(e.target.value); setPage(1) }}>
          <option value="">All classifications</option>
          <option value="normal">Normal</option>
          <option value="port_scan">Port scan</option>
          <option value="brute_force">Brute force</option>
          <option value="ddos">DDoS</option>
          <option value="abnormal">Abnormal</option>
        </select>
      </div>

      <ErrorBanner message={error} />

      <div className="card overflow-hidden p-0">
        {loading ? (
          <div className="grid place-items-center p-16"><Spinner /></div>
        ) : items.length === 0 ? (
          <div className="p-6"><EmptyState message="No flow events match the filters." /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-panel2 text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-3">Time</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Destination</th>
                  <th className="px-4 py-3">Proto</th>
                  <th className="px-4 py-3 text-right">Packets</th>
                  <th className="px-4 py-3 text-right">Bytes</th>
                  <th className="px-4 py-3">Classification</th>
                  <th className="px-4 py-3">Severity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {items.map((e) => (
                  <tr key={e.id} className="hover:bg-slate-800/30">
                    <td className="whitespace-nowrap px-4 py-2 font-mono text-xs text-slate-400">{formatTime(e.timestamp)}</td>
                    <td className="whitespace-nowrap px-4 py-2 font-mono text-xs text-slate-300">{e.src_ip}:{e.src_port}</td>
                    <td className="whitespace-nowrap px-4 py-2 font-mono text-xs text-slate-300">{e.dst_ip}:{e.dst_port}</td>
                    <td className="px-4 py-2 font-mono text-xs uppercase text-slate-400">{e.protocol}</td>
                    <td className="px-4 py-2 text-right tabular text-slate-300">{e.packet_count}</td>
                    <td className="px-4 py-2 text-right tabular text-slate-300">{(e.bytes_sent + e.bytes_recv).toLocaleString()}</td>
                    <td className="px-4 py-2">
                      <span className={`font-medium ${THREAT_CLS[e.threat_type] || 'text-slate-300'}`}>
                        {String(e.threat_type || '').replace(/_/g, ' ')}
                      </span>
                      <span className="ml-2 text-xs tabular text-slate-500">{e.threat_score}</span>
                    </td>
                    <td className="px-4 py-2"><SeverityBadge severity={e.severity || 'info'} /></td>
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