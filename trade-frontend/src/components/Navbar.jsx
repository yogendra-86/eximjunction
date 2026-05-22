import { Link, useNavigate } from 'react-router-dom'
import { isLoggedIn, clearAuth } from '../lib/auth'

export default function Navbar() {
  const navigate  = useNavigate()
  const loggedIn  = isLoggedIn()

  const logout = () => {
    clearAuth()
    navigate('/')
  }

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">T</span>
            </div>
            <span className="font-bold text-gray-900 text-lg">TradeData<span className="text-brand-600">API</span></span>
          </Link>

          {/* Nav links */}
          <div className="hidden md:flex items-center gap-6">
            <Link to="/portal/search" className="text-sm text-gray-600 hover:text-gray-900 font-medium">Data Portal</Link>
            <Link to="/pricing" className="text-sm text-gray-600 hover:text-gray-900 font-medium">Pricing</Link>
            <Link to="/portal/services" className="text-sm text-gray-600 hover:text-gray-900 font-medium">EXIM Services</Link>
            <a href={`${import.meta.env.VITE_API_BASE_URL}/docs`} target="_blank" rel="noreferrer" className="text-sm text-gray-600 hover:text-gray-900 font-medium">API Docs</a>

          {/* Auth */}
          <div className="flex items-center gap-3">
            {loggedIn ? (
              <>
                <Link to="/dashboard" className="btn-secondary text-sm py-2 px-4">Dashboard</Link>
                <button onClick={logout} className="btn-outline text-sm">Logout</button>
              </>
            ) : (
              <>
                <Link to="/login"  className="text-sm text-gray-600 hover:text-gray-900 font-medium">Login</Link>
                <Link to="/signup" className="btn-primary text-sm py-2 px-4">Get Started Free</Link>
              </>
            )}
          </div>
        </div>
      </div>
      </div>
    </nav>
  )
}
