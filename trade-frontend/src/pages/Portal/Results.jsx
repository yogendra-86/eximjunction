import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import Navbar from '../../components/Navbar'
import Footer from '../../components/Footer'
import axios from 'axios'

export default function PortalResults() {
  const navigate  = useNavigate()
  const [data,    setData]    = useState(null)
  const [params,  setParams]  = useState(null)
  const [sortKey, setSortKey] = useState('value_usd')
  const [sortDir, setSortDir] = useState('desc')
  const [exporting, setExporting] = useState(false)
  const [exportMsg, setExportMsg] = useState('')

  useEffect(() => {
    const raw    = sessionStorage.getItem('portal_results')
    const rawP   = sessionStorage.getItem('portal_params')
    if (!raw) { navigate('/portal/search'); return }
    setData(JSON.parse(raw))
    if (rawP) setParams(JSON.parse(rawP))
  }, [navigate])

  if (!data) return null

  const sorted = [...(data.results || [])].sort((a, b) => {
    const av = a[sortKey], bv = b[sortKey]
    if (typeof av === 'number') return sortDir === 'desc' ? bv - av : av - bv
    return sortDir === 'desc' ? String(bv).localeCompare(String(av)) : String(av).localeCompare(String(bv))
  })

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const SortIcon = ({ k }) => sortKey !== k ? ' â†•' : sortDir === 'desc' ? ' â†“' : ' â†‘'

  const handleExport = async () => {
    if (!data.can_export) return
    setExporting(true); setExportMsg('')
    try {
      const token = localStorage.getItem('token')
      const res = await axios.get('/api/v1/portal/export', {
        params: {
          hs_code: params?.hs_code || undefined,
          reporter: params?.reporter || undefined,
          partner: params?.partner || undefined,
          flow: params?.flow || 'export',
          year_from: params?.year_from || 2019,
          year_to: params?.year_to || 2024,
          format: 'csv',
        },
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      })
      // Trigger download
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `eximjunction_${params?.hs_code || "data"}_${params?.reporter || "global"}_${params?.flow || "export"}_${params?.year_to || "2024"}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
      setExportMsg('âœ… Download started')
    } catch (e) {
      setExportMsg(e.response?.data?.detail || 'âŒ Export failed')
    } finally {
      setExporting(false)
    }
  }

  // Chart data â€” top 10 by value for the chart
  const chartData = sorted.slice(0, 10).map(r => ({
    name: r.reporter_name?.split(' ').slice(0, 2).join(' ') || r.reporter_iso,
    value: parseFloat((r.value_usd / 1e9).toFixed(2)),
  }))

  const fmt = (v) => {
    if (v >= 1e9) return `$${(v / 1e9).toFixed(2)}B`
    if (v >= 1e6) return `$${(v / 1e6).toFixed(1)}M`
    return `$${v.toLocaleString()}`
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navbar />
      <div className="flex-1 py-8 px-4">
        <div className="max-w-7xl mx-auto">

          {/* Header */}
          <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <Link to="/portal/search" className="text-sm text-brand-600 hover:underline">
                  â† Back to search
                </Link>
                <span className="text-gray-300">|</span>
                <span className="text-sm text-gray-500">{data.count} records shown Â· Plan: {data.plan}</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">
                {params?.hs_code && <span className="text-brand-600">HS {params.hs_code}</span>}
                {params?.reporter && ` Â· ${params.reporter}`}
                {' '}Trade Data {params?.year_from}â€“{params?.year_to}
              </h1>
            </div>

            <div className="flex items-center gap-3">
              {data.can_export ? (
                <div>
                  <button
                    onClick={handleExport}
                    disabled={exporting}
                    className="btn-primary flex items-center gap-2"
                  >
                    {exporting ? 'â³ Exporting...' : 'â¬‡ Download CSV'}
                  </button>
                  {exportMsg && <p className="text-xs mt-1 text-center">{exportMsg}</p>}
                </div>
              ) : (
                <Link
                  to="/portal/plans"
                  className="btn-secondary flex items-center gap-2 text-sm"
                >
                  â¬‡ Download CSV â€” Upgrade
                </Link>
              )}
            </div>
          </div>

          {/* Free tier notice */}
          {data.has_more && (
            <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-amber-800">
                  âš ï¸ Showing {data.tier_limit} of many more records
                </p>
                <p className="text-xs text-amber-700 mt-0.5">
                  Your {data.plan} plan shows {data.tier_limit} records per search. Upgrade to see all results and download CSV.
                </p>
              </div>
              <Link to="/portal/plans" className="flex-shrink-0 btn-primary text-sm ml-4">
                Upgrade Plan
              </Link>
            </div>
          )}

          {/* Chart */}
          {chartData.length > 0 && (
            <div className="card mb-6">
              <h2 className="text-base font-semibold text-gray-900 mb-4">
                Top countries by trade value (USD Billions)
              </h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} unit="B" />
                  <Tooltip
                    formatter={(v) => [`$${v}B`, 'Trade Value']}
                    contentStyle={{ fontSize: 12, borderRadius: 8 }}
                  />
                  <Bar dataKey="value" fill="#2563eb" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Results table */}
          <div className="card overflow-hidden p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-900 text-white">
                    {[
                      { key: 'hs_code',       label: 'HS Code' },
                      { key: 'reporter_name', label: 'Reporter' },
                      { key: 'year',          label: 'Year' },
                      { key: 'flow_type',     label: 'Flow' },
                      { key: 'value_usd',     label: 'Value (USD)' },
                      { key: 'quantity',      label: 'Quantity' },
                    ].map(col => (
                      <th
                        key={col.key}
                        onClick={() => toggleSort(col.key)}
                        className="px-4 py-3 text-left text-xs font-semibold cursor-pointer hover:bg-gray-800 select-none"
                      >
                        {col.label}<SortIcon k={col.key} />
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {sorted.map((row, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-3 font-mono text-xs text-brand-700 font-semibold">
                        <Link to={`/portal/product/${row.hs_code}`} className="hover:underline">
                          {row.hs_code}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-gray-900">{row.reporter_name}</td>
                      <td className="px-4 py-3 text-gray-600">{row.year}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                          row.flow_type === 'export'
                            ? 'bg-green-100 text-green-700'
                            : 'bg-blue-100 text-blue-700'
                        }`}>
                          {row.flow_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-semibold text-gray-900">{fmt(row.value_usd)}</td>
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {row.quantity ? `${row.quantity.toLocaleString()} ${row.quantity_unit || ''}` : 'â€”'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Upgrade CTA */}
          {!data.can_export && (
            <div className="mt-6 p-6 bg-brand-600 rounded-xl text-white text-center">
              <h3 className="text-lg font-bold mb-2">Want the full dataset?</h3>
              <p className="text-brand-100 text-sm mb-4">
                Upgrade to Starter (â‚¹999/month) to see 500 records per search and download CSV files.
              </p>
              <Link to="/portal/plans" className="inline-block bg-white text-brand-700 font-bold py-2.5 px-8 rounded-lg hover:bg-brand-50 transition-colors">
                View Plans
              </Link>
            </div>
          )}
        </div>
      </div>
      <Footer />
    </div>
  )
}
