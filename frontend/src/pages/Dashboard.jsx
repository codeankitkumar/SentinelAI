import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import { api } from '../api/client'
import { SeverityBadge, Spinner, ErrorBanner, formatTime } from '../components/ui'

const THREAT_COLORS = {
  normal: '#34d399',
  port_scan: '#38bdf8',
  brute_force: '#fbbf24',
  ddos: '#f87171',
  abnormal: '#a78bfa',
}

const SEV_COLORS = {
  critical: '#f87171',
  high: '#fb923c',
  medium: '#fbbf24',
  low: '#38bdf8',
  info: '#94a3b8',
}

function Stat({ label, value, sub, accent }) {
  return (
    <div className="card">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</div>
      <div className={`mt-1 text-3xl font-bold tabular ${accent || 'text-slate-100'}`}>{value}</div>
      {sub ? <div className="mt-1 text-xs text-slate-500">{sub}</div> : null}
    </div>
  )
}

function Panel({ title, children }) {
  return (
    <div className="card">
      <h3 className="mb-4 text-sm font-semibold text-slate-200">{title}</h3>
      {children}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    api
      .get('/dashboard/stats')
      .then((res) => !cancelled && setStats(res.data))
      .catch((err) => !cancelled && setError(err.message))
    return () => {
      cancelled = true
    }
  }, [])

  if (error) return <ErrorBanner message={error} />
  if (!stats) {
    return (
      <div className="grid min-h-[50vh] place-items-center">
        <Spinner className="h-10 w-10" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-100">Security Overview</h1>
        <span className="text-xs text-slate-500">Last 24h · live telemetry</span>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Total Events" value={stats.total_events.toLocaleString()} />
        <Stat label="Total Alerts" value={stats.total_alerts.toLocaleString()} accent="text-accent" sub={`${stats.active_alerts} active`} />
        <Stat label="Critical Incidents" value={stats.critical_incidents} accent="text-rose-400" />
        <Stat label="Alerts Requiring Action" value={stats.active_alerts} accent="text-amber-400" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Traffic & Alerts (hourly)">
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={stats.traffic_over_time}>
              <defs>
                <linearGradient id="ev" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.7} />
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="al" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f87171" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#f87171" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="bucket" tick={{ fontSize: 10, fill: '#64748b' }} interval={3} />
              <YAxis tick={{ fontSize: 10, fill: '#64748b' }} width={36} />
              <Tooltip contentStyle={{ background: '#111a2e', border: '1px solid #334155', borderRadius: 8 }} />
              <Area type="monotone" dataKey="events" stroke="#38bdf8" fill="url(#ev)" name="Events" />
              <Area type="monotone" dataKey="alerts" stroke="#f87171" fill="url(#al)" name="Alerts" />
            </AreaChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Attack Distribution">
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={stats.attack_distribution} dataKey="count" nameKey="threat_type" innerRadius={55} outerRadius={88} paddingAngle={2}>
                {stats.attack_distribution.map((e) => (
                  <Cell key={e.threat_type} fill={THREAT_COLORS[e.threat_type] || '#94a3b8'} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#111a2e', border: '1px solid #334155', borderRadius: 8 }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Alert Severity">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={stats.severity_distribution} layout="vertical" margin={{ left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10, fill: '#64748b' }} />
              <YAxis type="category" dataKey="severity" tick={{ fontSize: 11, fill: '#94a3b8' }} width={64} />
              <Tooltip contentStyle={{ background: '#111a2e', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="count" name="Alerts" radius={[0, 4, 4, 0]}>
                {stats.severity_distribution.map((s) => (
                  <Cell key={s.severity} fill={SEV_COLORS[s.severity] || '#94a3b8'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Top Suspicious IPs">
          <div className="space-y-2">
            {stats.top_suspicious_ips.length === 0 && <div className="text-sm text-slate-500">No suspicious IPs yet.</div>}
            {stats.top_suspicious_ips.map((ip) => (
              <div key={ip.ip} className="flex items-center justify-between border-b border-slate-800/60 py-1.5 last:border-0">
                <span className="font-mono text-sm text-slate-200">{ip.ip}</span>
                <div className="flex items-center gap-3">
                  <SeverityBadge severity={ip.severity} />
                  <span className="text-xs tabular text-slate-400">{ip.count} alerts</span>
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Recent Alerts">
          <div className="space-y-2">
            {stats.recent_alerts.length === 0 && <div className="text-sm text-slate-500">No alerts yet.</div>}
            {stats.recent_alerts.map((a) => (
              <div key={`${a.id}-${a.title}`} className="flex items-start justify-between gap-3 border-b border-slate-800/60 py-1.5 last:border-0">
                <div className="min-w-0">
                  <Link to="/alerts" className="block truncate text-sm text-slate-200 hover:text-accent">{a.title}</Link>
                  <div className="text-xs text-slate-500 font-mono">{a.source_ip || a.rule_name || ''} · {formatTime(a.timestamp)}</div>
                </div>
                <SeverityBadge severity={a.severity} />
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  )
}