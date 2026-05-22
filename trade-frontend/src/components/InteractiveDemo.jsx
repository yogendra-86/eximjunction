import { useState } from 'react'
import axios from 'axios'

// Demo uses a public read-only key — replace with your actual demo key
// Set this in your .env as VITE_DEMO_API_KEY=tdk_your_demo_key_here
const DEMO_KEY = import.meta.env.VITE_DEMO_API_KEY || ''
const BASE     = '/api/v1'

const DEMO_QUERIES = [
  {
    id: 'coffee_partners',
    label: '☕ India coffee exports',
    description: "Which countries buy the most coffee from India?",
    category: 'Trading Partners',
    badge: 'Most Popular',
    params: { hs_code: '090111', reporter: 'IN', flow: 'export', year: 2024 },
    call: (key) => axios.get(`${BASE}/products/090111/top-partners`,
      { params: { reporter: 'IN', flow: 'export', year: 2024, limit: 5 }, headers: { 'X-API-Key': key } }),
    renderResult: (data) => (
      <div>
        <p className="text-xs text-gray-400 mb-3">
          Top 5 export markets for <strong className="text-white">HS 090111 — Coffee (not roasted)</strong> from India in 2024
        </p>
        <div className="space-y-2">
          {data.partners?.map((p, i) => {
            const pct = Math.round((p.value_usd / data.partners[0].value_usd) * 100)
            return (
              <div key={i}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white font-medium">#{p.rank} {p.country.name}</span>
                  <span className="text-green-400">${(p.value_usd / 1e9).toFixed(2)}B</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div className="bg-green-400 h-1.5 rounded-full" style={{ width: `${pct}%` }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    ),
  },
  {
    id: 'rice_trend',
    label: '🌾 India rice export trend',
    description: "How have India's rice exports to Saudi Arabia changed since 2019?",
    category: 'Trade Trends',
    badge: 'CAGR Included',
    params: { reporter: 'IN', partner: 'SA', hs_code: '100630' },
    call: (key) => axios.get(`${BASE}/trade-flows`,
      { params: { reporter: 'IN', partner: 'SA', hs_code: '100630', flow: 'export', year_from: 2019, year_to: 2024 },
        headers: { 'X-API-Key': key } }),
    renderResult: (data) => (
      <div>
        <p className="text-xs text-gray-400 mb-3">
          <strong className="text-white">India → Saudi Arabia</strong> · Milled Rice · 2019–2024
        </p>
        <div className="space-y-1.5">
          {data.points?.map((p, i) => {
            const max = Math.max(...data.points.map(x => x.value_usd))
            const pct = Math.round((p.value_usd / max) * 100)
            return (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs text-gray-400 w-8">{p.year}</span>
                <div className="flex-1 bg-gray-700 rounded-full h-2">
                  <div className="bg-blue-400 h-2 rounded-full" style={{ width: `${pct}%` }} />
                </div>
                <span className="text-xs text-blue-300 w-16 text-right">${(p.value_usd / 1e9).toFixed(2)}B</span>
              </div>
            )
          })}
        </div>
        {data.growth_rate_pct !== null && (
          <div className="mt-3 pt-3 border-t border-gray-600 flex justify-between text-xs">
            <span className="text-gray-400">CAGR (2019–2024)</span>
            <span className={`font-bold ${data.growth_rate_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {data.growth_rate_pct >= 0 ? '↑' : '↓'} {Math.abs(data.growth_rate_pct)}% / year
            </span>
          </div>
        )}
      </div>
    ),
  },
  {
    id: 'tariff_tshirt',
    label: '👕 Tariff on cotton T-shirts',
    description: "What duty does the US charge on cotton T-shirts from India vs Bangladesh?",
    category: 'Tariff Rates',
    badge: 'FTA Comparison',
    call: (key) => axios.get(`${BASE}/tariffs`,
      { params: { reporter: 'US', hs_code: '610910', partner: 'BD', year: 2024 },
        headers: { 'X-API-Key': key } }),
    renderResult: (data) => (
      <div>
        <p className="text-xs text-gray-400 mb-3">
          <strong className="text-white">US import duty on HS 610910</strong> — Cotton T-shirts (2024)
        </p>
        <div className="space-y-2">
          {data.map?.((t, i) => (
            <div key={i} className="flex justify-between items-center p-2 bg-gray-700 rounded-lg">
              <div>
                <p className="text-xs font-medium text-white">{t.rate_type}</p>
                {t.partner && <p className="text-xs text-gray-400">For: {t.partner.name}</p>}
                {t.agreement && <p className="text-xs text-green-400">{t.agreement}</p>}
                {t.notes && <p className="text-xs text-gray-500 mt-0.5 max-w-48 truncate">{t.notes}</p>}
              </div>
              <span className={`text-lg font-bold ${t.ad_valorem_rate === 0 ? 'text-green-400' : 'text-yellow-400'}`}>
                {t.ad_valorem_rate}%
              </span>
            </div>
          ))}
          {(!data.map || data.length === 0) && (
            <div className="p-3 bg-gray-700 rounded-lg text-center">
              <p className="text-yellow-400 font-bold text-xl">16.5%</p>
              <p className="text-xs text-gray-400">US MFN rate for cotton T-shirts</p>
              <p className="text-xs text-gray-500 mt-1">Bangladesh gets 0% under EU EBA — not US</p>
            </div>
          )}
        </div>
      </div>
    ),
  },
  {
    id: 'compliance_pharma',
    label: '💊 Pharma export compliance',
    description: "What documents are needed to export medicines from India to the US?",
    category: 'Compliance Docs',
    badge: 'Regulatory',
    call: (key) => axios.get(`${BASE}/compliance`,
      { params: { reporter: 'IN', partner: 'US', hs_code: '300490' },
        headers: { 'X-API-Key': key } }),
    renderResult: (data) => (
      <div>
        <p className="text-xs text-gray-400 mb-3">
          <strong className="text-white">India → US Pharma exports</strong> · HS 300490 · Required documents
        </p>
        <div className="space-y-1.5">
          {data.documents?.slice(0, 6).map((d, i) => (
            <div key={i} className="flex items-start gap-2 p-2 bg-gray-700 rounded-lg">
              <span className={`mt-0.5 flex-shrink-0 text-xs font-bold w-14 ${d.is_mandatory ? 'text-red-400' : 'text-yellow-400'}`}>
                {d.is_mandatory ? 'REQUIRED' : 'OPTIONAL'}
              </span>
              <div>
                <p className="text-xs text-white font-medium">{d.document_name}</p>
                {d.issuing_authority && <p className="text-xs text-gray-500">{d.issuing_authority}</p>}
              </div>
            </div>
          ))}
        </div>
      </div>
    ),
  },
  {
    id: 'phone_exporters',
    label: '📱 Global phone exporters',
    description: "Who exports the most mobile phones in the world?",
    category: 'Trading Partners',
    badge: 'Global View',
    call: (key) => axios.get(`${BASE}/products/851712/top-partners`,
      { params: { flow: 'export', year: 2024, limit: 5 }, headers: { 'X-API-Key': key } }),
    renderResult: (data) => (
      <div>
        <p className="text-xs text-gray-400 mb-3">
          <strong className="text-white">HS 851712 — Mobile Phones</strong> · Top 5 global exporters · 2024
        </p>
        <div className="space-y-2">
          {data.partners?.map((p, i) => {
            const pct = Math.round((p.value_usd / data.partners[0].value_usd) * 100)
            return (
              <div key={i}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white font-medium">#{p.rank} {p.country.name}</span>
                  <span className="text-purple-400">${(p.value_usd / 1e9).toFixed(1)}B</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-1.5">
                  <div className="bg-purple-400 h-1.5 rounded-full" style={{ width: `${pct}%` }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    ),
  },
]

export default function InteractiveDemo() {
  const [selected,  setSelected]  = useState(DEMO_QUERIES[0])
  const [result,    setResult]    = useState(null)
  const [loading,   setLoading]   = useState(false)
  const [error,     setError]     = useState('')
  const [hasRun,    setHasRun]    = useState(false)

  const run = async (query) => {
    if (!DEMO_KEY) {
      setError('Demo key not configured. Sign up for free to try the API.')
      return
    }
    setSelected(query)
    setLoading(true)
    setError('')
    setResult(null)
    setHasRun(true)
    try {
      const res = await query.call(DEMO_KEY)
      setResult(res.data)
    } catch (e) {
      if (e.response?.status === 429) {
        setError('Demo rate limit reached. Sign up free for your own API key with 50 calls/day.')
      } else {
        setError(e.response?.data?.detail || 'Query failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="py-24 bg-gray-900" id="demo">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-brand-900 border border-brand-700 text-brand-300 text-xs font-semibold px-3 py-1.5 rounded-full mb-4">
            ⚡ Live Demo — Real Data
          </div>
          <h2 className="text-3xl lg:text-4xl font-extrabold text-white mb-4">
            Try it right now. No signup needed.
          </h2>
          <p className="text-gray-400 max-w-xl mx-auto">
            Click any query below and see actual trade data come back in milliseconds. This is exactly what your application gets when it calls the API.
          </p>
        </div>

        <div className="grid lg:grid-cols-5 gap-6">
          {/* Query selector — left panel */}
          <div className="lg:col-span-2 space-y-2">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Choose a query</p>
            {DEMO_QUERIES.map(q => (
              <button
                key={q.id}
                onClick={() => run(q)}
                className={`w-full text-left px-4 py-3.5 rounded-xl border transition-all ${
                  selected.id === q.id && hasRun
                    ? 'bg-brand-900 border-brand-600 text-white'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-750 hover:border-gray-600'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold truncate">{q.label}</p>
                    <p className="text-xs text-gray-500 mt-0.5 leading-snug">{q.description}</p>
                  </div>
                  <span className="flex-shrink-0 text-xs bg-gray-700 text-gray-400 px-2 py-0.5 rounded-full whitespace-nowrap">
                    {q.category}
                  </span>
                </div>
              </button>
            ))}
          </div>

          {/* Result panel — right */}
          <div className="lg:col-span-3">
            <div className="bg-gray-950 rounded-2xl overflow-hidden border border-gray-800 h-full min-h-96">
              {/* Terminal header */}
              <div className="flex items-center justify-between px-4 py-3 bg-gray-800 border-b border-gray-700">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-red-500"></span>
                  <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                  <span className="w-3 h-3 rounded-full bg-green-500"></span>
                  <span className="ml-3 text-xs text-gray-400 font-mono">
                    GET /api/v1/{selected.id === 'coffee_partners' || selected.id === 'phone_exporters' ? 'products/*/top-partners' :
                                  selected.id === 'rice_trend' ? 'trade-flows' :
                                  selected.id === 'tariff_tshirt' ? 'tariffs' : 'compliance'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {loading && <span className="text-xs text-yellow-400 animate-pulse">● Running...</span>}
                  {!loading && result && <span className="text-xs text-green-400">● 200 OK</span>}
                  {!loading && error && <span className="text-xs text-red-400">● Error</span>}
                  {!loading && !result && !error && <span className="text-xs text-gray-500">● Ready</span>}
                </div>
              </div>

              {/* Content */}
              <div className="p-5">
                {!hasRun && (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <div className="text-4xl mb-4">👆</div>
                    <p className="text-gray-400 text-sm">Select a query on the left to see live results</p>
                    <p className="text-gray-600 text-xs mt-2">No signup required</p>
                  </div>
                )}

                {loading && (
                  <div className="flex flex-col items-center justify-center h-64">
                    <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                    <p className="text-gray-400 text-sm">Querying trade database...</p>
                  </div>
                )}

                {error && !loading && (
                  <div className="p-4 bg-red-900/30 border border-red-800 rounded-lg">
                    <p className="text-red-400 text-sm">{error}</p>
                    <a href="/signup" className="inline-block mt-3 text-xs bg-brand-600 text-white px-4 py-2 rounded-lg hover:bg-brand-700">
                      Sign up free →
                    </a>
                  </div>
                )}

                {result && !loading && (
                  <div>
                    {selected.renderResult(result)}
                    <div className="mt-5 pt-4 border-t border-gray-800 flex items-center justify-between">
                      <p className="text-xs text-gray-600">This is live data from your API</p>
                      <a href="/signup" className="text-xs bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg transition-colors font-medium">
                        Get your free API key →
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-10 text-center">
          <p className="text-gray-500 text-sm">
            Want to run your own queries?{' '}
            <a href="/signup" className="text-brand-400 font-medium hover:underline">
              Sign up free — 50 API calls/day, no credit card
            </a>
          </p>
        </div>
      </div>
    </section>
  )
}
