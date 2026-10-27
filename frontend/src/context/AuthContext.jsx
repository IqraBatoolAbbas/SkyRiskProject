import { createContext, useContext, useState, useEffect } from 'react'

const DEFAULT_USERS = [
  {
    id: 1,
    username: 'dispatcher_ayesha',
    fullName: 'Ayesha Rahman',
    role: 'flight_dispatcher',
    roleTitle: 'Flight Dispatcher',
    badgeTone: 'info',
    dispatcherId: 'DISP-PK-891',
    description: 'Authorized for flight plan submission, recovery route selection, and final OFP dispatch release.',
    permissions: ['create_flight', 'trigger_recovery', 'approve_route', 'reject_route', 'sign_ofp'],
  },
  {
    id: 2,
    username: 'safety_tariq',
    fullName: 'Tariq Mehmood',
    role: 'safety_analyst',
    roleTitle: 'Aviation Safety Analyst',
    badgeTone: 'elevated',
    dispatcherId: 'SAFE-ANA-402',
    description: 'Audits multi-hazard risk thresholds, validates cascading compound models, and flags hazard hotspots.',
    permissions: ['audit_risk', 'approve_route', 'flag_hazard', 'tune_thresholds'],
  },
  {
    id: 3,
    username: 'auditor_zainab',
    fullName: 'Zainab Fatima',
    role: 'security_auditor',
    roleTitle: 'Aviation Security Auditor',
    badgeTone: 'low',
    dispatcherId: 'AUD-SEC-109',
    description: 'Oversees regulatory compliance, verifies SHA-256 cryptographic audit logs, and inspects event trails.',
    permissions: ['view_audit', 'verify_hash', 'export_compliance', 'inspect_users'],
  },
  {
    id: 4,
    username: 'met_farhan',
    fullName: 'Farhan Ali',
    role: 'met_analyst',
    roleTitle: 'Meteorological Analyst',
    badgeTone: 'neutral',
    dispatcherId: 'MET-OPS-773',
    description: 'Calibrates Doppler radar returns, tests DistilBERT NOTAM classification, and tracks space weather Kp.',
    permissions: ['manage_weather', 'calibrate_kp', 'classify_notams', 'create_hazard'],
  },
]

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('skyrisk.activeUser')
      if (saved) return JSON.parse(saved)
    } catch {
      /* ignore */
    }
    return DEFAULT_USERS[0]
  })

  useEffect(() => {
    try {
      localStorage.setItem('skyrisk.activeUser', JSON.stringify(currentUser))
    } catch {
      /* ignore */
    }
  }, [currentUser])

  const switchUser = (roleOrUsername) => {
    const target = DEFAULT_USERS.find(
      (u) => u.role === roleOrUsername || u.username === roleOrUsername
    )
    if (target) {
      setCurrentUser(target)
    }
  }

  const hasPermission = (permission) => {
    return currentUser?.permissions?.includes(permission) || false
  }

  return (
    <AuthContext.Provider value={{ currentUser, setCurrentUser, switchUser, hasPermission, allUsers: DEFAULT_USERS }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
