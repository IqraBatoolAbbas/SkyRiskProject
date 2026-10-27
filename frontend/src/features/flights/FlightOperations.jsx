import { useEffect, useMemo, useState } from 'react'
import { Alert, Badge, Button, Card, DataTable, LoadingState, Modal, SearchField, StatusBadge } from '../../components/ui.jsx'
import { Icon } from '../../components/icons.jsx'
import { getFlights, getFlightTrajectory, createFlightPlan, evaluateFlightRisk } from '../../services/api.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { useRouter } from '../../utils/router.jsx'

export default function FlightOperations() {
  const { currentUser } = useAuth()
  const { navigate } = useRouter()

  const [flights, setFlights] = useState([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [origin, setOrigin] = useState('all')
  const [status, setStatus] = useState('all')
  const [selected, setSelected] = useState(null)
  const [trajectoryDetail, setTrajectoryDetail] = useState(null)
  const [openModal, setOpenModal] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [evaluating, setEvaluating] = useState(false)
  const [alertMsg, setAlertMsg] = useState(null)

  const [newFlight, setNewFlight] = useState({
    call_sign: 'PK-850',
    aircraft_type: 'A320-200',
    origin: 'OPKC',
    destination: 'OPLA',
    alternate_airport: 'OPIS',
    cruise_altitude_ft: 36000,
    cruise_speed_kts: 450,
    route_string: 'OPKC DCT RK J121 SULOM J130 OPLA',
  })

  const loadFlights = () => {
    setLoading(true)
    getFlights()
      .then((res) => {
        setLoading(false)
        if (res?.flights) {
          setFlights(res.flights)
          if (res.flights.length > 0 && !selected) {
            setSelected(res.flights[0])
          }
        }
      })
      .catch(() => {
        setLoading(false)
      })
  }

  useEffect(() => {
    loadFlights()
  }, [])

  // Load 4D trajectory details when flight selected
  useEffect(() => {
    if (selected?.id) {
      getFlightTrajectory(selected.id)
        .then((res) => {
          if (res?.flight) setTrajectoryDetail(res.flight)
        })
        .catch(() => {})
    }
  }, [selected])

  const rows = useMemo(() => {
    return flights.filter((flight) => {
      const hay = `${flight.id} ${flight.call_sign} ${flight.origin} ${flight.destination} ${flight.aircraft_type}`.toLowerCase()
      const q = query.toLowerCase()
      const matchQ = !q || hay.includes(q)
      const matchO = origin === 'all' || flight.origin === origin
      const matchS = status === 'all' || flight.status === status
      return matchQ && matchO && matchS
    })
  }, [flights, query, origin, status])

  const origins = ['all', ...new Set(flights.map((f) => f.origin))]
  const statuses = ['all', ...new Set(flights.map((f) => f.status))]

  const handleCreateFlight = async () => {
    setSubmitting(true)
    try {
      const res = await createFlightPlan(newFlight)
      setSubmitting(false)
      setOpenModal(false)
      setAlertMsg({
        tone: 'low',
        title: '4D Flight Plan Registered',
        text: `Flight ${newFlight.call_sign} saved to PostgreSQL with ${res.waypoint_count} 4D trajectory waypoints. Total distance: ${res.total_distance_km} km.`,
      })
      loadFlights()
    } catch (err) {
      setSubmitting(false)
      setAlertMsg({
        tone: 'critical',
        title: 'Error Creating Flight',
        text: err.message || 'Failed to submit flight plan to backend.',
      })
    }
  }

  const handleTriggerRiskScan = async (flightId) => {
    setEvaluating(true)
    try {
      const res = await evaluateFlightRisk(flightId)
      setEvaluating(false)
      setAlertMsg({
        tone: res.overall_risk_score >= 65 ? 'critical' : res.overall_risk_score >= 35 ? 'elevated' : 'low',
        title: `4D Multi-Hazard Scan Complete: ${flightId}`,
        text: `Assessed Risk: ${res.overall_risk_score}/100 (${res.overall_risk_band}). ${res.recommended_action}`,
      })
      loadFlights()
      if (selected?.id) {
        getFlightTrajectory(selected.id).then((r) => r?.flight && setTrajectoryDetail(r.flight))
      }
    } catch (err) {
      setEvaluating(false)
      setAlertMsg({
        tone: 'critical',
        title: 'Evaluation Failed',
        text: err.message,
      })
    }
  }

  const canCreateFlight = currentUser.role === 'flight_dispatcher' || currentUser.role === 'admin'

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: 20, margin: 0, fontWeight: 700 }}>Flight Operations & 4D Trajectory Management</h2>
          <p className="muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
            Process flight telemetry, represent trajectories in 4D (Lat, Lon, Alt, Time), and trigger automated risk scans.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <Button size="sm" icon="refresh" onClick={loadFlights}>
            Refresh Flights
          </Button>
          {canCreateFlight ? (
            <Button size="sm" icon="plane" onClick={() => setOpenModal(true)}>
              Enter New Flight Plan
            </Button>
          ) : (
            <Badge tone="neutral">Flight Creation Restricted to Dispatcher</Badge>
          )}
        </div>
      </div>

      {alertMsg && (
        <Alert tone={alertMsg.tone} title={alertMsg.title}>
          <span>{alertMsg.text}</span>
        </Alert>
      )}

      <div className="split">
        {/* Left Column: Filter Controls and Flight Table */}
        <Card>
          <div className="section-heading">
            <div>
              <h3>Active Airspace Flight Trajectories</h3>
              <p className="muted">Live flights retrieved from PostgreSQL database.</p>
            </div>
            <Badge tone="info">{rows.length} Flights</Badge>
          </div>

          <div className="filters">
            <SearchField
              id="flight-search"
              value={query}
              onChange={setQuery}
              placeholder="Search callsign, ICAO, aircraft type…"
            />

            <label className="field">
              <span>Origin</span>
              <select className="select" value={origin} onChange={(e) => setOrigin(e.target.value)}>
                {origins.map((o) => (
                  <option key={o} value={o}>{o === 'all' ? 'All Origin Aerodromes' : o}</option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Status</span>
              <select className="select" value={status} onChange={(e) => setStatus(e.target.value)}>
                {statuses.map((s) => (
                  <option key={s} value={s}>{s === 'all' ? 'All Operational Statuses' : s}</option>
                ))}
              </select>
            </label>
          </div>

          {loading ? (
            <LoadingState label="Loading flight trajectories from PostgreSQL database…" />
          ) : (
            <DataTable
              rows={rows}
              selectedId={selected?.id}
              onSelect={setSelected}
              empty="No matching flight records found."
              columns={[
                {
                  key: 'call_sign',
                  label: 'Callsign / ID',
                  render: (r) => (
                    <div>
                      <strong style={{ fontSize: 13, color: 'var(--text)' }}>{r.call_sign}</strong>
                      <div className="mono" style={{ fontSize: 10, color: 'var(--muted)' }}>{r.id}</div>
                    </div>
                  ),
                },
                {
                  key: 'route',
                  label: 'City Pair',
                  render: (r) => (
                    <span style={{ fontWeight: 600 }}>
                      {r.origin} <span style={{ color: 'var(--cyan)' }}>→</span> {r.destination}
                    </span>
                  ),
                },
                {
                  key: 'cruise_altitude_ft',
                  label: 'Altitude',
                  render: (r) => <span className="mono">FL{Math.floor(r.cruise_altitude_ft / 100)}</span>,
                },
                {
                  key: 'overall_risk_score',
                  label: 'Risk Score',
                  render: (r) => (
                    <span
                      style={{
                        fontWeight: 700,
                        color: r.overall_risk_score >= 65 ? '#EF4444' : r.overall_risk_score >= 35 ? '#F59E0B' : '#10B981',
                      }}
                    >
                      {r.overall_risk_score}/100
                    </span>
                  ),
                },
                {
                  key: 'status',
                  label: 'Status',
                  render: (r) => <StatusBadge value={r.status} />,
                },
              ]}
            />
          )}
        </Card>

        {/* Right Column: Selected Flight Trajectory Details */}
        {selected ? (
          <Card>
            <div className="section-heading">
              <div>
                <h3>Flight 4D Trajectory: {selected.call_sign}</h3>
                <p className="muted">{selected.aircraft_type} · {selected.origin} to {selected.destination}</p>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <Button
                  size="sm"
                  icon="sparkles"
                  onClick={() => handleTriggerRiskScan(selected.id)}
                  disabled={evaluating}
                >
                  {evaluating ? 'Scanning...' : 'Trigger Multi-Hazard Scan'}
                </Button>
                {selected.overall_risk_score >= 35 && (
                  <Button
                    variant="primary"
                    size="sm"
                    icon="arrow-right"
                    onClick={() => navigate('/workspace/recovery')}
                    style={{
                      background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
                    }}
                  >
                    Recovery Decision
                  </Button>
                )}
              </div>
            </div>

            <div className="stack" style={{ gap: 12 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
                <div style={{ padding: 10, background: 'rgba(0,0,0,0.25)', borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>DEPARTURE / ARRIVAL</div>
                  <strong style={{ fontSize: 13 }}>{selected.origin} → {selected.destination}</strong>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>ALTN: {selected.alternate_airport || 'OPIS'}</div>
                </div>

                <div style={{ padding: 10, background: 'rgba(0,0,0,0.25)', borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>CRUISE FL & SPEED</div>
                  <strong style={{ fontSize: 13 }}>FL{Math.floor(selected.cruise_altitude_ft / 100)}</strong>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>{selected.cruise_speed_kts} kts (TAS)</div>
                </div>

                <div style={{ padding: 10, background: 'rgba(0,0,0,0.25)', borderRadius: 8 }}>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>CURRENT RISK BAND</div>
                  <strong style={{ fontSize: 13, color: selected.overall_risk_score >= 65 ? '#EF4444' : '#10B981' }}>
                    {selected.overall_risk_score}/100 ({selected.overall_risk_band})
                  </strong>
                  <div style={{ fontSize: 11, color: 'var(--muted)' }}>Phase: {selected.phase}</div>
                </div>
              </div>

              {/* Cleared Routing String */}
              <div style={{ padding: 12, background: 'rgba(15, 23, 42, 0.6)', borderRadius: 8, border: '1px solid rgba(56, 189, 248, 0.15)' }}>
                <div style={{ fontSize: 11, color: 'var(--muted)', marginBottom: 4 }}>ATC CLEARED ROUTE STRING</div>
                <div className="mono" style={{ fontSize: 12.5, color: '#38BDF8', fontWeight: 600 }}>
                  {selected.route_string || `${selected.origin} DCT ${selected.destination}`}
                </div>
              </div>

              {/* 4D Waypoints Navlog Table */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <strong style={{ fontSize: 13, color: 'var(--cyan)' }}>
                    4D TRAJECTORY WAYPOINTS ({trajectoryDetail?.waypoints?.length || 0} FIXES)
                  </strong>
                  <Button size="sm" variant="ghost" onClick={() => navigate('/workspace/trajectory')}>
                    View on 4D Map Canvas →
                  </Button>
                </div>

                <div style={{ overflowX: 'auto', maxHeight: 250 }}>
                  <table className="table" style={{ width: '100%', fontSize: 12 }}>
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Fix Name</th>
                        <th>Latitude</th>
                        <th>Longitude</th>
                        <th>Alt</th>
                        <th>Time</th>
                        <th>Hazard</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(trajectoryDetail?.waypoints || []).map((wp, i) => (
                        <tr key={i} style={{ background: wp.hazard_score > 50 ? 'rgba(239, 68, 68, 0.1)' : 'transparent' }}>
                          <td>{i + 1}</td>
                          <td>
                            <strong>{wp.name}</strong>
                            {wp.is_hotspot && <Badge tone="critical" style={{ marginLeft: 6, fontSize: 10 }}>Hotspot</Badge>}
                          </td>
                          <td className="mono">{wp.lat?.toFixed(2)}°N</td>
                          <td className="mono">{wp.lon?.toFixed(2)}°E</td>
                          <td className="mono">FL{Math.floor((wp.alt || 36000) / 100)}</td>
                          <td className="mono">T+{wp.time_min}m</td>
                          <td>
                            {wp.hazard_score > 0 ? (
                              <span style={{ color: wp.hazard_score > 50 ? '#EF4444' : '#F59E0B', fontWeight: 700 }}>
                                {wp.hazard_score}/100
                              </span>
                            ) : (
                              <span style={{ color: 'var(--muted)' }}>Clear</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </Card>
        ) : null}
      </div>

      {/* Enter New Flight Plan Modal */}
      {openModal && (
        <Modal title="Enter New 4D Flight Plan (ICAO Format)" onClose={() => setOpenModal(false)}>
          <div className="stack" style={{ gap: 14 }}>
            <p className="muted" style={{ fontSize: 13 }}>
              Enter flight parameters to calculate and store a 4D trajectory (Lat, Lon, Alt, Time) in the PostgreSQL database.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <label className="field">
                <span>Flight Callsign</span>
                <input
                  className="input"
                  value={newFlight.call_sign}
                  onChange={(e) => setNewFlight({ ...newFlight, call_sign: e.target.value.toUpperCase() })}
                  placeholder="e.g. PK-781"
                />
              </label>

              <label className="field">
                <span>Aircraft Type</span>
                <input
                  className="input"
                  value={newFlight.aircraft_type}
                  onChange={(e) => setNewFlight({ ...newFlight, aircraft_type: e.target.value })}
                  placeholder="e.g. A320-200"
                />
              </label>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
              <label className="field">
                <span>Origin (ICAO)</span>
                <input
                  className="input"
                  value={newFlight.origin}
                  onChange={(e) => setNewFlight({ ...newFlight, origin: e.target.value.toUpperCase() })}
                  placeholder="OPKC"
                />
              </label>

              <label className="field">
                <span>Destination (ICAO)</span>
                <input
                  className="input"
                  value={newFlight.destination}
                  onChange={(e) => setNewFlight({ ...newFlight, destination: e.target.value.toUpperCase() })}
                  placeholder="OPLA"
                />
              </label>

              <label className="field">
                <span>Alternate (ICAO)</span>
                <input
                  className="input"
                  value={newFlight.alternate_airport}
                  onChange={(e) => setNewFlight({ ...newFlight, alternate_airport: e.target.value.toUpperCase() })}
                  placeholder="OPIS"
                />
              </label>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <label className="field">
                <span>Planned Altitude (ft)</span>
                <input
                  type="number"
                  className="input"
                  value={newFlight.cruise_altitude_ft}
                  onChange={(e) => setNewFlight({ ...newFlight, cruise_altitude_ft: Number(e.target.value) })}
                  placeholder="36000"
                />
              </label>

              <label className="field">
                <span>Cruise Speed (kts)</span>
                <input
                  type="number"
                  className="input"
                  value={newFlight.cruise_speed_kts}
                  onChange={(e) => setNewFlight({ ...newFlight, cruise_speed_kts: Number(e.target.value) })}
                  placeholder="450"
                />
              </label>
            </div>

            <label className="field">
              <span>Planned Route String (Optional)</span>
              <input
                className="input"
                value={newFlight.route_string}
                onChange={(e) => setNewFlight({ ...newFlight, route_string: e.target.value })}
                placeholder="OPKC DCT RK J121 SULOM J130 OPLA"
              />
            </label>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
              <Button variant="ghost" onClick={() => setOpenModal(false)} disabled={submitting}>
                Cancel
              </Button>
              <Button variant="primary" icon="check" onClick={handleCreateFlight} disabled={submitting}>
                {submitting ? 'Generating 4D Trajectory...' : 'Generate 4D Trajectory & Save'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  )
}
