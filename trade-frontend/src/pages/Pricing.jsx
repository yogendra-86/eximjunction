import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import { getPlans, checkout, mockSuccess, getSubscription } from '../lib/api'
import { isLoggedIn } from '../lib/auth'

function PlanCard({ plan, current, onUpgrade, loading }) {
  const isPaid    = plan.code !== 'free'
  const isCurrent = current?.plan?.code === plan.code
  const isAnnual  = plan.billing_period === 'annual'

  return (
    <div className={`card flex flex-col relative ${isPaid && !isAnnual ? 'border-2 border-brand-500 shadow-lg' : ''}`}>
      {isPaid && !isAnnual && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-brand-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
          Most Popular
        </div>
      )}
      {isAnnual && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-green-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
          Best Value
        </div>
      )}

      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
          {isCurrent && <span className="badge-paid">Current Plan</span>}
        </div>
        <div className="flex items-end gap-1 mb-1">
          <span className="text-4xl font-extrabold text-gray-900">{plan.price_display?.split('/')[0] || 'Free'}</span>
          {plan.price_inr > 0 && <span className="text-gray-400 text-sm mb-1">/{plan.billing_period === 'annual' ? 'year' : 'month'}</span>}
        </div>
        {isAnnual && <p className="text-xs text-green-600 font-medium">Save ₹3,998 vs monthly</p>}
        <p className="text-sm text-gray-500 mt-2">
          {plan.daily_request_limit
            ? `${plan.daily_request_limit.toLocaleString()} API calls/day`
            : 'Unlimited API calls'}
        </p>
      </div>

      <ul className="space-y-2.5 flex-1 mb-6">
        {(plan.features || []).map((f, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
            <span className="text-green-500 mt-0.5 flex-shrink-0">✓</span>
            {f}
          </li>
        ))}
      </ul>

      <button
        onClick={() => onUpgrade(plan)}
        disabled={loading || isCurrent || plan.price_inr === 0}
        className={`w-full py-2.5 rounded-lg font-semibold text-sm transition-colors ${
          isCurrent
            ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
            : plan.price_inr === 0
            ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
            : isPaid && !isAnnual
            ? 'btn-primary'
            : 'btn-secondary'
        }`}
      >
        {isCurrent
          ? 'Current Plan'
          : plan.price_inr === 0
          ? 'Free Forever'
          : loading
          ? 'Processing...'
          : `Upgrade to ${plan.name}`}
      </button>
    </div>
  )
}

export default function Pricing() {
  const [plans,   setPlans]   = useState([])
  const [current, setCurrent] = useState(null)
  const [loading, setLoading] = useState(false)
  const [msg,     setMsg]     = useState('')
  const navigate = useNavigate()
  const loggedIn = isLoggedIn()

  useEffect(() => {
    getPlans().then(r => setPlans(r.data)).catch(() => {})
    if (loggedIn) getSubscription().then(r => setCurrent(r.data)).catch(() => {})
  }, [loggedIn])

  const handleUpgrade = async (plan) => {
    if (!loggedIn) { navigate('/signup'); return }
    if (plan.price_inr === 0) return

    setLoading(true)
    setMsg('')
    try {
      const { data } = await checkout(plan.code)

      if (data.mock_mode) {
        // Dev mode — simulate payment
        await mockSuccess(data.razorpay_order_id)
        setMsg('✅ Subscription activated! Your API keys have been upgraded.')
        const sub = await getSubscription()
        setCurrent(sub.data)
      } else {
        // Real Razorpay checkout
        const options = {
          key:         data.razorpay_key_id,
          amount:      data.amount_paise,
          currency:    data.currency,
          order_id:    data.razorpay_order_id,
          name:        'Trade Data API',
          description: `${data.plan_name} subscription`,
          prefill: {
            email: data.customer_email,
            name:  data.customer_name || '',
            contact: data.customer_phone || '',
          },
          theme: { color: '#2563eb' },
          handler: async (response) => {
            try {
              const { verifyPayment } = await import('../lib/api')
              await verifyPayment({
                razorpay_order_id:   response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature:  response.razorpay_signature,
              })
              setMsg('✅ Payment successful! Your subscription is now active.')
              const sub = await getSubscription()
              setCurrent(sub.data)
            } catch {
              setMsg('⚠️ Payment received but verification failed. Please contact support.')
            }
          },
        }
        const rzp = new window.Razorpay(options)
        rzp.open()
      }
    } catch (e) {
      setMsg('❌ Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Show monthly plans first, then annual
  const monthly = plans.filter(p => p.billing_period === 'monthly')
  const annual  = plans.filter(p => p.billing_period === 'annual' && p.price_inr > 0)

  return (
    <div className="min-h-screen flex flex-col">
      {/* Load Razorpay script */}
      {!document.getElementById('rzp-script') && (() => {
        const s = document.createElement('script')
        s.id  = 'rzp-script'
        s.src = 'https://checkout.razorpay.com/v1/checkout.js'
        document.head.appendChild(s)
        return null
      })()}

      <Navbar />

      <div className="flex-1 py-16 bg-gray-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-extrabold text-gray-900 mb-3">Simple, transparent pricing</h1>
            <p className="text-gray-500 text-lg">Start free. Upgrade when you need more.</p>
          </div>

          {msg && (
            <div className={`mb-8 p-4 rounded-lg text-sm font-medium text-center ${
              msg.startsWith('✅') ? 'bg-green-50 text-green-800 border border-green-200' :
              msg.startsWith('⚠') ? 'bg-yellow-50 text-yellow-800 border border-yellow-200' :
              'bg-red-50 text-red-800 border border-red-200'
            }`}>
              {msg}
            </div>
          )}

          {/* Monthly plans */}
          <div className="grid md:grid-cols-2 gap-8 mb-10">
            {monthly.map(p => (
              <PlanCard key={p.code} plan={p} current={current} onUpgrade={handleUpgrade} loading={loading} />
            ))}
          </div>

          {/* Annual plans */}
          {annual.length > 0 && (
            <>
              <h2 className="text-center text-lg font-semibold text-gray-700 mb-6">Annual Plans — Save 2 months</h2>
              <div className="grid md:grid-cols-1 max-w-sm mx-auto gap-6 mb-12">
                {annual.map(p => (
                  <PlanCard key={p.code} plan={p} current={current} onUpgrade={handleUpgrade} loading={loading} />
                ))}
              </div>
            </>
          )}

          {/* FAQ */}
          <div className="max-w-2xl mx-auto mt-12">
            <h2 className="text-xl font-bold text-gray-900 mb-6 text-center">Common questions</h2>
            <div className="space-y-4">
              {[
                { q: 'What counts as an API call?', a: 'Each request to a data endpoint (products, tariffs, trade-flows, compliance, countries) counts as one call. Auth and billing endpoints are free.' },
                { q: 'When does the daily limit reset?', a: 'At 00:00 UTC every day (5:30 AM IST).' },
                { q: 'Can I cancel anytime?', a: 'Yes. You keep access until the end of your billing period. No penalties.' },
                { q: 'Do you provide GST invoices?', a: 'Yes. A GST invoice is generated automatically for every payment and available in your billing dashboard.' },
                { q: 'What payment methods are accepted?', a: 'UPI, Net Banking, Credit/Debit Cards (including RuPay), and EMI — all via Razorpay.' },
              ].map(({ q, a }) => (
                <details key={q} className="card cursor-pointer group">
                  <summary className="font-medium text-gray-900 cursor-pointer list-none flex justify-between items-center">
                    {q}
                    <span className="text-gray-400 group-open:rotate-180 transition-transform">▾</span>
                  </summary>
                  <p className="mt-3 text-sm text-gray-500 leading-relaxed">{a}</p>
                </details>
              ))}
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  )
}
