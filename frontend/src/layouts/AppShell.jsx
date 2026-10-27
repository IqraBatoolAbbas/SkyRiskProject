import { useEffect, useMemo, useState } from 'react'
import { Icon } from '../components/icons.jsx'
import { Badge, Button, SearchField } from '../components/ui.jsx'
import { notifications, PROJECT } from '../data/demoData.js'
import { pageMeta, workspaceNav } from '../data/nav.js'
import { formatClock, storageGet, storageSet } from '../utils/format.js'
import { Link, useRouter } from '../utils/router.jsx'
import { getHealth, getMonitoringStatus } from '../services/api.js'
import { useAuth } from '../context/AuthContext.jsx'

import OverviewDashboard from '../features/dashboard/OverviewDashboard.jsx'
import FlightOperations from '../features/flights/FlightOperations.jsx'
import TrajectoryVisualization from '../features/trajectory/TrajectoryVisualization.jsx'
import RiskAssessment from '../features/risk/RiskAssessment.jsx'
import RecoveryPlanning from '../features/recovery/RecoveryPlanning.jsx'
import FlightPlanManagement from '../features/ofp/FlightPlanManagement.jsx'
import AuditLogs from '../features/audit/AuditLogs.jsx'
import DataSources from '../features/sources/DataSources.jsx'
import UserManagement from '../features/users/UserManagement.jsx'
import SettingsPage from '../features/settings/SettingsPage.jsx'

function routeView(path) {
  if (path.startsWith('/workspace/flights')) return <FlightOperations />
  if (path.startsWith('/workspace/trajectory')) return <TrajectoryVisualization />
  if (path.startsWith('/workspace/risk')) return <RiskAssessment />
  if (path.startsWith('/workspace/recovery')) return <RecoveryPlanning />
  if (path.startsWith('/workspace/ofp')) return <FlightPlanManagement />
  if (path.startsWith('/workspace/audit')) return <AuditLogs />
  if (path.startsWith('/workspace/sources')) return <DataSources />
  if (path.startsWith('/workspace/users')) return <UserManagement />
  if (path.startsWith('/workspace/settings')) return <SettingsPage />
  return <OverviewDashboard />
}

export default function AppShell() {
  const { path, navigate } = useRouter()
  const [collapsed, setCollapsed] = useState(() => storageGet('skyrisk.sidebarCollapsed', false))
  const [drawer, setDrawer] = useState(false)
  const [query, setQuery] = useState('')
  const [openMenu, setOpenMenu] = useState(null)
  const [clock, setClock] = useState(new Date())
  const [backendState, setBackendState] = useState({ online: false, checked: false, pinging: false })

  const { currentUser, switchUser, allUsers } = useAuth()
  const [monitoring, setMonitoring] = useState({ active: true, conflictCount: 0, highRiskCount: 0, flights: [] })

  const timeMode = storageGet('skyrisk.timeDisplay', 'utc')
  const dataMode = storageGet('skyrisk.dataMode', 'Mixed')

  // Live clock tick
  useEffect(() => {
    const id = window.setInterval(() => setClock(new Date()), 1000)
    return () => window.clearInterval(id)
  }, [])

  // Poll 4D Airspace Monitoring & Backend Health
  useEffect(() => {
    let active = true
    const checkMonitoring = () => {
      getHealth()
        .then(() => {
          if (active) setBackendState({ online: true, checked: true, pinging: false })
        })
        .catch(() => {
          if (active) setBackendState({ online: false, checked: true, pinging: false })
        })

      getMonitoringStatus()
        .then((data) => {
          if (active && data) {
            setMonitoring({
              active: true,
              conflictCount: data.separation_conflicts_count || 0,
              highRiskCount: data.high_risk_flight_count || 0,
              flights: data.scanned_flights || [],
            })
          }
        })
        .catch(() => {
          /* ignore offline poll */
        })
    }

    checkMonitoring()
    const pollId = window.setInterval(checkMonitoring, 15000)
    return () => {
      active = false
      window.clearInterval(pollId)
    }
  }, [])

  // Check backend readiness on button click
  const handleCheckBackendClick = () => {
    setBackendState((prev) => ({ ...prev, pinging: true }))
    getHealth()
      .then(() => {
        setBackendState({ online: true, checked: true, pinging: false })
      })
      .catch(() => {
        setBackendState({ online: false, checked: true, pinging: false })
      })
  }

  useEffect(() => {
    storageSet('skyrisk.sidebarCollapsed', collapsed)
  }, [collapsed])

  // Close menus when clicking outside
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (!e.target.closest('.menu')) {
        setOpenMenu(null)
      }
    }
    document.addEventListener('click', handleOutsideClick)
    return () => document.removeEventListener('click', handleOutsideClick)
  }, [])

  const meta = pageMeta[path] || pageMeta['/workspace']

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return []
    return workspaceNav.filter((item) => item.label.toLowerCase().includes(q))
  }, [query])

  return (
    <div className={`shell ${collapsed ? 'is-collapsed' : ''} ${drawer ? 'drawer-open' : ''}`}>
      {drawer ? (
        <button
          className="overlay"
          aria-label="Close navigation drawer"
          onClick={() => setDrawer(false)}
        />
      ) : null}

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Icon name="radar" />
          </div>
          <div>
            <strong>{PROJECT.name}</strong>
            <small>Tactical Airspace FYP</small>
          </div>
        </div>

        <nav className="nav" aria-label="Workspace navigation">
          {workspaceNav.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              end={item.to === '/workspace'}
              onClick={() => setDrawer(false)}
              title={item.label}
            >
              <Icon name={item.icon} />
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar-foot">
          <Button
            variant="ghost"
            icon={collapsed ? 'expand' : 'collapse'}
            onClick={() => setCollapsed((v) => !v)}
            style={{ width: '100%', justifyContent: collapsed ? 'center' : 'flex-start' }}
          >
            <span>{collapsed ? 'Expand' : 'Collapse Sidebar'}</span>
          </Button>
        </div>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <button
            className="btn btn-icon btn-ghost mobile-only"
            onClick={() => setDrawer(true)}
            aria-label="Open mobile navigation"
          >
            <Icon name="menu" />
          </button>

          <div style={{ marginRight: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
            <h1>{meta.title}</h1>
          </div>

          <div className="menu">
            <SearchField
              id="workspace-search"
              value={query}
              onChange={setQuery}
              placeholder="Jump to module (e.g. Risk, 4D, OFP)…"
            />
            {matches.length ? (
              <div className="menu-panel">
                <div style={{ padding: '6px 12px', fontSize: 11, color: 'var(--muted)', fontWeight: 600 }}>
                  MATCHING MODULES
                </div>
                {matches.map((item) => (
                  <button
                    key={item.to}
                    className="menu-item"
                    onClick={() => {
                      navigate(item.to)
                      setQuery('')
                    }}
                  >
                    <Icon name={item.icon} size="sm" />
                    <span style={{ marginLeft: 8 }}>{item.label}</span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>

          <div className="topbar-actions">
            {/* Continuous 4D Monitoring Ticker */}
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '4px 10px',
                fontSize: 11.5,
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
                borderRadius: 999,
              }}
              title="Continuous 4D trajectory monitoring & conflict scanner"
            >
              <span
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: monitoring.conflictCount > 0 ? '#EF4444' : '#10B981',
                  boxShadow: monitoring.conflictCount > 0 ? '0 0 10px #EF4444' : '0 0 8px rgba(16, 185, 129, 0.7)',
                }}
              />
              <span style={{ fontWeight: 600, color: 'var(--text)' }}>
                {monitoring.conflictCount > 0
                  ? `${monitoring.conflictCount} Separation Conflict!`
                  : `4D Radar: ${monitoring.flights.length || 4} Flights`}
              </span>
            </div>

            {/* Backend connectivity indicator */}
            <button
              className="btn btn-ghost btn-sm"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '4px 10px',
                fontSize: 11.5,
                border: '1px solid var(--border)',
                borderRadius: 999,
              }}
              onClick={handleCheckBackendClick}
              title="Click to re-ping FastAPI backend at 127.0.0.1:8000"
            >
              <span
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: backendState.online ? 'var(--low)' : 'var(--high)',
                  boxShadow: backendState.online ? '0 0 8px rgba(34, 197, 94, 0.6)' : 'none',
                }}
              />
              <span>
                {backendState.pinging
                  ? 'Checking...'
                  : backendState.online
                    ? 'PostgreSQL Connected'
                    : 'Local Data Mode'}
              </span>
            </button>

            {/* Active RBAC Role Badge & Switcher */}
            <div className="menu">
              <button
                className="btn btn-ghost btn-sm"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '4px 12px',
                  borderRadius: 999,
                  border: '1px solid rgba(168, 85, 247, 0.4)',
                  background: 'rgba(168, 85, 247, 0.1)',
                }}
                onClick={() => setOpenMenu(openMenu === 'role' ? null : 'role')}
                title="Active Role in RBAC System"
              >
                <Icon name="shield" size="sm" />
                <span style={{ fontWeight: 600, color: '#C084FC', fontSize: 11.5 }}>
                  {currentUser?.roleTitle || 'Flight Dispatcher'}
                </span>
                <span style={{ fontSize: 10, color: 'var(--muted)' }}>▼</span>
              </button>

              {openMenu === 'role' ? (
                <div className="menu-panel" style={{ width: 290 }}>
                  <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', fontWeight: 600, fontSize: 12 }}>
                    SWITCH OPERATIONAL ROLE (RBAC)
                  </div>
                  {allUsers.map((u) => (
                    <button
                      key={u.role}
                      className="menu-item"
                      style={{
                        padding: '10px 12px',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'flex-start',
                        gap: 2,
                        background: currentUser.role === u.role ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                      }}
                      onClick={() => {
                        switchUser(u.role)
                        setOpenMenu(null)
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                        <strong style={{ color: currentUser.role === u.role ? 'var(--cyan)' : 'var(--text)', fontSize: 12.5 }}>
                          {u.fullName}
                        </strong>
                        <Badge tone={u.badgeTone}>{u.roleTitle.split(' ')[0]}</Badge>
                      </div>
                      <span style={{ fontSize: 11, color: 'var(--muted)', textAlign: 'left' }}>
                        {u.roleTitle} · {u.dispatcherId}
                      </span>
                    </button>
                  ))}
                </div>
              ) : null}
            </div>

            <span className="clock" title="System / UTC clock">
              <Icon name="clock" size="sm" style={{ display: 'inline', verticalAlign: '-2px', marginRight: 4 }} />
              {formatClock(clock, timeMode)}
            </span>

            {/* Notifications Menu */}
            <div className="menu">
              <button
                className="btn btn-icon"
                onClick={() => setOpenMenu(openMenu === 'bell' ? null : 'bell')}
                aria-label="System notifications"
                style={{ position: 'relative' }}
              >
                <Icon name="bell" />
                <span
                  style={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    width: 7,
                    height: 7,
                    borderRadius: '50%',
                    background: 'var(--cyan)',
                  }}
                />
              </button>
              {openMenu === 'bell' ? (
                <div className="menu-panel" style={{ width: 320 }}>
                  <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)', fontWeight: 600, fontSize: 13 }}>
                    Auditor Notifications ({notifications.length})
                  </div>
                  <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                    {notifications.map((note) => (
                      <div key={note.id} className="note" style={{ borderBottom: '1px solid rgba(37,54,80,0.3)', padding: '10px 12px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                          <strong style={{ fontSize: 13, color: 'var(--text)' }}>{note.title}</strong>
                          <span style={{ fontSize: 11, color: 'var(--muted)' }}>{note.time}</span>
                        </div>
                        <div style={{ fontSize: 12.5, lineHeight: 1.4 }}>{note.body}</div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>

            {/* Profile Menu */}
            <div className="menu">
              <button
                className="btn btn-icon"
                onClick={() => setOpenMenu(openMenu === 'user' ? null : 'user')}
                aria-label="User profile and settings"
              >
                <Icon name="user" />
              </button>
              {openMenu === 'user' ? (
                <div className="menu-panel">
                  <div className="note" style={{ borderBottom: '1px solid var(--border)', paddingBottom: 10 }}>
                    <strong style={{ color: 'var(--text)' }}>{currentUser?.fullName}</strong>
                    <div style={{ fontSize: 12, color: 'var(--cyan)' }}>{currentUser?.roleTitle}</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>
                      ID: {currentUser?.dispatcherId} · Postgres Auth
                    </div>
                  </div>
                  <button
                    className="menu-item"
                    onClick={() => {
                      navigate('/workspace/users')
                      setOpenMenu(null)
                    }}
                  >
                    <Icon name="users" size="sm" />
                    <span style={{ marginLeft: 8 }}>Role & Personnel Management</span>
                  </button>
                  <button
                    className="menu-item"
                    onClick={() => {
                      navigate('/workspace/settings')
                      setOpenMenu(null)
                    }}
                  >
                    <Icon name="settings" size="sm" />
                    <span style={{ marginLeft: 8 }}>Workspace Settings</span>
                  </button>
                  <button
                    className="menu-item"
                    onClick={() => {
                      navigate('/')
                      setOpenMenu(null)
                    }}
                  >
                    <Icon name="radar" size="sm" />
                    <span style={{ marginLeft: 8 }}>Landing Page</span>
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </header>

        <main className="content">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
            <p className="muted" style={{ fontSize: 13.5 }}>{meta.subtitle}</p>
            <div style={{ display: 'flex', gap: 6 }}>
              <Badge tone="neutral">FYP Prototype</Badge>
              <Badge tone="elevated">Not for Ops</Badge>
            </div>
          </div>

          {routeView(path)}
        </main>
      </div>
    </div>
  )
}
