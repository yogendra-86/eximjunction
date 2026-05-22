import { useState } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../../components/Navbar'
import Footer from '../../components/Footer'
import axios from 'axios'

const SERVICES = [
  {
    code: 'iec', icon: '🏛️', name: 'IEC Registration', price: '₹2,999',
    delivery: '3–5 working days',
    description: 'Importer Exporter Code — mandatory for all import/export activities in India.',
    details: ['File application on DGFT portal', 'Follow up with department', 'Delivery of IEC certificate by email', 'Government fee of ₹500 included'],
    popular: true,
  },
  {
    code: 'rcmc', icon: '📜', name: 'RCMC Registration', price: '₹3,999',
    delivery: '7–15 working days',
    description: 'Registration Cum Membership Certificate — required to claim export incentives under Foreign Trade Policy.',
    details: ['Register with appropriate Export Promotion Council', 'Helps claim MEIS/RoDTEP benefits', 'Valid for 5 years', 'Council membership fee included where applicable'],
  },
  {
    code: 'ad_code', icon: '🏦', name: 'AD Code Registration', price: '₹1,999',
    delivery: '3–5 working days',
    description: 'Authorised Dealer Code — required for direct bank remittances on exports. Linked to your bank account.',
    details: ['Register with your bank\'s international department', 'Required for ICEGATE registration', 'Enables direct export proceeds to your account', 'Documentation support included'],
  },
  {
    code: 'bundle', icon: '📦', name: 'Export Documentation Bundle', price: '₹9,999',
    delivery: '15 working days',
    description: 'Complete package for new exporters — IEC + RCMC + AD Code registration plus a 1-hour consultation call.',
    details: ['IEC Registration', 'RCMC Registration', 'AD Code Registration', '1-hour video consultation', 'All government fees included', 'Best value for new exporters'],
    badge: 'Best Value',
  },
  {
    code: 'retainer', icon: '🤝', name: 'Monthly Compliance Retainer', price: '₹4,999/month',
    delivery: 'Ongoing support',
    description: 'Ongoing export compliance support — amendments, renewals, document queries, and regulatory updates.',
    details: ['IEC/RCMC amendments and renewals', 'Regulatory updates and advisory', 'Document query resolution within 48h', 'Priority support via WhatsApp'],
  },
]

export default function Services() {
  const [selected, setSelected] = useState(null)
  const [form, setForm]         = useState({ applicant_name: '', company_name: '', pan_number: '', mobile: '', notes: '' })
  const [loading, setLoading]   = useState(false)
  const [success, setSuccess]   = useState(null)
  const [error,   setError]     = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const submit = async (e) => {
    e.preventDefault()
    if (!selected) return
    setLoading(true); setError('')
    try {
      const token = localStorage.getItem('token')
      if (!token) { window.location.href = '/login'; return }
      const res = await axios.post('/api/v1/portal/services/request', null, {
        params: { service_type: selected, ...form },
        headers: { Authorization: `Bearer ${token}` },
      })
      setSuccess(res.data)
      setSelected(null)
      setForm({ applicant_name: '', company_name: '', pan_number: '', mobile: '', notes: '' })
    } catch (e) {
      setError(e.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Navbar />

      <div className="flex-1 py-12 px-4">
        <div className="max-w-5xl mx-auto">

          {/* Header */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 bg-green-50 text-green-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-4">
              📋 EXIM Documentation Services
            </div>
            <h1 className="text-4xl font-extrabold text-gray-900 mb-3">
              We handle your EXIM paperwork
            </h1>
            <p className="text-gray-500 max-w-xl mx-auto">
              Fixed fee. No surprises. Our team files your IEC, RCMC, and AD Code registrations with the government on your behalf.
            </p>
          </div>

          {/* Success message */}
          {success && (
            <div className="mb-8 p-6 bg-green-50 border border-green-200 rounded-xl">
              <h3 className="font-bold text-green-800 text-lg mb-2">✅ Request submitted successfully!</h3>
              <p className="text-green-700 text-sm">{success.message}</p>
              <p className="text-green-600 text-xs mt-2">Reference ID: #{success.id}</p>
            </div>
          )}

          {/* Service cards */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            {SERVICES.map(svc => (
              <div
                key={svc.code}
                className={`card relative flex flex-col cursor-pointer transition-all hover:shadow-md ${
                  selected === svc.code ? 'border-2 border-brand-500 shadow-md' : ''
                }`}
                onClick={() => setSelected(svc.code === selected ? null : svc.code)}
              >
                {svc.popular && (
                  <div className="absolute -top-3 left-4 bg-brand-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                    Most Popular
                  </div>
                )}
                {svc.badge && (
                  <div className="absolute -top-3 left-4 bg-green-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
                    {svc.badge}
                  </div>
                )}
                <div className="text-3xl mb-3">{svc.icon}</div>
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-bold text-gray-900">{svc.name}</h3>
                </div>
                <p className="text-2xl font-extrabold text-brand-600 mb-1">{svc.price}</p>
                <p className="text-xs text-gray-400 mb-3">⏱ {svc.delivery}</p>
                <p className="text-sm text-gray-500 mb-4 leading-relaxed">{svc.description}</p>
                <ul className="space-y-1.5 flex-1 mb-5">
                  {svc.details.map((d, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-gray-500">
                      <span className="text-green-500 mt-0.5 flex-shrink-0">✓</span>
                      {d}
                    </li>
                  ))}
                </ul>
                <button
                  onClick={(e) => { e.stopPropagation(); setSelected(svc.code) }}
                  className={`w-full py-2.5 rounded-lg font-semibold text-sm transition-colors ${
                    selected === svc.code
                      ? 'bg-brand-600 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-brand-50 hover:text-brand-700'
                  }`}
                >
                  {selected === svc.code ? '✓ Selected' : `Request — ${svc.price}`}
                </button>
              </div>
            ))}
          </div>

          {/* Request form */}
          {selected && (
            <div className="card max-w-2xl mx-auto shadow-lg">
              <h2 className="text-xl font-bold text-gray-900 mb-1">
                Request: {SERVICES.find(s => s.code === selected)?.name}
              </h2>
              <p className="text-sm text-gray-500 mb-6">
                Fill in your details. Our team will contact you within 24 hours.
              </p>

              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>
              )}

              <form onSubmit={submit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Applicant Name *</label>
                    <input required value={form.applicant_name} onChange={e => set('applicant_name', e.target.value)}
                      className="input" placeholder="Rajesh Kumar" />
                  </div>
                  <div>
                    <label className="label">Company Name *</label>
                    <input required value={form.company_name} onChange={e => set('company_name', e.target.value)}
                      className="input" placeholder="Kumar Exports Pvt Ltd" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">PAN Number *</label>
                    <input required value={form.pan_number} onChange={e => set('pan_number', e.target.value.toUpperCase())}
                      className="input font-mono" placeholder="ABCDE1234F" maxLength={10} />
                  </div>
                  <div>
                    <label className="label">Mobile Number *</label>
                    <input required value={form.mobile} onChange={e => set('mobile', e.target.value)}
                      className="input" placeholder="+91-98765-43210" />
                  </div>
                </div>
                <div>
                  <label className="label">Additional Notes</label>
                  <textarea value={form.notes} onChange={e => set('notes', e.target.value)}
                    className="input h-24 resize-none" placeholder="Any specific requirements or questions..." />
                </div>

                <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
                  <strong>What happens next:</strong> We'll call you within 24 hours to collect remaining documents
                  (Aadhaar, cancelled cheque, photos) and process payment securely via Razorpay.
                  No payment is taken at this step.
                </div>

                <div className="flex gap-3">
                  <button type="submit" disabled={loading} className="btn-primary flex-1">
                    {loading ? 'Submitting...' : `Submit Request — ${SERVICES.find(s => s.code === selected)?.price}`}
                  </button>
                  <button type="button" onClick={() => setSelected(null)} className="btn-outline">
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Trust signals */}
          <div className="mt-12 grid sm:grid-cols-3 gap-6">
            {[
              { icon: '🔒', title: 'Secure & Confidential', desc: 'Your documents are handled securely. Never shared with third parties.' },
              { icon: '✅', title: 'Government Compliance', desc: 'All filings done on official DGFT and bank portals. 100% compliant.' },
              { icon: '📞', title: '24h Response', desc: 'Our team responds within 24 business hours after submission.' },
            ].map(t => (
              <div key={t.title} className="card text-center">
                <div className="text-3xl mb-2">{t.icon}</div>
                <h3 className="font-semibold text-gray-900 mb-1">{t.title}</h3>
                <p className="text-sm text-gray-500">{t.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  )
}
