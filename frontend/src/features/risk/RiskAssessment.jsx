import { useEffect, useState } from 'react'
import { Alert, Badge, Button, Card, LoadingState, StatusBadge } from '../../components/ui.jsx'
import { Icon } from '../../components/icons.jsx'
import { evaluateFlightRisk, getActiveHazards, classifyNotam, getFlights } from '../../services/api.js'
import { useAuth } from '../../context/AuthContext.jsx'
import { useRouter } from '../../utils/router.jsx'

const SAMPLE_NOTAMS = [
  "A0482/26 NOTAMN Q) OPKR/QMRLC/IV/NBO/A/000/999/3131N07424E005 A) OPLA B) 2610240800 C) 2610241600 E) RWY 36R/18L CLSD DUE WIP.",
  "A0129/26 NOTAMN Q) OPKR/QNVAS/IV/BO/AE/000/999/2825N07018E025 A) OPKC B) 2610240400 C) 2610251800 E) RAHIM YAR KHAN VOR/DME RK 116.5MHZ U/S.",
  "B0993/26 NOTAMN Q) OPLA/QRTCA/IV/BO/W/000/450/2845N07006E050 A) OPLA B) 2610240600 C) 2610241800 E) AIRSPACE TEMPORARILY RESTRICTED FOR MILITARY TACTICAL FLIGHT DRILLS.",
  "C0241/26 NOTAMN Q) OPIS/QOBCE/IV/M/AE/000/010/3336N07251E005 A) OPIS B) 2610240001 C) 2610302359 E) TOWER CRANE ERECTED APRON EXPANSION HGT 180FT AGL LGTD.",
]

export default function RiskAssessment() {
  const { currentUser } = useAuth()
  const { navigate } = useRouter()

  const [flights, setFlights] = useState([])
  const [selectedFlightId, setSelectedFlightId] = useState('PK-781')
  const [evaluation, setEvaluation] = useState({ status: 'loading', data: null })
  const [hazards, setHazards] = useState([])

  // NOTAM Classifier Interactive State
  const [notamInput, setNotamInput] = useState(SAMPLE_NOTAMS[0])
  const [notamResult, setNotamResult] = useState(null)
  const [classifying, setClassifying] = useState(false)

  // Load flights and hazards
  useEffect(() => {
    getFlights()
      .then((res) => {
        if (res?.flights) setFlights(res.flights)
      })
      .catch(() => {})

    getActiveHazards()
      .then((res) => {
        if (res?.hazards) setHazards(res.hazards)
      })
      .catch(() => {})
  }, [])

  // Evaluate flight risk
  const runEvaluation = (fId) => {
    setEvaluation({ status: 'loading', data: null })
    evaluateFlightRisk(fId)
      .then((res) => {
        setEvaluation({ status: 'ready', data: res })
      })
      .catch((err) => {
        setEvaluation({ status: 'error', error: err })
      })
  }

  useEffect(() => {
    runEvaluation(selectedFlightId)
  }, [selectedFlightId])

  // Classify NOTAM
  const handleClassifyNotam = async () => {
    if (!notamInput.trim()) return
    setClassifying(true)
    try {
      const res = await classifyNotam(notamInput)
      setClassifying(false)
      setNotamResult(res)
    } catch {
      setClassifying(false)
    }
  }

  const evalData = evaluation.data

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: 20, margin: 0, fontWeight: 700 }}>4D Multi-Hazard Risk Assessment & NLP Classifier</h2>
          <p className="muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
            Multi-dimensional risk assessment integrating Doppler Weather, Space-Weather (SWPC Kp index), NOTAMs, and Airspace restrictions.
          </p>
        </div>

        {/* Flight Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 12.5, color: 'var(--muted)', fontWeight: 600 }}>INSPECT FLIGHT:</span>
          <select
            className="select"
            style={{ minWidth: 200, padding: '6px 12px', fontWeight: 600 }}
            value={selectedFlightId}
            onChange={(e) => setSelectedFlightId(e.target.value)}
          >
            {flights.map((f) => (
              <option key={f.id} value={f.id}>
                {f.call_sign} ({f.origin} → {f.destination})
              </option>
            ))}
          </select>
          <Button size="sm" icon="refresh" onClick={() => runEvaluation(selectedFlightId)}>
            Re-Scan
          </Button>
        </div>
      </div>

      {evaluation.status === 'loading' && <LoadingState label="Computing 4D trajectory multi-hazard risk and cascading synergy..." />}

      {evaluation.status === 'ready' && evalData && (
        <div className="stack" style={{ gap: 16 }}>
          {/* Main Risk Score Card */}
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 14 }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <h3 style={{ margin: 0, fontSize: 18 }}>Flight {evalData.flight_id} Multi-Hazard Risk</h3>
                  <Badge tone={evalData.overall_risk_score >= 65 ? 'critical' : evalData.overall_risk_score >= 35 ? 'elevated' : 'low'}>
                    {evalData.overall_risk_band}
                  </Badge>
                </div>
                <p className="muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
                  {evalData.recommended_action}
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase' }}>Aggregate Risk Score</div>
                  <div
                    style={{
                      fontSize: 28,
                      fontWeight: 800,
                      color: evalData.overall_risk_score >= 65 ? '#EF4444' : evalData.overall_risk_score >= 35 ? '#F59E0B' : '#10B981',
                    }}
                  >
                    {evalData.overall_risk_score}<span style={{ fontSize: 16, color: 'var(--muted)', fontWeight: 400 }}>/100</span>
                  </div>
                </div>

                {evalData.overall_risk_score >= 35 && (
                  <Button
                    variant="primary"
                    icon="arrow-right"
                    onClick={() => navigate('/workspace/recovery')}
                    style={{
                      background: 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)',
                    }}
                  >
                    Generate Recovery Routes
                  </Button>
                )}
              </div>
            </div>

            {/* 4 Multi-Hazard Dimension Gauges */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginTop: 16 }}>
              {/* Weather */}
              <div style={{ padding: 12, borderRadius: 8, background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(56, 189, 248, 0.15)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: '#38BDF8' }}>CONVECTIVE WEATHER</span>
                  <Badge tone={evalData.scores?.weather > 50 ? 'critical' : 'low'}>
                    {evalData.scores?.weather}/100
                  </Badge>
                </div>
                <div style={{ height: 6, width: '100%', background: '#1E293B', borderRadius: 999, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${evalData.scores?.weather || 0}%`, background: '#38BDF8' }} />
                </div>
                <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 6 }}>
                  Doppler reflectivity, microburst, icing
                </div>
              </div>

              {/* Space Weather */}
              <div style={{ padding: 12, borderRadius: 8, background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(168, 85, 247, 0.15)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: '#C084FC' }}>SPACE WEATHER (SWPC)</span>
                  <Badge tone={evalData.scores?.space_weather > 50 ? 'elevated' : 'low'}>
                    {evalData.scores?.space_weather}/100
                  </Badge>
                </div>
                <div style={{ height: 6, width: '100%', background: '#1E293B', borderRadius: 999, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${evalData.scores?.space_weather || 0}%`, background: '#C084FC' }} />
                </div>
                <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 6 }}>
                  Kp=6.7 geomagnetic storm & HF margin
                </div>
              </div>

              {/* NOTAMs */}
              <div style={{ padding: 12, borderRadius: 8, background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(245, 158, 11, 0.15)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: '#FBBF24' }}>NOTAM RESTRICTIONS</span>
                  <Badge tone={evalData.scores?.notam > 50 ? 'elevated' : 'low'}>
                    {evalData.scores?.notam}/100
                  </Badge>
                </div>
                <div style={{ height: 6, width: '100%', background: '#1E293B', borderRadius: 999, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${evalData.scores?.notam || 0}%`, background: '#FBBF24' }} />
                </div>
                <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 6 }}>
                  Runway closure & nav aid outages
                </div>
              </div>

              {/* Airspace Conflicts */}
              <div style={{ padding: 12, borderRadius: 8, background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(239, 68, 68, 0.15)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: '#F87171' }}>AIRSPACE TFR CONFLICT</span>
                  <Badge tone={evalData.scores?.conflict > 50 ? 'critical' : 'low'}>
                    {evalData.scores?.conflict}/100
                  </Badge>
                </div>
                <div style={{ height: 6, width: '100%', background: '#1E293B', borderRadius: 999, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${evalData.scores?.conflict || 0}%`, background: '#F87171' }} />
                </div>
                <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 6 }}>
                  Military corridors & 4D separation
                </div>
              </div>
            </div>

            {/* AI-Assisted Narrative & Cascading Factor Breakdown */}
            <div
              style={{
                marginTop: 16,
                padding: 14,
                borderRadius: 10,
                background: 'rgba(8, 15, 29, 0.7)',
                border: '1px solid rgba(56, 189, 248, 0.25)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <Icon name="sparkles" size="sm" />
                <strong style={{ fontSize: 13, color: 'var(--cyan)' }}>AI-Assisted Multi-Hazard Decision Explanation</strong>
              </div>
              <p style={{ fontSize: 13, lineHeight: 1.5, margin: '0 0 10px', color: 'var(--text)' }}>
                {evalData.ai_explanation}
              </p>

              {evalData.cascading_factors?.length > 0 && (
                <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 10 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', marginBottom: 6, textTransform: 'uppercase' }}>
                    Cascading & Synergy Amplification Factors:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: '#E2E8F0', lineHeight: 1.6 }}>
                    {evalData.cascading_factors.map((factor, i) => (
                      <li key={i}>{factor}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Card>

          {/* Active Airspace Hazards & NOTAM NLP Classifier Grid */}
          <div className="grid-2">
            {/* Active Airspace Spatial Hazards */}
            <Card>
              <div className="section-heading">
                <div>
                  <h3>Active Monitored Hazards ({hazards.length})</h3>
                  <p className="muted">Live spatial polygons and weather cells within Karachi & Lahore FIRs.</p>
                </div>
                <Badge tone="elevated">Live PostgreSQL</Badge>
              </div>

              <div className="stack" style={{ gap: 10, marginTop: 10, maxHeight: 380, overflowY: 'auto' }}>
                {hazards.map((h) => (
                  <div
                    key={h.id}
                    style={{
                      padding: 12,
                      borderRadius: 8,
                      background: 'rgba(15, 23, 42, 0.5)',
                      border: '1px solid rgba(56, 189, 248, 0.12)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                      <strong style={{ fontSize: 13, color: 'var(--text)' }}>{h.title}</strong>
                      <Badge tone={h.severity === 'SEVERE' ? 'critical' : h.severity === 'HIGH' ? 'elevated' : 'info'}>
                        {h.severity}
                      </Badge>
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.4 }}>
                      {h.description}
                    </div>
                    <div style={{ display: 'flex', gap: 12, marginTop: 6, fontSize: 11, color: 'var(--cyan)' }}>
                      <span>Sector: {h.lat}°N, {h.lon}°E</span>
                      <span>Radius: {h.radius_km} km</span>
                      <span>FL: {Math.floor(h.min_alt_ft / 100)} - {Math.floor(h.max_alt_ft / 100)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* Fine-Tuned DistilBERT NOTAM NLP Classifier */}
            <Card>
              <div className="section-heading">
                <div>
                  <h3>DistilBERT NOTAM NLP Classifier</h3>
                  <p className="muted">Fine-tuned sequence classification model for aeronautical NOTAM notices.</p>
                </div>
                <Badge tone="low">DistilBERT Ready</Badge>
              </div>

              <div className="stack" style={{ gap: 12, marginTop: 10 }}>
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 11, color: 'var(--muted)', alignSelf: 'center', fontWeight: 600 }}>SAMPLES:</span>
                  {SAMPLE_NOTAMS.map((s, idx) => (
                    <button
                      key={idx}
                      className="btn btn-ghost btn-sm"
                      style={{ fontSize: 11, padding: '2px 8px' }}
                      onClick={() => setNotamInput(s)}
                    >
                      Sample {idx + 1}
                    </button>
                  ))}
                </div>

                <label className="field" style={{ margin: 0 }}>
                  <textarea
                    className="input mono"
                    rows={4}
                    value={notamInput}
                    onChange={(e) => setNotamInput(e.target.value)}
                    placeholder="Enter ICAO NOTAM text string..."
                    style={{ fontSize: 12 }}
                  />
                </label>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 11, color: 'var(--muted)' }}>
                    Trained on Estrellajer/Knots NOTAM Dataset
                  </span>
                  <Button size="sm" icon="sparkles" onClick={handleClassifyNotam} disabled={classifying}>
                    {classifying ? 'Inference Running...' : 'Classify with DistilBERT'}
                  </Button>
                </div>

                {/* Classification Result Card */}
                {notamResult && (
                  <div
                    style={{
                      padding: 12,
                      borderRadius: 8,
                      background: 'rgba(8, 15, 29, 0.7)',
                      border: '1px solid #10B981',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <strong style={{ fontSize: 13, color: '#10B981' }}>
                        PREDICTED: {notamResult.predicted_category}
                      </strong>
                      <Badge tone="low">{notamResult.confidence_percent}% Confidence</Badge>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, fontSize: 11.5, marginTop: 8 }}>
                      <div>
                        <span style={{ color: 'var(--muted)' }}>AIRPORT: </span>
                        <strong>{notamResult.airport || 'EN-ROUTE'}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--muted)' }}>RUNWAY: </span>
                        <strong>{notamResult.runway || 'N/A'}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--muted)' }}>STATUS: </span>
                        <strong>{notamResult.status}</strong>
                      </div>
                    </div>

                    <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 8 }}>
                      Model: <strong>{notamResult.model}</strong>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          </div>
        </div>
      )}
    </>
  )
}
