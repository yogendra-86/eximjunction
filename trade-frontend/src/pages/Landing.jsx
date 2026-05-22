import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import InteractiveDemo from '../components/InteractiveDemo'

const features = [
  { icon: '🔍', title: 'HS Code Search', desc: 'Find the right product classification instantly. Search by keyword or partial code across all 99 HS chapters.' },
  { icon: '🌍', title: 'Top Trading Partners', desc: 'Discover which countries import or export any product. Ranked by trade value for any year.' },
  { icon: '📈', title: 'Trade Trends', desc: 'Year-over-year trade flow data between any two countries with CAGR calculation built in.' },
  { icon: '💰', title: 'Tariff Rates', desc: 'MFN and preferential duty rates. Instantly see if an FTA like ASEAN-India or USMCA applies.' },
  { icon: '📋', title: 'Compliance Docs', desc: 'Know exactly which certificates and documents are required for any export corridor before you ship.' },
  { icon: '⚡', title: 'Fast REST API', desc: 'JSON responses in milliseconds. Works with any language — Python, JavaScript, PHP, Excel Power Query.' },
]

const useCases = [
  { role: 'Freight Forwarders', desc: 'Look up HS codes and compliance requirements in seconds, right from your TMS.' },
  { role: 'Export Consultants', desc: 'Back your market entry recommendations with real trade data and tariff analysis.' },
  { role: 'Manufacturers', desc: 'Discover new export markets by seeing who imports your product category.' },
  { role: 'Customs Agents', desc: 'Quick tariff classification lookup with MFN and FTA preferential rates.' },
]

const codeExample = `curl "https://api.tradedataapi.in/api/v1/products/090111/top-partners
  ?reporter=IN&flow=export&year=2024&limit=5" \\
  -H "X-API-Key: tdk_YourKeyHere"`

const responseExample = `{
  "hs_code": "090111",
  "hs_description": "Coffee, not roasted",
  "flow_type": "export",
  "reporter": { "name": "India", "iso_alpha2": "IN" },
  "partners": [
    { "rank": 1, "country": { "name": "United States" },
      "value_usd": 1180000000 },
    { "rank": 2, "country": { "name": "Germany" },
      "value_usd": 985000000 }
  ]
}`

export default function Landing() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Hero */}
      <section className="bg-gradient-to-br from-brand-900 via-brand-700 to-brand-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 lg:py-32">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 bg-white/10 text-white/90 text-xs font-medium px-3 py-1.5 rounded-full mb-6">
                🇮🇳 Built for Indian Import-Export Businesses
              </div>
              <h1 className="text-4xl lg:text-5xl font-extrabold leading-tight mb-6">
                Global Trade Data.<br />
                <span className="text-brand-200">One Simple API.</span>
              </h1>
              <p className="text-lg text-white/80 mb-8 leading-relaxed">
                HS codes, trading partners, tariff rates, and compliance documents — all in one REST API. 
                Stop searching government portals. Start querying.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/signup" className="bg-white text-brand-700 hover:bg-brand-50 font-bold py-3 px-8 rounded-lg transition-colors text-center">
                  Start Free — 50 calls/day
                </Link>
                <Link to="/pricing" className="bg-white/10 hover:bg-white/20 text-white font-semibold py-3 px-8 rounded-lg transition-colors text-center border border-white/20">
                  View Pricing
                </Link>
              </div>
              <p className="mt-4 text-sm text-white/60">No credit card required · Free plan forever</p>
            </div>

            {/* Code preview */}
            <div className="hidden lg:block">
              <div className="bg-gray-900 rounded-xl overflow-hidden shadow-2xl">
                <div className="flex items-center gap-1.5 px-4 py-3 bg-gray-800">
                  <span className="w-3 h-3 rounded-full bg-red-500"></span>
                  <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                  <span className="w-3 h-3 rounded-full bg-green-500"></span>
                  <span className="ml-2 text-xs text-gray-400">API Request</span>
                </div>
                <pre className="p-4 text-xs text-green-400 overflow-x-auto leading-relaxed">{codeExample}</pre>
                <div className="border-t border-gray-700 px-4 py-2 text-xs text-gray-500">Response</div>
                <pre className="p-4 text-xs text-blue-300 overflow-x-auto leading-relaxed">{responseExample}</pre>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats bar */}
      <section className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            {[
              { value: '200+', label: 'Countries covered' },
              { value: '5,000+', label: 'HS codes indexed' },
              { value: '6 years', label: 'Historical data' },
              { value: '< 200ms', label: 'Avg. response time' },
            ].map(s => (
              <div key={s.label}>
                <div className="text-2xl font-extrabold text-brand-600">{s.value}</div>
                <div className="text-sm text-gray-500 mt-1">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <InteractiveDemo />
      
      {/* Features */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Everything you need to understand global trade</h2>
            <p className="text-gray-500 max-w-xl mx-auto">Six powerful endpoints. One API key. Query from any language or tool.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map(f => (
              <div key={f.title} className="card hover:shadow-md transition-shadow">
                <div className="text-3xl mb-3">{f.icon}</div>
                <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Up and running in 3 minutes</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', title: 'Sign up free', desc: 'Create your account. No credit card required. Get 50 API calls per day instantly.' },
              { step: '02', title: 'Get your API key', desc: 'From your dashboard, create a named API key. Copy it — shown only once for security.' },
              { step: '03', title: 'Start querying', desc: 'Pass X-API-Key in your header. Get trade data as clean JSON in under 200ms.' },
            ].map(s => (
              <div key={s.step} className="flex gap-5">
                <div className="flex-shrink-0 w-10 h-10 bg-brand-600 text-white rounded-xl flex items-center justify-center font-bold text-sm">
                  {s.step}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">{s.title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Portal CTA */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-6">
            <div className="card hover:shadow-md transition-shadow border-2 border-brand-100">
              <div className="text-3xl mb-3">🌐</div>
              <h3 className="font-bold text-gray-900 mb-2">Trade Data Portal</h3>
              <p className="text-sm text-gray-500 mb-4">
                Browse and download global import-export data. No coding required.
                Search by product, country, and year.
              </p>
              <Link to="/portal/search" className="btn-primary text-sm py-2 inline-block">
                Open Portal →
              </Link>
            </div>
            <div className="card hover:shadow-md transition-shadow border-2 border-green-100">
              <div className="text-3xl mb-3">📋</div>
              <h3 className="font-bold text-gray-900 mb-2">EXIM Documentation</h3>
              <p className="text-sm text-gray-500 mb-4">
                IEC registration, RCMC, AD Code. We handle the paperwork
                so you can focus on your business.
              </p>
              <Link to="/portal/services" className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors text-sm inline-block">
                View Services →
              </Link>
            </div>
            <div className="card hover:shadow-md transition-shadow border-2 border-purple-100">
              <div className="text-3xl mb-3">⚡</div>
              <h3 className="font-bold text-gray-900 mb-2">Trade Data API</h3>
              <p className="text-sm text-gray-500 mb-4">
                REST API for developers. Integrate trade data directly
                into your application or ERP system.
              </p>
              <Link to="/pricing" className="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-6 rounded-lg transition-colors text-sm inline-block">
                View API Plans →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Use cases */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Who uses TradeData API?</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {useCases.map(u => (
              <div key={u.role} className="card text-center">
                <h3 className="font-semibold text-gray-900 mb-2">{u.role}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{u.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-brand-600">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Start querying trade data today</h2>
          <p className="text-brand-100 mb-8">Free plan. No credit card. 50 API calls per day forever.</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/signup" className="bg-white text-brand-700 hover:bg-brand-50 font-bold py-3 px-8 rounded-lg transition-colors">
              Create Free Account
            </Link>
            <Link to="/pricing" className="bg-brand-500 hover:bg-brand-400 text-white font-semibold py-3 px-8 rounded-lg transition-colors border border-brand-400">
              See Pricing
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
