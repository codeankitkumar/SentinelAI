import axios from 'axios'

// In dev Vite proxies /api to the backend; in Docker nginx does the same.
// Override with VITE_API_URL if the API is hosted elsewhere.
const baseURL = import.meta.env.VITE_API_URL || '/api'

export const api = axios.create({ baseURL })

const TOKEN_KEY = 'sentinel_token'

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* ignore quota errors */
  }
}

export function clearToken() {
  setToken(null)
}

// Attach Authorization header when a token is present.
api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401 clear the stale token so the UI can redirect to login.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && err.response.status === 401) clearToken()
    return Promise.reject(err)
  },
)

export function authError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg
  return err?.message || 'Request failed'
}

export default api