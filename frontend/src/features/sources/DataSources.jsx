import { useState } from 'react'
import { Alert, Badge, Button, Card, LoadingState, StatusBadge } from '../../components/ui.jsx'
import { dataSources, sampleNotams } from '../../data/demoData.js'
import { prepareNotam, simulateNotamClassification } from '../../services/api.js'

const scenarios = [
  {
    id: 'SCN-HIST-OCT',
    name: 'Karachi–Lahore Corridor Monsoon Hotspot (Oct 2026)',
    detail: 'Simulates convective weather cells along airway W12 west of Multan. Evaluates lateral offsets around SULOM waypoint.',
    type: 'Historical Archive',
    focus: 'Weather & Lateral Recovery',
  },
  {
    id: 'SCN-NOTAM-OPLA',
    name: 'Lahore (OPLA) Runway 36L Maintenance Closure',
    detail: 'Tests DistilBERT classification on runway maintenance NOTAM. Flags airport code and reveals extraction requirements for validity timestamps.',
    type: 'Experimental NLP',
    focus: 'Aerodrome NOTAM Screening',
  },
  {
    id: 'SCN-MIL-RESTRICT',
    name: 'Southern Punjab Tactical Airspace Activation',
    detail: 'Simulates military exercise airspace reservation up to FL220. Evaluates re-routing around temporary restricted area R-112.',
    type: 'Tactical Airspace',
    focus: 'Airspace Restriction & Reroute',
  },
]

export default function DataSources() {
  const [selectedNotamPreset, setSelectedNotamPreset] = useState(sampleNotams[0])
  const [text, setText] = useState(sampleNotams[0].text)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [scenario, setScenario] = useState(scenarios[0])

  async function runNotam() {
    setBusy(true)
    setError(null)
    setResult(null)

    try {
      const payload = await prepareNotam(text)
      setResult(payload)
    } catch {
      // If backend is offline or timed out, seamlessly execute high-fidelity NLP simulation
      const fallbackResult = simulateNotamClassification(text)
      setResult(fallbackResult)
    } finally {
      setBusy(false)
    }
  }

  const handleSelectPreset = (preset) => {
    setSelectedNotamPreset(preset)
    setText(preset.text)
    setResult(null)
    setError(null)
  }

  return (
    <>
      <Alert tone="info" title="Rigorous Connection Language Protocol.">
        <span>
          A source is NEVER labelled <strong style={{ color: '#22C55E' }}>Connected</strong> unless an
          active communication handshake has been verified this session. Historical CSVs, local ML models,
          synthetic demo data, and unavailable live feeds remain explicitly partitioned.
        </span>
      </Alert>

      {/* Data Source Governance Cards */}
      <div className="grid-3">
        {dataSources.map((source) => (
          <Card key={source.id}>
            <div className="source-meta">
              <h3 style={{ fontSize: 15 }}>{source.name}</h3>
              <StatusBadge
                value={
                  source.status.includes('Unavailable')
                    ? 'Unavailable'
                    : source.type
                }
              />
            </div>

            <div style={{ margin: '10px 0', fontSize: 13 }}>
              <div style={{ color: 'var(--cyan)', fontWeight: 600 }}>{source.type}</div>
              <div style={{ color: 'var(--text)', marginTop: 2 }}>{source.status}</div>
            </div>

            <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>
              <strong>Endpoint / Link:</strong> {source.connection}
            </div>

            <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 8 }}>
              <strong>Last Verified:</strong> {source.lastUpdate}
            </div>

            <p className="muted" style={{ fontSize: 12, lineHeight: 1.4, borderTop: '1px solid var(--border)', paddingTop: 8 }}>
              <strong>Limitation:</strong> {source.limitations}
            </p>
          </Card>
        ))}
      </div>

      {/* Scenarios & Interactive NOTAM Laboratory */}
      <div className="grid-2" style={{ marginTop: 16 }}>
        {/* Left Column: Research Scenarios */}
        <Card>
          <div className="section-heading">
            <div>
              <h3>Airspace Evaluation Scenarios</h3>
              <p className="muted">Standardized benchmark scenarios for testing the 4D auditor.</p>
            </div>
            <Badge tone="info">3 Benchmarks</Badge>
          </div>

          <div className="stack" style={{ marginTop: 12 }}>
            {scenarios.map((item) => (
              <button
                key={item.id}
                className="menu-item"
                onClick={() => setScenario(item)}
                style={{
                  border: item.id === scenario.id ? '1px solid var(--cyan)' : '1px solid var(--border)',
                  background: item.id === scenario.id ? 'rgba(53, 199, 232, 0.08)' : 'rgba(8, 15, 29, 0.4)',
                  padding: 14,
                  borderRadius: 10,
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <strong style={{ fontSize: 14, color: 'var(--text)' }}>{item.name}</strong>
                  <Badge tone="neutral">{item.focus}</Badge>
                </div>
                <div className="muted" style={{ fontSize: 12.5, marginTop: 4 }}>
                  {item.detail}
                </div>
              </button>
            ))}
          </div>

          <div
            style={{
              marginTop: 16,
              padding: 14,
              background: 'rgba(8, 15, 29, 0.6)',
              borderRadius: 10,
              border: '1px solid var(--border)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <Badge tone="low">Active Scenario</Badge>
              <span style={{ fontWeight: 600, color: 'var(--text)', fontSize: 13 }}>{scenario.name}</span>
            </div>
            <p className="muted" style={{ fontSize: 12.5, lineHeight: 1.5 }}>
              {scenario.detail}
            </p>
          </div>
        </Card>

        {/* Right Column: Interactive NOTAM Screening Workbench */}
        <Card>
          <div className="section-heading">
            <div>
              <h3>Experimental NOTAM Screening (NLP)</h3>
              <p className="muted">FastAPI POST /api/notam/prepare with local DistilBERT model.</p>
            </div>
            <Badge tone="info">DistilBERT Inference</Badge>
          </div>

          {/* Sample Preset Buttons */}
          <div style={{ marginBottom: 10 }}>
            <span className="muted" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
              Quick Presets:
            </span>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {sampleNotams.map((p) => (
                <button
                  key={p.id}
                  className={`btn btn-sm ${selectedNotamPreset.id === p.id ? 'btn-primary' : 'btn-ghost'}`}
                  onClick={() => handleSelectPreset(p)}
                >
                  {p.title}
                </button>
              ))}
            </div>
          </div>

          <label className="field">
            <span>Aeronautical NOTAM Text (ICAO Format)</span>
            <textarea
              className="textarea"
              style={{ minHeight: 110, fontSize: 12 }}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste raw NOTAM text here…"
            />
          </label>

          <Button
            variant="primary"
            icon="file"
            style={{ marginTop: 12, width: '100%' }}
            onClick={runNotam}
            disabled={busy || !text.trim()}
          >
            {busy ? 'Screening via NLP Model…' : 'Execute NOTAM Screening'}
          </Button>

          {busy ? <LoadingState label="Running DistilBERT classification…" /> : null}

          {error ? (
            <div style={{ marginTop: 12 }}>
              <Alert tone="warning">{error}</Alert>
            </div>
          ) : null}

          {result ? (
            <div
              style={{
                marginTop: 16,
                padding: 16,
                background: 'rgba(8, 15, 29, 0.7)',
                borderRadius: 12,
                border: '1px solid var(--border)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <span style={{ fontWeight: 700, color: 'var(--cyan)', fontSize: 14 }}>
                  Classification Output
                </span>
                <Badge tone={result.is_simulated ? 'info' : 'low'}>
                  {result.is_simulated ? 'Local Simulated Fallback' : 'Live PyTorch Output'}
                </Badge>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 10,
                  fontSize: 12.5,
                  marginBottom: 12,
                }}
              >
                <div>
                  <span className="muted">Predicted Category:</span>
                  <div style={{ fontWeight: 600, color: 'var(--text)', marginTop: 2 }}>
                    {result.predicted_category}
                  </div>
                </div>

                <div>
                  <span className="muted">Model Confidence:</span>
                  <div style={{ fontWeight: 700, color: '#22C55E', marginTop: 2 }}>
                    {result.confidence_percent}%
                  </div>
                </div>

                <div>
                  <span className="muted">Target Aerodrome:</span>
                  <div className="mono" style={{ color: 'var(--text)', marginTop: 2 }}>
                    {result.airport || <span style={{ color: '#F59E0B' }}>needs_extraction</span>}
                  </div>
                </div>

                <div>
                  <span className="muted">Affected Runway:</span>
                  <div className="mono" style={{ color: 'var(--text)', marginTop: 2 }}>
                    {result.runway || '—'}
                  </div>
                </div>

                <div>
                  <span className="muted">Valid From:</span>
                  <div style={{ color: '#F59E0B', fontSize: 11, marginTop: 2 }}>
                    {result.valid_from}
                  </div>
                </div>

                <div>
                  <span className="muted">Valid To:</span>
                  <div style={{ color: '#F59E0B', fontSize: 11, marginTop: 2 }}>
                    {result.valid_to}
                  </div>
                </div>
              </div>

              <div style={{ fontSize: 12, color: 'var(--muted)', borderTop: '1px solid var(--border)', paddingTop: 10 }}>
                <strong style={{ color: 'var(--text)' }}>NLP Extraction Note: </strong>
                {result.extraction_note}
              </div>
            </div>
          ) : null}
        </Card>
      </div>
    </>
  )
}
