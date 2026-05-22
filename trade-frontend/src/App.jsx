import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { isLoggedIn } from './lib/auth'
import Landing   from './pages/Landing'
import Pricing   from './pages/Pricing'
import Signup    from './pages/Signup'
import Login     from './pages/Login'
import Overview  from './pages/Dashboard/Overview'
import APIKeys   from './pages/Dashboard/APIKeys'
import Billing   from './pages/Dashboard/Billing'
import Explorer  from './pages/Dashboard/Explorer'
import DashLayout from './components/DashLayout'
import PortalSearch  from './pages/Portal/Search'
import PortalResults from './pages/Portal/Results'
import Services      from './pages/Portal/Services'

function Protected({ children }) {
  return isLoggedIn() ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public */}
        <Route path="/"        element={<Landing />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/signup"  element={<Signup />} />
        <Route path="/login"   element={<Login />} />

        {/* Portal routes */}
        <Route path="/portal/search"   element={<PortalSearch />} />
        <Route path="/portal/results"  element={<PortalResults />} />
        <Route path="/portal/services" element={<Services />} />

        {/* Protected dashboard */}
        <Route path="/dashboard" element={<Protected><DashLayout /></Protected>}>
          <Route index           element={<Overview />} />
          <Route path="keys"     element={<APIKeys />} />
          <Route path="billing"  element={<Billing />} />
          <Route path="explorer" element={<Explorer />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
