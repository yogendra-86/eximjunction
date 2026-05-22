import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import Navbar from '../../components/Navbar'
import Footer from '../../components/Footer'
import axios from 'axios'
import { isLoggedIn } from '../../lib/auth'

const COUNTRIES = [
  {code:'IN',name:'India'},{code:'US',name:'United States'},{code:'CN',name:'China'},
  {code:'DE',name:'Germany'},{code:'JP',name:'Japan'},{code:'GB',name:'United Kingdom'},
  {code:'AE',name:'UAE'},{code:'SA',name:'Saudi Arabia'},{code:'BD',name:'Bangladesh'},
  {code:'VN',name:'Vietnam'},{code:'KR',name:'South Korea'},{code:'BR',name:'Brazil'},
  {code:'NL',name:'Netherlands'},{code:'SG',name:'Singapore'},{code:'AU',name:'Australia'},
]

const POPULAR = [
  {label:'India coffee exports 2019–2024', hs:'090111', reporter:'IN', flow:'export'},
  {label:'India pharma exports to US', hs:'300490', reporter:'IN', partner:'US', flow:'export'},
  {label:'India rice exports', hs:'100630', reporter:'IN', flow:'export'},
  {label:'Global mobile phone exporters', hs:'851712', flow:'export'},
  {label:'India crude oil imports', hs:'270900', reporter:'IN', flow:'import'},
  {label:'India diamond imports', hs:'710231', reporter:'IN', flow:'import'},
]

export default function PortalSearch() {
  const navigate  = useNavigate()
  const loggedIn  = isLoggedIn()
  const [form, setForm] = useState({
    hs_code: '', q: '', reporter: '', partner: '',
    flow: 'export', year_from: '2019', year_to: '2024',
  })
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const runSearch = async (overrides = {}) => {
    if (!loggedIn) { navigate('/signup'); return }
    const params = { ...form, ...overrides }
    if (!params.hs_code && !params.q) { setError('Enter an HS code or product keyword'); return }
    setLoading(true); setError('')
    try {
      const token = localStorage.getItem('token')
      const res = await axios.get('/api/v1/portal/search', {
        params: {
          hs_code: params.hs_code || undefined,
          q: params.q || undefined,
          reporter: params.reporter || undefined,
          partner: params.partner || undefined,
          flow: params.flow,
          year_from: parseInt(params.year_from),
          year_to:   parseInt(params.year_to),
        },
        headers: { Authorization: `Bearer ${token}` },
      })
      // Store results in sessionStorage and navigate
      sessionStorage.setItem('portal_results', JSON.stringify(res.data))
      sessionStorage.setItem('portal_params', JSON.stringify({ ...params, ...overrides }))
      navigate('/portal/results')
    } catch (e) {
      setError(e.response?.data?.detail || 'Search failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const usePopular = (p) => {
    const next = { hs_code: p.hs, q: '', reporter: p.reporter || '', partner: p.partner || '', flow: p.flow }
    setForm(f => ({ ...f, ...next }))
    runSearch(next)
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navbar />

      <div className="flex-1 py-12 px-4">
        <div className="max-w-4xl mx-auto">

          {/* Header */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 bg-brand-50 text-brand-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-4">
              🌐 Trade Data Portal
            </div>
            <h1 className="text-4xl font-extrabold text-gray-900 mb-3">
              Search Global Trade Data
            </h1>
            <p className="text-gray-500 max-w-xl mx-auto">
              Search by product, country, and year. Free users see 10 records per search.
              Upgrade to download CSV exports.
            </p>
            {!loggedIn && (
              <div className="mt-4 p-3 bg-brand-50 border border-brand-200 rounded-lg inline-block">
                <p className="text-sm text-brand-700">
                  <Link to="/signup" className="font-semibold underline">Sign up free</Link>
                  {' '}to search. No credit card required.
                </p>
              </div>
            )}
          </div>

          {/* Search form */}
          <div className="card shadow-md mb-8">
            <div className="grid md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="label">HS Code</label>
                <input
                  value={form.hs_code}
                  onChange={e => set('hs_code', e.target.value)}
                  className="input"
                  placeholder="e.g. 090111, 300490, 851712"
                />
                <p className="text-xs text-gray-400 mt-1">6-digit product code</p>
              </div>
              <div>
                <label className="label">Or search by keyword</label>
                <input
                  value={form.q}
                  onChange={e => set('q', e.target.value)}
                  className="input"
                  placeholder="e.g. coffee, mobile phone, rice"
                />
              </div>
            </div>

            <div className="grid md:grid-cols-4 gap-4 mb-6">
              <div>
                <label className="label">Flow</label>
                <select value={form.flow} onChange={e => set('flow', e.target.value)} className="input">
                  <option value="export">Export</option>
                  <option value="import">Import</option>
                </select>
              </div>
              <div>
                <label className="label">Reporter (Exporter)</label>
                <select value={form.reporter} onChange={e => set('reporter', e.target.value)} className="input">
                  <option value="">All countries</option>
                  {COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Year From</label>
                <select value={form.year_from} onChange={e => set('year_from', e.target.value)} className="input">
                  {[2019,2020,2021,2022,2023,2024].map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
              <div>
                <label className="label">Year To</label>
                <select value={form.year_to} onChange={e => set('year_to', e.target.value)} className="input">
                  {[2019,2020,2021,2022,2023,2024].map(y => <option key={y} value={y}>{y}</option>)}
                </select>
              </div>
            </div>

            {error && <p className="mb-4 text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</p>}

            <button
              onClick={() => runSearch()}
              disabled={loading}
              className="btn-primary w-full py-3 text-base"
            >
              {loading ? '🔍 Searching...' : '🔍 Search Trade Data'}
            </button>
          </div>

          {/* Popular searches */}
          <div>
            <p className="text-sm font-semibold text-gray-500 mb-3">Popular searches</p>
            <div className="grid sm:grid-cols-2 gap-2">
              {POPULAR.map((p, i) => (
                <button
                  key={i}
                  onClick={() => usePopular(p)}
                  disabled={loading}
                  className="text-left px-4 py-3 bg-white border border-gray-200 rounded-lg hover:border-brand-300 hover:bg-brand-50 transition-colors text-sm text-gray-700 font-medium"
                >
                  ↗ {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Plan info */}
          <div className="mt-8 p-4 bg-white border border-gray-200 rounded-xl">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center text-sm">
              {[
                {plan:'Free', limit:'10 rows', export:'No',    price:'₹0'},
                {plan:'Starter', limit:'500 rows', export:'CSV', price:'₹999/mo'},
                {plan:'Professional', limit:'Unlimited', export:'CSV+Excel', price:'₹3,999/mo'},
                {plan:'Enterprise', limit:'Unlimited', export:'All+Shipments', price:'₹14,999/mo'},
              ].map(p => (
                <div key={p.plan} className="p-3 rounded-lg bg-gray-50">
                  <p className="font-bold text-gray-900">{p.plan}</p>
                  <p className="text-gray-500 text-xs mt-1">{p.limit} · {p.export}</p>
                  <p className="text-brand-600 font-semibold text-xs mt-1">{p.price}</p>
                </div>
              ))}
            </div>
            <p className="text-center mt-3">
              <Link to="/portal/plans" className="text-xs text-brand-600 hover:underline font-medium">
                Compare all plans →
              </Link>
            </p>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}
