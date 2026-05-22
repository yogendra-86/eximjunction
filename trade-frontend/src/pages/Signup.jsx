import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { signup } from '../lib/api'
import { setAuth } from '../lib/auth'

export default function Signup() {
  const navigate = useNavigate()
  const [form,    setForm]    = useState({ email: '', password: '', full_name: '', company_name: '', phone: '' })
  const [error,   setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const change = e => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async e => {
    e.preventDefault()
    setError('')
    if (form.password.length < 8) { setError('Password must be at least 8 characters.'); return }

    setLoading(true)
    try {
      const { data } = await signup(form)
      // Fetch user profile
      const { getMe } = await import('../lib/api')
      const me = await getMe()
      setAuth(data.access_token, me.data)
      navigate('/dashboard')
    } catch (e) {
      const msg = e.response?.data?.detail
      if (msg?.includes('already registered')) setError('This email is already registered. Try logging in.')
      else setError(msg || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navbar />
      <div className="flex-1 flex items-center justify-center py-12 px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-extrabold text-gray-900">Create your account</h1>
            <p className="mt-2 text-sm text-gray-500">Free plan · 50 API calls/day · No credit card</p>
          </div>

          <div className="card shadow-md">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
            )}

            <form onSubmit={submit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Full Name</label>
                  <input name="full_name" value={form.full_name} onChange={change}
                    className="input" placeholder="Rajesh Kumar" />
                </div>
                <div>
                  <label className="label">Phone</label>
                  <input name="phone" value={form.phone} onChange={change}
                    className="input" placeholder="+91-98765..." />
                </div>
              </div>

              <div>
                <label className="label">Company Name</label>
                <input name="company_name" value={form.company_name} onChange={change}
                  className="input" placeholder="Kumar Exports Pvt Ltd" />
              </div>

              <div>
                <label className="label">Email address <span className="text-red-500">*</span></label>
                <input name="email" type="email" value={form.email} onChange={change}
                  required className="input" placeholder="you@company.com" />
              </div>

              <div>
                <label className="label">Password <span className="text-red-500">*</span></label>
                <input name="password" type="password" value={form.password} onChange={change}
                  required minLength={8} className="input" placeholder="Min. 8 characters" />
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full mt-2">
                {loading ? 'Creating account...' : 'Create Free Account'}
              </button>
            </form>

            <p className="mt-5 text-center text-sm text-gray-500">
              Already have an account?{' '}
              <Link to="/login" className="text-brand-600 font-medium hover:underline">Log in</Link>
            </p>
          </div>

          <p className="mt-4 text-center text-xs text-gray-400">
            By signing up, you agree to our{' '}
            <Link to="/terms" className="underline">Terms</Link> and{' '}
            <Link to="/privacy" className="underline">Privacy Policy</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
