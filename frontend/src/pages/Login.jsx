import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../store/auth'
import { authError } from '../api/client'
import { ErrorBanner } from '../components/ui'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await login(username.trim(), password)
      navigate('/', { replace: true })
    } catch (err) {
      setError(authError(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center">
          <span className="grid h-14 w-14 place-items-center rounded-2xl bg-accent text-slate-900 shadow-lg shadow-accent/20">
            <svg viewBox="0 0 24 24" className="h-8 w-8" fill="currentColor">
              <path d="M12 2l2.4 4.6L19.5 8l-3.2 4.4.7 5.3L12 20.5l-5-2.8.7-5.3L4.5 8l5.1-1.4L12 2z" />
            </svg>
          </span>
          <h1 className="mt-4 text-2xl font-bold text-slate-100">SentinelAI</h1>
          <p className="text-sm text-slate-500">AI-Powered Threat Detection &amp; SOC Platform</p>
        </div>

        <form onSubmit={onSubmit} className="card space-y-4">
          <ErrorBanner message={error} />
          <div>
            <label className="label">Username</label>
            <input
              className="input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoFocus
              autoComplete="username"
              placeholder="admin"
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              placeholder="••••••••"
            />
          </div>
          <button className="btn-primary w-full justify-center" disabled={busy || !username || !password}>
            {busy ? 'Signing in…' : 'Sign in'}
          </button>

          <div className="rounded-lg border border-slate-700/60 bg-panel2/40 px-3 py-2 text-xs text-slate-400">
            Demo credentials — <span className="text-slate-200">admin / Admin@12345</span> or{' '}
            <span className="text-slate-200">analyst / Analyst@12345</span>
          </div>
        </form>
      </div>
    </div>
  )
}