import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { getSubscription, getKeys, getKeyUsage } from '../../lib/api'
import { getUser } from '../../lib/auth'

function StatCard({ label, value, sub, color = 'brand' }) {
  return (
    <div className="card">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`text-2xl font-bold mt-1 text-${color}-600`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  )
}

export default function Overview() {
  const user             = getUser()
  const [sub,     setSub]     = useState(null)
  const [keys,    setKeys]    = useState([])
  const [usage,   setUsage]   = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getSubscription().then(r => setSub(r.data)).catch(() => {}),
      getKeys().then(r => setKeys(r.data || [])).catch(() => {}),
    ]).finally(() => setLoading(false))
  }, [])

  // Load usage for first active key
  useEffect(() => {
    const first = keys.find(k => k.is_active)
    if (first) {
      getKeyUsage(first.id).then(r => setUsage(r.data?.daily || [])).catch(() => {})
    }
  }, [keys])

  const activeKeys  = keys.filter(k => k.is_active).length
  const totalToday  = usage.find(u => u.usage_date === new Date().toISOString().split('T')[0])?.request_count || 0
  const totalMonth  = usage.reduce((s, u) => s + u.request_count, 0)
  const dailyLimit  = sub?.plan?.daily_request_limit || 50
  const pctUsed     = dailyLimit ? Math.round((totalToday / dailyLimit) * 100) : 0

  // Last 14 days for chart
  const chartData = (() => {
    const days = []
    for (let i = 13; i >= 0; i--) {
      const d = new Date(); d.setDate(d.getDate() - i)
      const ds = d.toISOString().split('T')[0]
      const found = usage.find(u => u.usage_date === ds)
      days.push({ date: ds.slice(5), calls: found?.request_count || 0 })
    }
    return days
  })()

  if (loading) return (
    <div className="p-8 flex items-center justify-center h-full">
      <div className="text-gray-400">Loading...</div>
    </div>
  )

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''} 👋
          </h1>
          <p className="text-sm text-gray-500 mt-1">{user?.company_name || user?.email}</p>
        </div>
        {sub?.plan?.code === 'free' && (
          <Link to="/pricing" className="btn-primary text-sm">
            Upgrade to Paid ↗
          </Link>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Current Plan" value={sub?.plan?.name || 'Free'} sub={sub?.plan?.price_display} />
        <StatCard label="Today's Calls" value={totalToday} sub={`of ${dailyLimit} daily limit`} color={pctUsed > 80 ? 'red' : 'brand'} />
        <StatCard label="Calls This Month" value={totalMonth} sub="last 30 days" color="green" />
        <StatCard label="Active API Keys" value={activeKeys} sub="keys in use" color="purple" />
      </div>

      {/* Daily limit bar */}
      <div className="card mb-8">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">Today's usage</span>
          <span className="text-sm text-gray-500">{totalToday} / {dailyLimit} calls ({pctUsed}%)</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all ${pctUsed > 80 ? 'bg-red-500' : pctUsed > 50 ? 'bg-yellow-500' : 'bg-brand-600'}`}
            style={{ width: `${Math.min(pctUsed, 100)}%` }}
          />
        </div>
        {pctUsed > 80 && (
          <p className="mt-2 text-xs text-red-600">
            ⚠️ Approaching daily limit.{' '}
            <Link to="/pricing" className="underline font-medium">Upgrade for 10,000 calls/day</Link>
          </p>
        )}
      </div>

      {/* Usage chart */}
      <div className="card mb-8">
        <h2 className="text-base font-semibold text-gray-900 mb-4">API Calls — Last 14 Days</h2>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} />
            <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
              formatter={(v) => [`${v} calls`, 'API Calls']}
            />
            <Bar dataKey="calls" fill="#2563eb" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Quick links */}
      <div className="grid sm:grid-cols-3 gap-4">
        {[
          { to: '/dashboard/keys',     icon: '🔑', title: 'Manage API Keys',    desc: 'Create, view, and revoke your API keys' },
          { to: '/dashboard/billing',  icon: '💳', title: 'Billing & Plans',    desc: 'Upgrade your plan or view payment history' },
          { to: '/dashboard/explorer', icon: '🔍', title: 'API Explorer',       desc: 'Test queries live against the trade database' },
        ].map(q => (
          <Link key={q.to} to={q.to} className="card hover:shadow-md transition-shadow group">
            <div className="text-2xl mb-2">{q.icon}</div>
            <div className="font-semibold text-gray-900 group-hover:text-brand-600 transition-colors">{q.title}</div>
            <div className="text-xs text-gray-400 mt-1">{q.desc}</div>
          </Link>
        ))}
      </div>
    </div>
  )
}
