import { useEffect, useState } from 'react'
import { getKeys, searchProducts, getTopPartners, getTradeFlow, getTariffs, getCompliance } from '../../lib/api'

const ENDPOINTS = [
  { id: 'search',      label: 'Search HS Codes',     icon: '🔍' },
  { id: 'partners',    label: 'Top Trading Partners', icon: '🌍' },
  { id: 'tradeflow',   label: 'Trade Flow Trend',     icon: '📈' },
  { id: 'tariffs',     label: 'Tariff Rates',         icon: '💰' },
  { id: 'compliance',  label: 'Compliance Docs',      icon: '📋' },
]

const SAMPLE_COUNTRIES = ['IN','US','CN','DE','JP','GB','AE','SA','BD','VN','KR','BR']

function Field({ label, children }) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
    </div>
  )
}

export default function Explorer() {
  const [keys,     setKeys]     = useState([])
  const [apiKey,   setApiKey]   = useState('')
  const [endpoint, setEndpoint] = useState('search')
  const [params,   setParams]   = useState({
    q: 'coffee', level: '', hs_code: '090111', reporter: 'IN',
    partner: 'US', flow: 'export', year: '2024',
    year_from: '2019', year_to: '2024',
  })
  const [result,  setResult]   = useState(null)
  const [loading, setLoading]  = useState(false)
  const [error,   setError]    = useState('')
  const [copied,  setCopied]   = useState(false)

  useEffect(() => {
    getKeys().then(r => {
      const active = (r.data || []).filter(k => k.is_active)
      setKeys(active)
      if (active.length > 0) setApiKey(active[0].key_prefix + '...')
    }).catch(() => {})
  }, [])

  const p = (name) => (e) => setParams({ ...params, [name]: e.target.value })

  const run = async () => {
    if (!apiKey || apiKey.endsWith('...')) {
      setError('Enter your full API key (tdk_...). You can copy it from the API Keys page.')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      let res
      if (endpoint === 'search')
        res = await searchProducts(params.q, params.level || undefined, apiKey)
      else if (endpoint === 'partners')
        res = await getTopPartners(params.hs_code, params.reporter, params.flow, params.year, apiKey)
      else if (endpoint === 'tradeflow')
        res = await getTradeFlow(params.reporter, params.partner, params.hs_code, params.flow, params.year_from, params.year_to, apiKey)
      else if (endpoint === 'tariffs')
        res = await getTariffs(params.reporter, params.hs_code, params.partner || undefined, params.year, apiKey)
      else if (endpoint === 'compliance')
        res = await getCompliance(params.reporter, params.partner, params.hs_code || undefined, apiKey)
      setResult(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Request failed.')
    } finally {
      setLoading(false)
    }
  }

  const copyResult = () => {
    navigator.clipboard.writeText(JSON.stringify(result, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">API Explorer</h1>
        <p className="text-sm text-gray-500 mt-1">Test queries live against the trade database</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Left: controls */}
        <div className="space-y-4">
          {/* API Key */}
          <div className="card">
            <Field label="Your API Key">
              <input
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
                className="input font-mono text-sm"
                placeholder="tdk_YourFullKeyHere"
              />
              {keys.length > 0 && (
                <p className="text-xs text-gray-400 mt-1">
                  You have {keys.length} active key{keys.length > 1 ? 's' : ''}. 
                  Go to <a href="/dashboard/keys" className="text-brand-600 hover:underline">API Keys</a> to copy the full key.
                </p>
              )}
            </Field>
          </div>

          {/* Endpoint selector */}
          <div className="card">
            <label className="label">Endpoint</label>
            <div className="grid grid-cols-2 gap-2">
              {ENDPOINTS.map(ep => (
                <button
                  key={ep.id}
                  onClick={() => setEndpoint(ep.id)}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium border transition-colors text-left ${
                    endpoint === ep.id
                      ? 'bg-brand-50 border-brand-300 text-brand-700'
                      : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <span>{ep.icon}</span>
                  <span className="truncate">{ep.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Dynamic params */}
          <div className="card space-y-3">
            <label className="label">Parameters</label>

            {endpoint === 'search' && (
              <>
                <Field label="Search term (q) *">
                  <input value={params.q} onChange={p('q')} className="input" placeholder="coffee, mobile, 0901..." />
                </Field>
                <Field label="Level (optional)">
                  <select value={params.level} onChange={p('level')} className="input">
                    <option value="">All levels</option>
                    <option value="2">2 — Chapter</option>
                    <option value="4">4 — Heading</option>
                    <option value="6">6 — Subheading</option>
                  </select>
                </Field>
              </>
            )}

            {(endpoint === 'partners' || endpoint === 'tariffs' || endpoint === 'compliance' || endpoint === 'tradeflow') && (
              <Field label="HS Code *">
                <input value={params.hs_code} onChange={p('hs_code')} className="input" placeholder="090111" />
              </Field>
            )}

            {(endpoint === 'partners' || endpoint === 'tariffs' || endpoint === 'tradeflow' || endpoint === 'compliance') && (
              <Field label="Reporter (exporting country) *">
                <select value={params.reporter} onChange={p('reporter')} className="input">
                  {SAMPLE_COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </Field>
            )}

            {(endpoint === 'tradeflow' || endpoint === 'compliance') && (
              <Field label="Partner (importing country) *">
                <select value={params.partner} onChange={p('partner')} className="input">
                  {SAMPLE_COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </Field>
            )}

            {endpoint === 'tariffs' && (
              <Field label="Partner country (optional)">
                <select value={params.partner} onChange={p('partner')} className="input">
                  <option value="">Any (MFN only)</option>
                  {SAMPLE_COUNTRIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </Field>
            )}

            {(endpoint === 'partners' || endpoint === 'tariffs') && (
              <Field label="Year">
                <input value={params.year} onChange={p('year')} className="input" placeholder="2024" />
              </Field>
            )}

            {(endpoint === 'partners' || endpoint === 'tradeflow') && (
              <Field label="Flow">
                <select value={params.flow} onChange={p('flow')} className="input">
                  <option value="export">Export</option>
                  <option value="import">Import</option>
                </select>
              </Field>
            )}

            {endpoint === 'tradeflow' && (
              <div className="grid grid-cols-2 gap-3">
                <Field label="Year from">
                  <input value={params.year_from} onChange={p('year_from')} className="input" />
                </Field>
                <Field label="Year to">
                  <input value={params.year_to} onChange={p('year_to')} className="input" />
                </Field>
              </div>
            )}
          </div>

          <button
            onClick={run}
            disabled={loading}
            className="btn-primary w-full py-3"
          >
            {loading ? '⏳ Running query...' : '▶ Run Query'}
          </button>
        </div>

        {/* Right: result */}
        <div>
          <div className="bg-gray-900 rounded-xl overflow-hidden h-full min-h-96">
            <div className="flex items-center justify-between px-4 py-3 bg-gray-800">
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-red-500"></span>
                <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                <span className="ml-2 text-xs text-gray-400">Response</span>
              </div>
              {result && (
                <button onClick={copyResult} className="text-xs text-gray-400 hover:text-white">
                  {copied ? '✓ Copied' : 'Copy JSON'}
                </button>
              )}
            </div>

            <div className="p-4 overflow-auto" style={{ maxHeight: 600 }}>
              {loading && (
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                  <span className="animate-spin">⟳</span> Querying...
                </div>
              )}
              {error && (
                <div className="text-red-400 text-sm">
                  <span className="font-semibold">Error:</span> {error}
                </div>
              )}
              {result && !loading && (
                <pre className="text-xs text-blue-300 leading-relaxed whitespace-pre-wrap">
                  {JSON.stringify(result, null, 2)}
                </pre>
              )}
              {!loading && !error && !result && (
                <p className="text-gray-500 text-sm">Select an endpoint and run a query to see results here.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
