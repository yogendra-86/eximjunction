import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getSubscription, getPayments, getPlans, checkout, mockSuccess } from '../../lib/api'

export default function Billing() {
  const [sub,      setSub]      = useState(null)
  const [payments, setPayments] = useState([])
  const [plans,    setPlans]    = useState([])
  const [loading,  setLoading]  = useState(true)
  const [upgrading, setUpgrading] = useState(false)
  const [msg,      setMsg]      = useState('')

  const load = async () => {
    setLoading(true)
    await Promise.all([
      getSubscription().then(r => setSub(r.data)).catch(() => {}),
      getPayments().then(r => setPayments(r.data || [])).catch(() => {}),
      getPlans().then(r => setPlans(r.data || [])).catch(() => {}),
    ])
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const handleUpgrade = async (plan) => {
    setUpgrading(true)
    setMsg('')
    try {
      const { data } = await checkout(plan.code)
      if (data.mock_mode) {
        await mockSuccess(data.razorpay_order_id)
        setMsg('✅ Subscription upgraded successfully!')
        await load()
      } else {
        const options = {
          key: data.razorpay_key_id,
          amount: data.amount_paise,
          currency: data.currency,
          order_id: data.razorpay_order_id,
          name: 'Trade Data API',
          description: `${data.plan_name} Plan`,
          prefill: { email: data.customer_email },
          theme: { color: '#2563eb' },
          handler: async (response) => {
            const { verifyPayment } = await import('../../lib/api')
            await verifyPayment({
              razorpay_order_id:   response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature:  response.razorpay_signature,
            })
            setMsg('✅ Payment successful!')
            await load()
          },
        }
        new window.Razorpay(options).open()
      }
    } catch {
      setMsg('❌ Something went wrong. Please try again.')
    } finally {
      setUpgrading(false)
    }
  }

  if (loading) return <div className="p-8 text-gray-400">Loading...</div>

  const isPaid   = sub?.plan?.code !== 'free'
  const paidPlans = plans.filter(p => p.price_inr > 0 && p.billing_period === 'monthly')

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Billing & Plans</h1>

      {msg && (
        <div className={`mb-6 p-4 rounded-lg text-sm font-medium ${
          msg.startsWith('✅') ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
        }`}>{msg}</div>
      )}

      {/* Current subscription */}
      <div className="card mb-8">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Current Subscription</h2>
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-lg font-bold text-gray-900">{sub?.plan?.name || 'Free'}</span>
              <span className={isPaid ? 'badge-paid' : 'badge-free'}>{sub?.status || 'active'}</span>
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {sub?.plan?.price_display || 'Free forever'} ·{' '}
              {sub?.plan?.daily_request_limit
                ? `${sub.plan.daily_request_limit.toLocaleString()} calls/day`
                : 'Unlimited calls'}
            </p>
            {sub?.current_period_end && isPaid && (
              <p className="text-xs text-gray-400 mt-1">
                Renews {new Date(sub.current_period_end).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
              </p>
            )}
          </div>
          {!isPaid && (
            <Link to="/pricing" className="btn-primary text-sm">
              Upgrade Plan
            </Link>
          )}
        </div>
      </div>

      {/* Upgrade options (only show if on free) */}
      {!isPaid && paidPlans.length > 0 && (
        <div className="card mb-8">
          <h2 className="text-base font-semibold text-gray-900 mb-4">Available Plans</h2>
          <div className="space-y-3">
            {paidPlans.map(plan => (
              <div key={plan.code} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-brand-300 transition-colors">
                <div>
                  <p className="font-semibold text-gray-900">{plan.name}</p>
                  <p className="text-sm text-gray-500">{plan.price_display} · {plan.daily_request_limit?.toLocaleString()} calls/day</p>
                </div>
                <button
                  onClick={() => handleUpgrade(plan)}
                  disabled={upgrading}
                  className="btn-primary text-sm py-2"
                >
                  {upgrading ? 'Processing...' : `Upgrade — ${plan.price_display}`}
                </button>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-3 text-center">
            <Link to="/pricing" className="hover:underline text-brand-600">View all plans including annual discounts →</Link>
          </p>
        </div>
      )}

      {/* Payment history */}
      <div className="card">
        <h2 className="text-base font-semibold text-gray-900 mb-4">Payment History</h2>
        {payments.length === 0 ? (
          <div className="text-center py-10 text-gray-400 text-sm">No payments yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left text-xs font-medium text-gray-500 pb-3">Date</th>
                  <th className="text-left text-xs font-medium text-gray-500 pb-3">Amount</th>
                  <th className="text-left text-xs font-medium text-gray-500 pb-3">Status</th>
                  <th className="text-left text-xs font-medium text-gray-500 pb-3">Reference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {payments.map(p => (
                  <tr key={p.id}>
                    <td className="py-3 text-gray-600">
                      {new Date(p.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                    </td>
                    <td className="py-3 font-medium text-gray-900">
                      ₹{(p.amount_paise / 100).toLocaleString('en-IN')}
                    </td>
                    <td className="py-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                        p.status === 'captured' ? 'bg-green-100 text-green-700' :
                        p.status === 'failed'   ? 'bg-red-100 text-red-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="py-3 text-gray-400 font-mono text-xs truncate max-w-32">
                      {p.razorpay_payment_id || p.razorpay_order_id || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <p className="mt-4 text-xs text-gray-400">
          GST invoices are emailed to your registered address after each payment.
        </p>
      </div>
    </div>
  )
}
