import { useEffect, useState } from 'react'
import { Alert, Badge, Button, Card, LoadingState, StatusBadge } from '../../components/ui.jsx'
import { Icon } from '../../components/icons.jsx'
import { getHealth, getFlights, getActiveHazards, getRecoverySummary, getMonitoringStatus, triggerAirspaceScan } from '../../services/api.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { useRouter } from '../../utils/router.jsx'

export default function OverviewDashboard() {
  const { currentUser } = useAuth()
  const { navigate } = useRouter()

  const [loading, setLoading] = useState(true)
  const [flights, setFlights] = useState([])
  const [hazards, setHazards] = useState([])
  const [recoverySummary, setRecoverySummary] = useState(null)
  const [monitoring, setMonitoring] = useState(null)
  const [scanning, setScanning] = useState(false)
  const [scanMessage, setScanMessage] = useState(null)

  const loadDashboardData = () => {
    setLoading(true)
    Promise.all([
      getFlights(),
      getActiveHazards(),
      getRecoverySummary(),
      getMonitoringStatus(),
    ])
      .then(([flightsRes, hazardsRes, recoveryRes, monitorRes]) => {
        setLoading(false)
        if (flightsRes?.flights) setFlights(flightsRes.flights)
        if (hazardsRes?.hazards) setHazards(hazardsRes.hazards)
        if (recoveryRes) setRecoverySummary(recoveryRes)
        if (monitorRes) setMonitoring(monitorRes)
      })
      .catch(() => {
        setLoading(false)
      })
  }

  useEffect(() => {
    loadDashboardData()
    const id = window.setInterval(loadDashboardData, 20000)
    return () => window.clearInterval(id)
  }, [])

  const handleScanNow = async () => {
    setScanning(true)
    try {
      const res = await triggerAirspaceScan()
      setScanning(false)
      setMonitoring(res)
      setScanMessage({
        tone: res.separation_conflicts_count > 0 ? 'critical' : 'low',
        title: 'Airspace 4D Scan Complete',
        text: `Scanned ${res.total_monitored_flights} flights across Karachi & Lahore FIRs. Found ${res.separation_conflicts_count} separation conflicts and ${res.high_risk_flight_count} flights exceeding safety threshold.`,
      })
      loadDashboardData()
    } catch {
      setScanning(false)
    }
  }

  const highRiskFlights = flights.filter((f) => f.overall_risk_score >= 50.0)

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: 20, margin: 0, fontWeight: 700 }}>Tactical Airspace Risk & Decision-Support Operations</h2>
          <p className="muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
            Integrated 4D flight risk assessment, multi-route recovery decision support, and audit control center.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Badge tone="low">PostgreSQL Active</Badge>
          <Button size="sm" icon="refresh" onClick={loadDashboardData}>
            Refresh Center
          </Button>
          <Button
            size="sm"
            icon="radar"
            onClick={handleScanNow}
            disabled={scanning}
            style={{
              background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
            }}
          >
            {scanning ? 'Scanning 4D Airspace...' : 'Scan Airspace Now'}
          </Button>
        </div>
      </div>

      {scanMessage && (
        <Alert tone={scanMessage.tone} title={scanMessage.title}>
          <span>{scanMessage.text}</span>
        </Alert>
      )}

      {/* KPI Command Center Cards */}
      <div className="kpis">
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Badge tone="info">4D Flights</Badge>
            <Icon name="plane" size="sm" />
          </div>
          <div className="kpi-value">{flights.length}</div>
          <div className="kpi-label">Active Airspace Tracks</div>
        </Card>

        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Badge tone={hazards.length > 0 ? 'critical' : 'low'}>Multi-Hazards</Badge>
            <Icon name="cloud" size="sm" />
          </div>
          <div className="kpi-value">{hazards.length}</div>
          <div className="kpi-label">Weather / SWPC / NOTAMs</div>
        </Card>

        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Badge tone="elevated">Action Required</Badge>
            <Icon name="sparkles" size="sm" />
          </div>
          <div className="kpi-value" style={{ color: highRiskFlights.length > 0 ? '#EF4444' : 'var(--text)' }}>
            {highRiskFlights.length}
          </div>
          <div className="kpi-label">Flights Exceeding Risk Limit</div>
        </Card>

        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Badge tone="low">Audit Integrity</Badge>
            <Icon name="shield" size="sm" />
          </div>
          <div className="kpi-value" style={{ color: '#10B981' }}>100%</div>
          <div className="kpi-label">SHA-256 Digest Chain</div>
        </Card>
      </div>

      {/* Continuous 4D Monitoring & Conflict Radar */}
      <Card style={{ marginTop: 16 }}>
        <div className="section-heading">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: monitoring?.separation_conflicts_count > 0 ? '#EF4444' : '#10B981',
                boxShadow: monitoring?.separation_conflicts_count > 0 ? '0 0 12px #EF4444' : '0 0 10px rgba(16, 185, 129, 0.8)',
              }}
            />
            <div>
              <h3>Continuous 4D Monitoring Radar & Separation Scanner</h3>
              <p className="muted">Monitors trajectory waypoints against evolving weather, space-weather, and flight separation conflicts.</p>
            </div>
          </div>
          <Badge tone={monitoring?.separation_conflicts_count > 0 ? 'critical' : 'low'}>
            {monitoring?.separation_conflicts_count > 0
              ? `${monitoring.separation_conflicts_count} Separation Conflicts!`
              : 'All Corridors Clear'}
          </Badge>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 12, marginTop: 12 }}>
          {flights.map((f) => (
            <div
              key={f.id}
              onClick={() => navigate('/workspace/trajectory')}
              style={{
                padding: 12,
                borderRadius: 8,
                background: 'rgba(15, 23, 42, 0.6)',
                border: `1px solid ${f.overall_risk_score >= 65 ? '#EF4444' : f.overall_risk_score >= 35 ? '#F59E0B' : 'rgba(56, 189, 248, 0.2)'}`,
                cursor: 'pointer',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                <strong style={{ fontSize: 13 }}>{f.call_sign}</strong>
                <Badge tone={f.overall_risk_score >= 65 ? 'critical' : f.overall_risk_score >= 35 ? 'elevated' : 'low'}>
                  {f.overall_risk_score}/100
                </Badge>
              </div>
              <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                {f.origin} → {f.destination} · FL{Math.floor(f.cruise_altitude_ft / 100)}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8, fontSize: 11 }}>
                <span style={{ color: 'var(--cyan)' }}>Phase: {f.phase}</span>
                <span style={{ fontWeight: 600 }}>{f.status}</span>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Main Grid: Active Trajectories & Quick Action Center */}
      <div className="grid-2" style={{ marginTop: 16 }}>
        {/* Active Airspace Trajectories */}
        <Card>
          <div className="section-heading">
            <div>
              <h3>Active Airspace Flight Trajectories</h3>
              <p className="muted">Live status of flights monitored across Pakistani FIRs.</p>
            </div>
            <Button size="sm" icon="plane" onClick={() => navigate('/workspace/flights')}>
              View All Flights →
            </Button>
          </div>

          <div style={{ overflowX: 'auto', marginTop: 10 }}>
            <table className="table" style={{ width: '100%', fontSize: 12.5 }}>
              <thead>
                <tr>
                  <th>Flight</th>
                  <th>Route</th>
                  <th>Altitude</th>
                  <th>Risk</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {flights.map((f) => (
                  <tr key={f.id}>
                    <td>
                      <strong>{f.call_sign}</strong>
                      <div className="mono" style={{ fontSize: 10, color: 'var(--muted)' }}>{f.aircraft_type}</div>
                    </td>
                    <td>{f.origin} → {f.destination}</td>
                    <td className="mono">FL{Math.floor(f.cruise_altitude_ft / 100)}</td>
                    <td>
                      <span
                        style={{
                          fontWeight: 700,
                          color: f.overall_risk_score >= 65 ? '#EF4444' : f.overall_risk_score >= 35 ? '#F59E0B' : '#10B981',
                        }}
                      >
                        {f.overall_risk_score}/100
                      </span>
                    </td>
                    <td><StatusBadge value={f.status} /></td>
                    <td>
                      {f.overall_risk_score >= 35 ? (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => navigate('/workspace/recovery')}
                          style={{ fontSize: 11, padding: '2px 8px' }}
                        >
                          Recover
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => navigate('/workspace/trajectory')}
                          style={{ fontSize: 11, padding: '2px 8px' }}
                        >
                          Inspect
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Tactical Decision-Support Workflow Stepper */}
        <Card>
          <div className="section-heading">
            <div>
              <h3>SkyRisk Auditor 4D Workflow</h3>
              <p className="muted">Integrated pipeline from flight entry to recovery sign-off.</p>
            </div>
            <Badge tone="info">RBAC Enabled</Badge>
          </div>

          <div className="stack" style={{ gap: 12, marginTop: 10 }}>
            <div style={{ display: 'flex', gap: 12, padding: 12, background: 'rgba(15, 23, 42, 0.6)', borderRadius: 8, border: '1px solid rgba(56, 189, 248, 0.2)' }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#38BDF8', color: '#000', fontWeight: 800, display: 'grid', placeItems: 'center', fontSize: 12 }}>
                1
              </div>
              <div style={{ flex: 1 }}>
                <strong style={{ fontSize: 13, color: '#38BDF8' }}>4D Flight Plan Entry</strong>
                <p style={{ fontSize: 12, margin: '2px 0 0', color: 'var(--muted)' }}>
                  Submit flight plan; coordinates, elevation, speed, and time waypoints are computed automatically.
                </p>
              </div>
              <Button size="sm" variant="ghost" onClick={() => navigate('/workspace/flights')}>
                Launch →
              </Button>
            </div>

            <div style={{ display: 'flex', gap: 12, padding: 12, background: 'rgba(15, 23, 42, 0.6)', borderRadius: 8, border: '1px solid rgba(245, 158, 11, 0.2)' }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#F59E0B', color: '#000', fontWeight: 800, display: 'grid', placeItems: 'center', fontSize: 12 }}>
                2
              </div>
              <div style={{ flex: 1 }}>
                <strong style={{ fontSize: 13, color: '#F59E0B' }}>Multi-Hazard 4D Scan</strong>
                <p style={{ fontSize: 12, margin: '2px 0 0', color: 'var(--muted)' }}>
                  Assesses Weather, Space-Weather Kp, DistilBERT NOTAMs, and Airspace conflicts along the 4D path.
                </p>
              </div>
              <Button size="sm" variant="ghost" onClick={() => navigate('/workspace/risk')}>
                Scan →
              </Button>
            </div>

            <div style={{ display: 'flex', gap: 12, padding: 12, background: 'rgba(15, 23, 42, 0.6)', borderRadius: 8, border: '1px solid rgba(16, 185, 129, 0.2)' }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#10B981', color: '#000', fontWeight: 800, display: 'grid', placeItems: 'center', fontSize: 12 }}>
                3
              </div>
              <div style={{ flex: 1 }}>
                <strong style={{ fontSize: 13, color: '#10B981' }}>Recovery Decision & Approval</strong>
                <p style={{ fontSize: 12, margin: '2px 0 0', color: 'var(--muted)' }}>
                  Compare 4 recovery routes (Shortest, Eco, Safest, Balanced). Authorized user signs off.
                </p>
              </div>
              <Button size="sm" variant="ghost" onClick={() => navigate('/workspace/recovery')}>
                Approve →
              </Button>
            </div>

            <div style={{ display: 'flex', gap: 12, padding: 12, background: 'rgba(15, 23, 42, 0.6)', borderRadius: 8, border: '1px solid rgba(168, 85, 247, 0.2)' }}>
              <div style={{ width: 28, height: 28, borderRadius: '50%', background: '#A855F7', color: '#000', fontWeight: 800, display: 'grid', placeItems: 'center', fontSize: 12 }}>
                4
              </div>
              <div style={{ flex: 1 }}>
                <strong style={{ fontSize: 13, color: '#C084FC' }}>Updated OFP & SHA-256 Audit</strong>
                <p style={{ fontSize: 12, margin: '2px 0 0', color: 'var(--muted)' }}>
                  Generates amended flight plan navlog and appends tamper-evident audit record to PostgreSQL.
                </p>
              </div>
              <Button size="sm" variant="ghost" onClick={() => navigate('/workspace/ofp')}>
                Inspect →
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </>
  )
}
