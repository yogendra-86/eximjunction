import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-400 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-7 h-7 bg-brand-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xs">T</span>
              </div>
              <span className="font-bold text-white text-base">TradeDataAPI</span>
            </div>
            <p className="text-sm leading-relaxed max-w-xs">
              India's import-export intelligence platform. Programmatic access to global trade data for businesses, consultants, and developers.
            </p>
          </div>

          <div>
            <h4 className="text-white font-semibold text-sm mb-3">Product</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/pricing" className="hover:text-white transition-colors">Pricing</Link></li>
              <li><a href="/docs" className="hover:text-white transition-colors">API Docs</a></li>
              <li><a href="/redoc" className="hover:text-white transition-colors">Reference</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold text-sm mb-3">Company</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="mailto:support@tradedataapi.in" className="hover:text-white transition-colors">Support</a></li>
              <li><Link to="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link></li>
              <li><Link to="/terms" className="hover:text-white transition-colors">Terms of Service</Link></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 flex flex-col sm:flex-row justify-between items-center gap-2">
          <p className="text-xs">© {new Date().getFullYear()} TradeData API. All rights reserved. Made in India 🇮🇳</p>
          <p className="text-xs">GST invoices provided for all payments</p>
        </div>
      </div>
    </footer>
  )
}
