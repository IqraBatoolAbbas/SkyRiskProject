import { useEffect } from 'react'
import AppShell from './layouts/AppShell.jsx'
import LandingPage from './pages/LandingPage.jsx'
import { storageGet } from './utils/format.js'
import { Router, useRouter } from './utils/router.jsx'
import { AuthProvider } from './context/AuthContext.jsx'

function applyDisplayPrefs() {
  const density = storageGet('skyrisk.density', 'comfortable')
  const grid = storageGet('skyrisk.grid', false)
  const glow = storageGet('skyrisk.glow', true)
  document.documentElement.dataset.density = density
  document.documentElement.dataset.grid = grid ? 'on' : 'off'
  document.documentElement.dataset.glow = glow ? 'on' : 'off'
}

function Routes() {
  const { path, navigate } = useRouter()

  if (path === '/' || path === '') {
    return <LandingPage />
  }

  if (path.startsWith('/workspace')) {
    return <AppShell />
  }

  return (
    <div className="content">
      <h1>Page not found</h1>
      <p className="muted">That path is not part of the SkyRisk Auditor prototype.</p>
      <button className="btn btn-primary" onClick={() => navigate('/')}>
        Return to landing page
      </button>
    </div>
  )
}

export default function App() {
  useEffect(() => {
    applyDisplayPrefs()
  }, [])

  return (
    <AuthProvider>
      <Router>
        <Routes />
      </Router>
    </AuthProvider>
  )
}
