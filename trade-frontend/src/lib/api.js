import axios from 'axios'

const BASE = '/api/v1'

const http = axios.create({ baseURL: BASE })

// Attach token to every request if present
http.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

// Auto-logout on 401
http.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      const path = window.location.pathname
      if (path.startsWith('/dashboard')) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

// ── Auth ────────────────────────────────────────────
export const signup = (data) => http.post('/auth/signup', data)
export const login  = (data) => http.post('/auth/login', data)
export const getMe  = ()     => http.get('/auth/me')

// ── API Keys ─────────────────────────────────────────
export const getKeys      = ()         => http.get('/auth/keys')
export const createKey    = (name)     => http.post('/auth/keys', { name })
export const revokeKey    = (id)       => http.delete(`/auth/keys/${id}`)
export const getKeyUsage  = (id)       => http.get(`/auth/keys/${id}/usage`)

// ── Billing ──────────────────────────────────────────
export const getPlans        = ()           => http.get('/billing/plans')
export const getSubscription = ()           => http.get('/billing/subscription')
export const checkout        = (plan_code)  => http.post('/billing/checkout', { plan_code })
export const verifyPayment   = (data)       => http.post('/billing/verify-payment', data)
export const mockSuccess     = (order_id)   => http.post(`/billing/mock-success/${order_id}`)
export const getPayments     = ()           => http.get('/billing/payments')

// ── Trade Data ───────────────────────────────────────
// These use X-API-Key not Bearer — pass key explicitly
export const searchProducts = (q, level, apiKey) =>
  axios.get(`${BASE}/products/search`, {
    params: { q, level },
    headers: { 'X-API-Key': apiKey }
  })

export const getTopPartners = (hs_code, reporter, flow, year, apiKey) =>
  axios.get(`${BASE}/products/${hs_code}/top-partners`, {
    params: { reporter, flow, year, limit: 10 },
    headers: { 'X-API-Key': apiKey }
  })

export const getTradeFlow = (reporter, partner, hs_code, flow, year_from, year_to, apiKey) =>
  axios.get(`${BASE}/trade-flows`, {
    params: { reporter, partner, hs_code, flow, year_from, year_to },
    headers: { 'X-API-Key': apiKey }
  })

export const getTariffs = (reporter, hs_code, partner, year, apiKey) =>
  axios.get(`${BASE}/tariffs`, {
    params: { reporter, hs_code, partner, year },
    headers: { 'X-API-Key': apiKey }
  })

export const getCompliance = (reporter, partner, hs_code, apiKey) =>
  axios.get(`${BASE}/compliance`, {
    params: { reporter, partner, hs_code },
    headers: { 'X-API-Key': apiKey }
  })

export default http
