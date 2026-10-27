import { useEffect, useState } from 'react'
import { Alert, Badge, Button, Card, DataTable, LoadingState, Modal, StatusBadge } from '../../components/ui.jsx'
import { Icon } from '../../components/icons.jsx'
import { getFlightRecovery, approveRecoveryRoute, rejectRecoveryRoute, getFlights } from '../../services/api.js'
import { formatNumber } from '../../utils/format.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { useRouter } from '../../utils/router.jsx'
import confetti from 'canvas-confetti'

export default function RecoveryPlanning() {
  const { currentUser, hasPermission } = useAuth()
  const { navigate } = useRouter()

  const [flights, setFlights] = useState([])
  const [selectedFlightId, setSelectedFlightId] = useState('PK-781')
  const [recoveryData, setRecoveryData] = useState({ status: 'loading', data: null })
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const [isApproving, setIsApproving] = useState(false)
  const [isRejecting, setIsRejecting] = useState(false)
  const [approvalNotes, setApprovalNotes] = useState('Cleared via Pareto-optimal trajectory. Multi-hazard risk reduced below threshold.')
  const [rejectionReason, setRejectionReason] = useState('Lateral detour incurs unacceptable traffic delay during peak FIR hours.')
  const [actionAlert, setActionAlert] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  // Load flights list
  useEffect(() => {
    getFlights()
      .then((res) => {
        if (res?.flights) setFlights(res.flights)
      })
      .catch(() => {})
  }, [])

  // Load recovery candidates for selected flight
  const fetchFlightCandidates = (flightId) => {
    setRecoveryData({ status: 'loading', data: null })
    setActionAlert(null)
    getFlightRecovery(flightId)
      .then((res) => {
        setRecoveryData({ status: 'ready', data: res })
        if (res?.candidates?.length > 0) {
          // Default to Balanced or highest risk reduction candidate
          const best = res.candidates.find((c) => c.candidate_code === 'ROUTE_D') || res.candidates[0]
          setSelectedCandidate(best)
        }
      })
      .catch((err) => {
        setRecoveryData({ status: 'error', error: err })
      })
  }

  useEffect(() => {
    fetchFlightCandidates(selectedFlightId)
  }, [selectedFlightId])

  const candidates = recoveryData.data?.candidates || []

  // Handle formal approval
  const handleConfirmApproval = async () => {
    if (!selectedCandidate) return
    setSubmitting(true)
    try {
      const res = await approveRecoveryRoute({
        recoveryPlanId: selectedCandidate.id,
        approvedBy: currentUser.fullName,
        approvedRole: currentUser.role,
        notes: approvalNotes,
      })

      setIsApproving(false)
      setSubmitting(false)

      // Trigger celebratory confetti
      try {
        confetti({
          particleCount: 80,
          spread: 70,
          origin: { y: 0.6 },
        })
      } catch {
        /* ignore */
      }

      setActionAlert({
        tone: 'low',
        title: `Recovery Route Approved Successfully!`,
        message: `Candidate '${selectedCandidate.strategy_name}' has been authorized. Updated OFP document '${res.ofp_id}' generated and logged in PostgreSQL audit trail.`,
        ofpId: res.ofp_id,
      })

      // Refresh candidates
      fetchFlightCandidates(selectedFlightId)
    } catch (err) {
      setSubmitting(false)
      setActionAlert({
        tone: 'critical',
        title: 'Approval Authorization Failed',
        message: err.message || 'Error communicating with backend recovery service.',
      })
    }
  }

  // Handle formal rejection
  const handleConfirmRejection = async () => {
    if (!selectedCandidate) return
    setSubmitting(true)
    try {
      await rejectRecoveryRoute({
        recoveryPlanId: selectedCandidate.id,
        rejectedBy: currentUser.fullName,
        rejectedRole: currentUser.role,
        reason: rejectionReason,
      })

      setIsRejecting(false)
      setSubmitting(false)

      setActionAlert({
        tone: 'warning',
        title: `Recovery Candidate Rejected`,
        message: `Candidate '${selectedCandidate.strategy_name}' rejected by ${currentUser.fullName}. Reason logged in audit records.`,
      })

      fetchFlightCandidates(selectedFlightId)
    } catch (err) {
      setSubmitting(false)
      setActionAlert({
        tone: 'critical',
        title: 'Rejection Failed',
        message: err.message || 'Error submitting rejection.',
      })
    }
  }

  const canApprove = currentUser.role === 'flight_dispatcher' || currentUser.role === 'safety_analyst'

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: 20, margin: 0, fontWeight: 700 }}>Recovery Route & Impact Decision Support</h2>
          <p className="muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
            Multi-route generation algorithms evaluating fuel consumption, delay minutes, and residual 4D risk.
          </p>
        </div>

        {/* Flight Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 12.5, color: 'var(--muted)', fontWeight: 600 }}>MONITORED FLIGHT:</span>
          <select
            className="select"
            style={{ minWidth: 200, padding: '6px 12px', fontWeight: 600 }}
            value={selectedFlightId}
            onChange={(e) => setSelectedFlightId(e.target.value)}
          >
            {flights.map((f) => (
              <option key={f.id} value={f.id}>
                {f.call_sign} ({f.origin} → {f.destination}) · Risk: {f.overall_risk_score}
              </option>
            ))}
          </select>
        </div>
      </div>

      {actionAlert && (
        <Alert tone={actionAlert.tone} title={actionAlert.title}>
          <div>
            <span>{actionAlert.message}</span>
            {actionAlert.ofpId && (
              <div style={{ marginTop: 8 }}>
                <Button size="sm" icon="file" onClick={() => navigate('/workspace/ofp')}>
                  Inspect Updated OFP Document
                </Button>
              </div>
            )}
          </div>
        </Alert>
      )}

      {recoveryData.status === 'loading' && <LoadingState label="Synthesizing multi-route recovery candidates from PostgreSQL database…" />}

      {recoveryData.status === 'ready' && (
        <div className="stack" style={{ gap: 16 }}>
          {/* Flight Risk Header Card */}
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <div
                  style={{
                    width: 44,
                    height: 44,
                    borderRadius: 10,
                    background: recoveryData.data.current_risk_score >= 65 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(56, 189, 248, 0.15)',
                    border: `1px solid ${recoveryData.data.current_risk_score >= 65 ? '#EF4444' : '#38BDF8'}`,
                    display: 'grid',
                    placeItems: 'center',
                  }}
                >
                  <Icon name="plane" size="lg" />
                </div>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <strong style={{ fontSize: 18 }}>Flight {recoveryData.data.call_sign}</strong>
                    <Badge tone={recoveryData.data.current_risk_score >= 65 ? 'critical' : 'elevated'}>
                      {recoveryData.data.current_flight_status}
                    </Badge>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>
                    Original Route Multi-Hazard Risk: <strong style={{ color: '#EF4444' }}>{recoveryData.data.current_risk_score}/100 ({recoveryData.data.current_risk_band})</strong>
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ textAlign: 'right', marginRight: 8 }}>
                  <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase' }}>Active RBAC Evaluator</div>
                  <strong style={{ fontSize: 13, color: 'var(--cyan)' }}>{currentUser.fullName} ({currentUser.roleTitle})</strong>
                </div>
                <Badge tone={canApprove ? 'low' : 'neutral'}>
                  {canApprove ? 'Authorized to Release' : 'Auditor / Observer Mode'}
                </Badge>
              </div>
            </div>
          </Card>

          {/* 4 Multi-Route Comparative Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 14 }}>
            {candidates.map((cand) => {
              const isSelected = selectedCandidate?.id === cand.id
              const isApproved = cand.status === 'APPROVED'

              let borderColor = 'var(--border)'
              let badgeColor = 'neutral'
              if (cand.candidate_code === 'ROUTE_A') {
                badgeColor = 'amber'
                if (isSelected) borderColor = '#F59E0B'
              } else if (cand.candidate_code === 'ROUTE_B') {
                badgeColor = 'purple'
                if (isSelected) borderColor = '#A855F7'
              } else if (cand.candidate_code === 'ROUTE_C') {
                badgeColor = 'emerald'
                if (isSelected) borderColor = '#10B981'
              } else if (cand.candidate_code === 'ROUTE_D') {
                badgeColor = 'cyan'
                if (isSelected) borderColor = '#38BDF8'
              }

              return (
                <div
                  key={cand.id}
                  onClick={() => setSelectedCandidate(cand)}
                  style={{
                    cursor: 'pointer',
                    padding: 16,
                    borderRadius: 12,
                    background: isSelected ? 'rgba(30, 41, 59, 0.85)' : 'rgba(15, 23, 42, 0.6)',
                    border: `2px solid ${isSelected ? borderColor : 'rgba(56, 189, 248, 0.15)'}`,
                    boxShadow: isSelected ? `0 0 20px rgba(56, 189, 248, 0.2)` : 'none',
                    transition: 'all 0.2s ease',
                    position: 'relative',
                  }}
                >
                  {isApproved && (
                    <div
                      style={{
                        position: 'absolute',
                        top: 10,
                        right: 10,
                        background: '#10B981',
                        color: '#fff',
                        fontSize: 10,
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: 999,
                      }}
                    >
                      ✓ APPROVED RELEASE
                    </div>
                  )}

                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: 4,
                        background: 'rgba(255,255,255,0.08)',
                        color: 'var(--text)',
                      }}
                    >
                      {cand.candidate_code}
                    </span>
                    <strong style={{ fontSize: 14 }}>{cand.strategy_name}</strong>
                  </div>

                  <p style={{ fontSize: 12, color: 'var(--muted)', minHeight: 48, lineHeight: 1.4, margin: '6px 0 12px' }}>
                    {cand.route_description}
                  </p>

                  {/* Metrics Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, background: 'rgba(0,0,0,0.25)', padding: 10, borderRadius: 8 }}>
                    <div>
                      <div style={{ fontSize: 10, color: 'var(--muted)' }}>RESIDUAL RISK</div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: cand.residual_risk_score < 20 ? '#10B981' : '#F59E0B' }}>
                        {cand.residual_risk_score}/100
                      </div>
                      <div style={{ fontSize: 10, color: '#10B981', fontWeight: 600 }}>
                        -{cand.risk_reduction_percent}% risk
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: 10, color: 'var(--muted)' }}>FLIGHT DELAY</div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: cand.delay_minutes > 10 ? '#EF4444' : 'var(--text)' }}>
                        +{cand.delay_minutes} min
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--muted)' }}>
                        +{cand.distance_change_km} km
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: 10, color: 'var(--muted)' }}>FUEL IMPACT</div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: cand.fuel_delta_kg < 0 ? '#10B981' : '#38BDF8' }}>
                        {cand.fuel_delta_kg > 0 ? `+${cand.fuel_delta_kg}` : cand.fuel_delta_kg} kg
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--muted)' }}>
                        ({cand.fuel_delta_percent > 0 ? `+${cand.fuel_delta_percent}` : cand.fuel_delta_percent}%)
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: 10, color: 'var(--muted)' }}>STATUS</div>
                      <div style={{ fontSize: 12, fontWeight: 600, marginTop: 2 }}>
                        <StatusBadge value={cand.status} />
                      </div>
                    </div>
                  </div>

                  <div style={{ marginTop: 12, display: 'flex', justifyContent: 'flex-end' }}>
                    <span style={{ fontSize: 11.5, color: isSelected ? 'var(--cyan)' : 'var(--muted)', fontWeight: 600 }}>
                      {isSelected ? '● Currently Selected' : 'Click to Compare'}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Selected Candidate Detailed Inspection & Map Trajectory Canvas */}
          {selectedCandidate && (
            <Card>
              <div className="section-heading">
                <div>
                  <h3>Interactive 4D Trajectory Route Inspection: {selectedCandidate.strategy_name}</h3>
                  <p className="muted">
                    Visual comparison of original trajectory vs approved/candidate recovery waypoints.
                  </p>
                </div>

                <div style={{ display: 'flex', gap: 8 }}>
                  {canApprove ? (
                    <>
                      <Button
                        variant="secondary"
                        size="sm"
                        icon="x"
                        onClick={() => setIsRejecting(true)}
                        disabled={selectedCandidate.status === 'REJECTED'}
                      >
                        Reject Candidate
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        icon="check"
                        onClick={() => setIsApproving(true)}
                        disabled={selectedCandidate.status === 'APPROVED'}
                        style={{
                          background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                          boxShadow: '0 0 14px rgba(16, 185, 129, 0.4)',
                        }}
                      >
                        {selectedCandidate.status === 'APPROVED' ? 'Already Approved' : 'Approve & Release OFP'}
                      </Button>
                    </>
                  ) : (
                    <div style={{ fontSize: 12, color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Icon name="lock" size="sm" />
                      <span>Role '{currentUser.roleTitle}' cannot sign dispatch releases. Switch to Dispatcher in topbar.</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Waypoints Table */}
              <div style={{ marginTop: 14 }}>
                <h4 style={{ fontSize: 13, marginBottom: 8, color: 'var(--cyan)' }}>
                  RECOVERY ROUTE 4D WAYPOINT NAVLOG ({selectedCandidate.waypoints?.length || 0} FIXES)
                </h4>
                <div style={{ overflowX: 'auto' }}>
                  <table className="table" style={{ width: '100%', fontSize: 12.5 }}>
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Waypoint Fix</th>
                        <th>Latitude</th>
                        <th>Longitude</th>
                        <th>Altitude</th>
                        <th>Est. Time</th>
                        <th>Speed</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(selectedCandidate.waypoints || []).map((wp, i) => (
                        <tr key={i} style={{ background: wp.name?.includes('DETOUR') || wp.name?.includes('BUFFER') || wp.name?.includes('CLIMB') ? 'rgba(56, 189, 248, 0.08)' : 'transparent' }}>
                          <td>{i + 1}</td>
                          <td>
                            <strong>{wp.name}</strong>
                            {(wp.name?.includes('DETOUR') || wp.name?.includes('BUFFER') || wp.name?.includes('CLIMB')) && (
                              <Badge tone="info" style={{ marginLeft: 6, fontSize: 10 }}>Diversion Fix</Badge>
                            )}
                          </td>
                          <td className="mono">{wp.lat?.toFixed(4)}°N</td>
                          <td className="mono">{wp.lon?.toFixed(4)}°E</td>
                          <td className="mono">FL{Math.floor((wp.alt || 36000) / 100)}</td>
                          <td className="mono">T+{wp.time_min || i * 20}m</td>
                          <td className="mono">{wp.speed_kts || 450} kts</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Rationale & Decision Explanation Block */}
              <div
                style={{
                  marginTop: 16,
                  padding: 14,
                  borderRadius: 10,
                  background: 'rgba(8, 15, 29, 0.6)',
                  border: '1px solid rgba(56, 189, 248, 0.2)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <Icon name="sparkles" size="sm" />
                  <strong style={{ fontSize: 13, color: 'var(--cyan)' }}>AI-Assisted Recovery Rationale</strong>
                </div>
                <p style={{ fontSize: 12.5, lineHeight: 1.5, color: 'var(--text)', margin: 0 }}>
                  By selecting <strong>{selectedCandidate.strategy_name}</strong>, flight {recoveryData.data.call_sign} bypasses the primary Multan convective storm cell and military TFR restriction. 
                  The expected flight delay of <strong>+{selectedCandidate.delay_minutes} minutes</strong> and fuel variance of <strong>{selectedCandidate.fuel_delta_kg > 0 ? `+${selectedCandidate.fuel_delta_kg}` : selectedCandidate.fuel_delta_kg} kg</strong> achieves an optimal safety margin, lowering aggregate 4D trajectory hazard score from <strong>{selectedCandidate.original_risk_score}</strong> down to <strong>{selectedCandidate.residual_risk_score}/100</strong>.
                </p>
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Formal Approval Modal */}
      {isApproving && (
        <Modal
          title={`Formal Operational Approval: ${selectedCandidate?.strategy_name}`}
          onClose={() => setIsApproving(false)}
        >
          <div className="stack" style={{ gap: 14 }}>
            <Alert tone="info" title="Aviation Dispatch Sign-Off Verification">
              <span>
                You are approving candidate route <strong>{selectedCandidate?.candidate_code}</strong> for flight <strong>{recoveryData.data?.call_sign}</strong>. 
                Upon confirmation, this action updates the 4D active trajectory, generates an Updated Operational Flight Plan (OFP), and stores an immutable record in the PostgreSQL audit database.
              </span>
            </Alert>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, padding: 12, background: 'rgba(0,0,0,0.3)', borderRadius: 8 }}>
              <div>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>AUTHORIZED DISPATCHER</div>
                <strong style={{ fontSize: 13, color: 'var(--cyan)' }}>{currentUser.fullName}</strong>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>Role: {currentUser.roleTitle}</div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>DISPATCH CREDENTIAL ID</div>
                <strong style={{ fontSize: 13 }}>{currentUser.dispatcherId}</strong>
                <div style={{ fontSize: 11, color: 'var(--muted)' }}>Integrity: SHA-256 Enabled</div>
              </div>
            </div>

            <label className="field">
              <span>Operational Dispatch Release Notes</span>
              <textarea
                className="input"
                rows={3}
                value={approvalNotes}
                onChange={(e) => setApprovalNotes(e.target.value)}
                placeholder="Enter dispatch reasoning or ATC clearance notes..."
              />
            </label>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
              <Button variant="ghost" onClick={() => setIsApproving(false)} disabled={submitting}>
                Cancel
              </Button>
              <Button
                variant="primary"
                icon="check"
                onClick={handleConfirmApproval}
                disabled={submitting}
                style={{
                  background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)',
                }}
              >
                {submitting ? 'Generating OFP & Logging Audit...' : 'Confirm Release & Sign OFP'}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Formal Rejection Modal */}
      {isRejecting && (
        <Modal
          title={`Reject Recovery Candidate: ${selectedCandidate?.strategy_name}`}
          onClose={() => setIsRejecting(false)}
        >
          <div className="stack" style={{ gap: 14 }}>
            <p className="muted" style={{ fontSize: 13 }}>
              Please record the technical or operational grounds for rejecting this recovery route candidate. 
              The rejection reason will be permanently committed to the security audit ledger.
            </p>

            <label className="field">
              <span>Rejection Rationale (Required)</span>
              <textarea
                className="input"
                rows={3}
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="State reason for rejection..."
              />
            </label>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 10 }}>
              <Button variant="ghost" onClick={() => setIsRejecting(false)} disabled={submitting}>
                Cancel
              </Button>
              <Button
                variant="danger"
                icon="x"
                onClick={handleConfirmRejection}
                disabled={submitting || !rejectionReason.trim()}
              >
                {submitting ? 'Recording Rejection...' : 'Confirm Rejection'}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </>
  )
}
