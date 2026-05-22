import { useEffect, useState } from 'react'
import { getKeys, createKey, revokeKey, getKeyUsage } from '../../lib/api'

function KeyRow({ k, onRevoke }) {
  const [usage, setUsage] = useState(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    getKeyUsage(k.id).then(r => setUsage(r.data)).catch(() => {})
  }, [k.id])

  const copy = (text) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const today = usage?.daily?.find(d => d.usage_date === new Date().toISOString().split('T')[0])
  const todayCount = today?.request_count || 0

  return (
    <div className="border border-gray-200 rounded-xl p-4 bg-white">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-gray-900 truncate">{k.name}</span>
            <span className={k.tier === 'paid' ? 'badge-paid' : 'badge-free'}>{k.tier}</span>
            {!k.is_active && <span className="bg-red-100 text-red-600 text-xs font-medium px-2 py-0.5 rounded-full">Revoked</span>}
          </div>

          <div className="flex items-center gap-2 mt-2">
            <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono text-gray-600">
              {k.key_prefix}••••••••••••••••••••
            </code>
            <button
              onClick={() => copy(k.key_prefix)}
              className="text-xs text-brand-600 hover:underline"
            >
              {copied ? '✓ Copied' : 'Copy prefix'}
            </button>
          </div>

          <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
            <span>Created {new Date(k.created_at).toLocaleDateString('en-IN')}</span>
            {k.last_used_at && <span>Last used {new Date(k.last_used_at).toLocaleDateString('en-IN')}</span>}
            {usage && <span>Today: <strong className="text-gray-600">{todayCount}</strong> calls</span>}
            {usage && <span>30-day total: <strong className="text-gray-600">{usage.total_requests_30d}</strong></span>}
          </div>
        </div>

        {k.is_active && (
          <button
            onClick={() => onRevoke(k)}
            className="flex-shrink-0 text-xs text-red-600 hover:text-red-700 border border-red-200 hover:border-red-300 px-3 py-1.5 rounded-lg transition-colors"
          >
            Revoke
          </button>
        )}
      </div>
    </div>
  )
}

export default function APIKeys() {
  const [keys,    setKeys]    = useState([])
  const [name,    setName]    = useState('')
  const [newKey,  setNewKey]  = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState('')

  const load = () => getKeys().then(r => setKeys(r.data || [])).catch(() => {})

  useEffect(() => { load() }, [])

  const handleCreate = async e => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    setError('')
    setNewKey(null)
    try {
      const { data } = await createKey(name.trim())
      setNewKey(data)
      setName('')
      load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create key.')
    } finally {
      setLoading(false)
    }
  }

  const handleRevoke = async (k) => {
    if (!confirm(`Revoke key "${k.name}"? Any apps using it will stop working immediately.`)) return
    try {
      await revokeKey(k.id)
      load()
    } catch {
      alert('Failed to revoke key.')
    }
  }

  const active  = keys.filter(k => k.is_active)
  const revoked = keys.filter(k => !k.is_active)

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">API Keys</h1>
          <p className="text-sm text-gray-500 mt-1">{active.length} active key{active.length !== 1 ? 's' : ''}</p>
        </div>
      </div>

      {/* Create new key */}
      <div className="card mb-8">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Create New Key</h2>
        <form onSubmit={handleCreate} className="flex gap-3">
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            className="input flex-1"
            placeholder="e.g. Production, Mobile App, Testing..."
            maxLength={120}
          />
          <button type="submit" disabled={loading || !name.trim()} className="btn-primary">
            {loading ? 'Creating...' : 'Create Key'}
          </button>
        </form>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

        {/* Show new key once */}
        {newKey && (
          <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-semibold text-green-800">⚠️ Copy your API key now — it won't be shown again</p>
              <button
                onClick={() => { navigator.clipboard.writeText(newKey.plaintext_key) }}
                className="text-xs bg-green-700 text-white px-3 py-1 rounded hover:bg-green-800"
              >
                Copy Key
              </button>
            </div>
            <code className="text-sm font-mono text-green-900 break-all block bg-green-100 p-2 rounded">
              {newKey.plaintext_key}
            </code>
          </div>
        )}
      </div>

      {/* Active keys */}
      <div className="mb-8">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Active Keys ({active.length})</h2>
        {active.length === 0 ? (
          <div className="text-center py-10 bg-white border border-gray-200 rounded-xl text-gray-400 text-sm">
            No active keys. Create one above.
          </div>
        ) : (
          <div className="space-y-3">
            {active.map(k => <KeyRow key={k.id} k={k} onRevoke={handleRevoke} />)}
          </div>
        )}
      </div>

      {/* Revoked keys */}
      {revoked.length > 0 && (
        <div>
          <h2 className="text-base font-semibold text-gray-500 mb-4">Revoked Keys ({revoked.length})</h2>
          <div className="space-y-3 opacity-60">
            {revoked.map(k => <KeyRow key={k.id} k={k} onRevoke={handleRevoke} />)}
          </div>
        </div>
      )}

      {/* How to use */}
      <div className="card mt-8 bg-gray-50">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">How to use your API key</h3>
        <div className="space-y-2">
          <div>
            <p className="text-xs text-gray-500 mb-1">Header (recommended):</p>
            <code className="text-xs bg-gray-800 text-green-400 px-3 py-2 rounded block font-mono">
              X-API-Key: tdk_YourKeyHere
            </code>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Query param (browser testing):</p>
            <code className="text-xs bg-gray-800 text-green-400 px-3 py-2 rounded block font-mono">
              ?api_key=tdk_YourKeyHere
            </code>
          </div>
        </div>
        <p className="text-xs text-gray-400 mt-3">
          Full API documentation at{' '}
          <a href="/docs" target="_blank" className="text-brand-600 hover:underline">/docs</a>
        </p>
      </div>
    </div>
  )
}
