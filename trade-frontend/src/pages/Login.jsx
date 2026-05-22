import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { login, getMe } from '../lib/api'
import { setAuth } from '../lib/auth'

export default function Login() {
  const navigate = useNavigate()
  const [form,    setForm]    = useState({ email: '', password: '' })
  const [error,   setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const change = e => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await login(form)
      const me = await getMe()
      setAuth(data.access_token, me.data)
      navigate('/dashboard')
    } catch (e) {
      setError(e.response?.data?.detail || 'Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navbar />
      <div className="flex-1 flex items-center justify-center py-12 px-4">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-extrabold text-gray-900">Welcome back</h1>
            <p className="mt-2 text-sm text-gray-500">Log in to your Trade Data API account</p>
          </div>

          <div className="card shadow-md">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
            )}

            <form onSubmit={submit} className="space-y-4">
              <div>
                <label className="label">Email address</label>
                <input name="email" type="email" value={form.email} onChange={change}
                  required className="input" placeholder="you@company.com" autoFocus />
              </div>
              <div>
                <label className="label">Password</label>
                <input name="password" type="password" value={form.password} onChange={change}
                  required className="input" placeholder="Your password" />
              </div>
              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading ? 'Logging in...' : 'Log In'}
              </button>
            </form>

            <p className="mt-5 text-center text-sm text-gray-500">
              Don't have an account?{' '}
              <Link to="/signup" className="text-brand-600 font-medium hover:underline">Sign up free</Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
