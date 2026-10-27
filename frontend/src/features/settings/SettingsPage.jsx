import { useEffect, useState } from 'react'
import { Alert, Badge, Button, Card } from '../../components/ui.jsx'
import { Icon } from '../../components/icons.jsx'
import { PROJECT } from '../../data/demoData.js'
import { DEFAULT_BACKEND_ORIGIN, getApiBaseUrl, getHealth, setApiBaseUrl } from '../../services/api.js'
import { storageGet, storageSet } from '../../utils/format.js'

export default function SettingsPage() {
  const [density, setDensity] = useState(() => storageGet('skyrisk.density', 'comfortable'))
  const [grid, setGrid] = useState(() => storageGet('skyrisk.grid', false))
  const [glow, setGlow] = useState(() => storageGet('skyrisk.glow', true))
  const [timeDisplay, setTimeDisplay] = useState(() => storageGet('skyrisk.timeDisplay', 'utc'))
  const [distanceUnit, setDistanceUnit] = useState(() => storageGet('skyrisk.distanceUnit', 'NM'))
  const [altitudeUnit, setAltitudeUnit] = useState(() => storageGet('skyrisk.altitudeUnit', 'FL'))

  // Backend connection testing
  const [backendUrl, setBackendUrlState] = useState(() => getApiBaseUrl() || DEFAULT_BACKEND_ORIGIN)
  const [testResult, setTestResult] = useState(null)
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    storageSet('skyrisk.density', density)
    storageSet('skyrisk.grid', grid)
    storageSet('skyrisk.glow', glow)
    storageSet('skyrisk.timeDisplay', timeDisplay)
    storageSet('skyrisk.distanceUnit', distanceUnit)
    storageSet('skyrisk.altitudeUnit', altitudeUnit)

    document.documentElement.dataset.density = density
    document.documentElement.dataset.grid = grid ? 'on' : 'off'
    document.documentElement.dataset.glow = glow ? 'on' : 'off'
  }, [density, grid, glow, timeDisplay, distanceUnit, altitudeUnit])

  const handleTestBackend = async () => {
    setTesting(true)
    setTestResult(null)
    setApiBaseUrl(backendUrl)

    const start = performance.now()
    try {
      const data = await getHealth()
      const elapsed = Math.round(performance.now() - start)
      setTestResult({
        success: true,
        message: `Connected successfully in ${elapsed} ms. NOTAM model loaded: ${data.notam_model_loaded ? 'Yes' : 'No'}.`,
      })
    } catch (err) {
      setTestResult({
        success: false,
        message: `Connection failed: ${err.message}. Ensure backend is running with: .\\NOTAM-FineTuning\\.venv\\Scripts\\python.exe -m uvicorn main:app --app-dir backend --port 8000`,
      })
    } finally {
      setTesting(false)
    }
  }

  const handleResetDefaults = () => {
    setDensity('comfortable')
    setGrid(false)
    setGlow(true)
    setTimeDisplay('utc')
    setDistanceUnit('NM')
    setAltitudeUnit('FL')
    setBackendUrlState(DEFAULT_BACKEND_ORIGIN)
    setApiBaseUrl('')
    setTestResult(null)
  }

  return (
    <>
      <Alert tone="info" title="Local Settings & Architecture Parameters.">
        <span>
          Visual display settings, unit selections, and backend target origins are maintained
          in your local browser session. Adjusting them customizes your research auditing environment.
        </span>
      </Alert>

      <div className="settings-grid">
        {/* Display & Theming Card */}
        <Card>
          <div className="section-heading">
            <div>
              <h3>Display & Atmosphere</h3>
              <p className="muted">Configure visual density, glows, and radar grids.</p>
            </div>
            <Icon name="settings" size="sm" className="muted" />
          </div>

          <label className="toggle">
            <div>
              <strong>Interface Density</strong>
              <div className="muted" style={{ fontSize: 12 }}>Adjust spacing and typography padding</div>
            </div>
            <select
              className="select"
              value={density}
              onChange={(e) => setDensity(e.target.value)}
              style={{ maxWidth: 160 }}
            >
              <option value="comfortable">Comfortable</option>
              <option value="compact">Compact</option>
            </select>
          </label>

          <label className="toggle">
            <div>
              <strong>Tactical Airspace Grid</strong>
              <div className="muted" style={{ fontSize: 12 }}>Subtle coordinate grid across background</div>
            </div>
            <input
              type="checkbox"
              checked={grid}
              onChange={(e) => setGrid(e.target.checked)}
              style={{ width: 18, height: 18, accentColor: 'var(--cyan)' }}
            />
          </label>

          <label className="toggle">
            <div>
              <strong>Cyan Glow Effects</strong>
              <div className="muted" style={{ fontSize: 12 }}>Aerospace glowing accents on cards and buttons</div>
            </div>
            <input
              type="checkbox"
              checked={glow}
              onChange={(e) => setGlow(e.target.checked)}
              style={{ width: 18, height: 18, accentColor: 'var(--cyan)' }}
            />
          </label>

          <label className="toggle">
            <div>
              <strong>System Clock Context</strong>
              <div className="muted" style={{ fontSize: 12 }}>Standard aviation UTC vs local computer time</div>
            </div>
            <select
              className="select"
              value={timeDisplay}
              onChange={(e) => setTimeDisplay(e.target.value)}
              style={{ maxWidth: 160 }}
            >
              <option value="utc">Universal (UTC)</option>
              <option value="local">Local System Time</option>
            </select>
          </label>

          <label className="toggle">
            <div>
              <strong>Distance Units</strong>
              <div className="muted" style={{ fontSize: 12 }}>Aviation nautical miles vs metric kilometers</div>
            </div>
            <select
              className="select"
              value={distanceUnit}
              onChange={(e) => setDistanceUnit(e.target.value)}
              style={{ maxWidth: 160 }}
            >
              <option value="NM">Nautical Miles (NM)</option>
              <option value="KM">Kilometers (KM)</option>
            </select>
          </label>

          <div style={{ marginTop: 14 }}>
            <Button size="sm" variant="ghost" onClick={handleResetDefaults}>
              Reset Display Defaults
            </Button>
          </div>
        </Card>

        {/* Backend Endpoint Integration */}
        <Card>
          <div className="section-heading">
            <div>
              <h3>FastAPI Backend Integration</h3>
              <p className="muted">Configure target server for recovery summaries and NOTAM NLP.</p>
            </div>
            <Icon name="database" size="sm" className="muted" />
          </div>

          <label className="field" style={{ marginTop: 8 }}>
            <span>Backend Server URL</span>
            <input
              className="input mono"
              value={backendUrl}
              onChange={(e) => setBackendUrlState(e.target.value)}
              placeholder="http://127.0.0.1:8000"
            />
          </label>

          <div style={{ marginTop: 12, display: 'flex', gap: 10 }}>
            <Button
              variant="primary"
              size="sm"
              icon="refresh"
              onClick={handleTestBackend}
              disabled={testing}
            >
              {testing ? 'Pinging Endpoint…' : 'Ping /health Endpoint'}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setBackendUrlState(DEFAULT_BACKEND_ORIGIN)
                setApiBaseUrl('')
                setTestResult(null)
              }}
            >
              Reset to 127.0.0.1:8000
            </Button>
          </div>

          {testResult ? (
            <div style={{ marginTop: 14 }}>
              <Alert tone={testResult.success ? 'success' : 'warning'}>
                {testResult.message}
              </Alert>
            </div>
          ) : null}

          <div
            style={{
              marginTop: 16,
              padding: 12,
              background: 'rgba(8, 15, 29, 0.5)',
              borderRadius: 8,
              border: '1px solid var(--border)',
              fontSize: 12,
            }}
          >
            <strong style={{ color: 'var(--cyan)' }}>Terminal Command to Start Backend:</strong>
            <pre
              style={{
                margin: '6px 0 0',
                padding: 8,
                background: '#040810',
                borderRadius: 6,
                color: '#e8f0fc',
                fontFamily: 'var(--mono)',
                fontSize: 11,
                overflowX: 'auto',
              }}
            >
              .\NOTAM-FineTuning\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
            </pre>
          </div>
        </Card>

        {/* Prototype Scope Card */}
        <Card>
          <div className="section-heading">
            <div>
              <h3>Prototype Scope & Implementation</h3>
              <p className="muted">Implemented research capabilities.</p>
            </div>
            <Badge tone="low">Functional</Badge>
          </div>

          <ul className="muted" style={{ fontSize: 13, lineHeight: 1.7, paddingLeft: 18 }}>
            <li><strong style={{ color: 'var(--text)' }}>Overview Dashboard:</strong> Historical evaluations and readiness telemetry</li>
            <li><strong style={{ color: 'var(--text)' }}>Flight Operations:</strong> Multi-parameter search, catalog sorting, and flight dossiers</li>
            <li><strong style={{ color: 'var(--text)' }}>4D Trajectory Viewer:</strong> Animated timeline scrubber, waypoints, and altitude sync</li>
            <li><strong style={{ color: 'var(--text)' }}>Multi-Hazard Assessment:</strong> Transparent category formulas and sensitivity controls</li>
            <li><strong style={{ color: 'var(--text)' }}>Recovery Planning:</strong> Candidate route comparative metrics and geometry schema</li>
            <li><strong style={{ color: 'var(--text)' }}>OFP Management:</strong> Realistic ICAO research navlog drafts with fuel calculation</li>
            <li><strong style={{ color: 'var(--text)' }}>Approvals & Audit:</strong> Human-in-the-loop review workflow and event ledger</li>
            <li><strong style={{ color: 'var(--text)' }}>Data Sources & Scenarios:</strong> NOTAM screening with DistilBERT fallback</li>
            <li><strong style={{ color: 'var(--text)' }}>User Management:</strong> Role directory and permissions privilege matrix</li>
          </ul>
        </Card>

        {/* Research Limitations & Academic Attributions */}
        <Card>
          <div className="section-heading">
            <div>
              <h3>Academic Disclaimers & Ethics</h3>
              <p className="muted">Final year project research compliance.</p>
            </div>
            <Badge tone="elevated">Academic Integrity</Badge>
          </div>

          <div style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--muted)' }}>
            <p>
              <strong>{PROJECT.name}</strong> — {PROJECT.subtitle} is submitted in partial fulfillment
              of the requirements for the Bachelor of Science in Computer Science / Software Engineering.
            </p>
            <p style={{ marginTop: 10 }}>
              The software is strictly an academic research decision-support prototype. It does not
              interface with certified Air Traffic Management (ATM) automation or FAA/ICAO certified
              flight management systems (FMS).
            </p>
            <div style={{ marginTop: 12, padding: 10, background: 'rgba(245, 158, 11, 0.08)', borderRadius: 8, borderLeft: '3px solid #f59e0b' }}>
              <strong>Notice on Clearance:</strong> No automated route recommendation may be flown without
              independent pilot-in-command validation and certified ATC clearance.
            </div>
          </div>
        </Card>
      </div>
    </>
  )
}
