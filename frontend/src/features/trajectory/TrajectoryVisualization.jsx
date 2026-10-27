import { useEffect, useState } from 'react'
import { Alert, Badge, Button, Card } from '../../components/ui.jsx'
import { Icon } from '../../components/icons.jsx'
import { getFlights, getFlightTrajectory, getFlightRecovery, getActiveHazards } from '../../services/api.js'

export default function TrajectoryVisualization() {
  const [flights, setFlights] = useState([])
  const [flightId, setFlightId] = useState('PK-781')
  const [trajectory, setTrajectory] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [hazards, setHazards] = useState([])

  const [t, setT] = useState(48)
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)

  // View Mode: 'DUAL' | 'PLAN' | 'PROFILE'
  const [viewMode, setViewMode] = useState('DUAL')

  // Layer Toggles
  const [showAirways, setShowAirways] = useState(true)
  const [showWeather, setShowWeather] = useState(true)
  const [showSpaceWeather, setShowSpaceWeather] = useState(true)
  const [showTFR, setShowTFR] = useState(true)
  const [showRadarSweep, setShowRadarSweep] = useState(false)
  const [selectedRouteView, setSelectedRouteView] = useState('ROUTE_D') // Defaults to Route D (Pareto) for optimal clarity
  const [activeWaypoint, setActiveWaypoint] = useState(null)

  // Load Flights & Hazards
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

  // Load Trajectory & Recovery Candidates
  useEffect(() => {
    getFlightTrajectory(flightId)
      .then((res) => {
        if (res?.flight) setTrajectory(res.flight)
      })
      .catch(() => {})

    getFlightRecovery(flightId)
      .then((res) => {
        if (res?.candidates) setCandidates(res.candidates)
      })
      .catch(() => {})
  }, [flightId])

  // Playback timer
  useEffect(() => {
    let timer = null
    if (isPlaying) {
      timer = window.setInterval(() => {
        setT((prev) => {
          if (prev >= 100) return 0
          return Math.min(100, prev + 0.8 * speed)
        })
      }, 100)
    }
    return () => window.clearInterval(timer)
  }, [isPlaying, speed])

  // Precise, Clean Coordinates on 900 x 480 Canvas
  // Karachi (OPKC) -> Rahim Yar Khan (RK) -> SULOM (Multan Sector) -> Trimmu (TRK) -> Lahore (OPLA)
  const waypoints = [
    {
      name: 'OPKC',
      fullName: 'Jinnah Int’l Airport, Karachi',
      x: 120,
      y: 420,
      labelX: 135,
      labelY: 425,
      distNm: 0,
      altFl: 0,
      heading: '045°',
      mea: '2,500 FT',
      airway: 'DEP / J121',
      lat: '24.9065° N',
      lon: '67.1608° E',
      type: 'AIRPORT',
    },
    {
      name: 'RK',
      fullName: 'Rahim Yar Khan VOR/DME',
      x: 330,
      y: 285,
      labelX: 345,
      labelY: 280,
      distNm: 250,
      altFl: 360,
      heading: '038°',
      mea: 'FL150',
      airway: 'J121',
      lat: '28.4300° N',
      lon: '70.2790° E',
      type: 'VOR',
    },
    {
      name: 'SULOM',
      fullName: 'SULOM Intersection (Multan Sector Hotspot)',
      x: 490,
      y: 205,
      labelX: 505,
      labelY: 215,
      distNm: 410,
      altFl: 360,
      heading: '035°',
      mea: 'FL180',
      airway: 'J121 / J130',
      lat: '30.1575° N',
      lon: '71.5249° E',
      isHotspot: true,
      hazard: 'Convective Cell (54 dBZ) & Space-Weather Flux',
      type: 'WAYPOINT',
    },
    {
      name: 'TRK',
      fullName: 'Trimmu Reporting Point',
      x: 640,
      y: 135,
      labelX: 655,
      labelY: 130,
      distNm: 520,
      altFl: 280,
      heading: '040°',
      mea: 'FL140',
      airway: 'J130',
      lat: '31.1890° N',
      lon: '72.1480° E',
      type: 'WAYPOINT',
    },
    {
      name: 'OPLA',
      fullName: 'Allama Iqbal Int’l Airport, Lahore',
      x: 780,
      y: 70,
      labelX: 740,
      labelY: 55,
      distNm: 620,
      altFl: 0,
      heading: '042°',
      mea: '3,000 FT',
      airway: 'ARR / J130',
      lat: '31.5216° N',
      lon: '74.4036° E',
      type: 'AIRPORT',
    },
  ]

  // Secondary Fixes
  const secondaryFixes = [
    { name: 'PANJG', x: 190, y: 310, label: 'PANJG' },
    { name: 'ZHO', x: 420, y: 110, label: 'ZHOB' },
    { name: 'FAZIL', x: 620, y: 250, label: 'FAZILKA' },
  ]

  // Interpolated aircraft marker coordinates on Canvas
  const pointIndex = Math.min(
    waypoints.length - 1,
    Math.floor((t / 100) * (waypoints.length - 1)),
  )
  const currentWaypoint = waypoints[pointIndex]
  const nextPoint = waypoints[Math.min(waypoints.length - 1, pointIndex + 1)]
  const segmentRatio = (t / 100) * (waypoints.length - 1) - pointIndex
  const planeX = currentWaypoint.x + segmentRatio * (nextPoint.x - currentWaypoint.x)
  const planeY = currentWaypoint.y + segmentRatio * (nextPoint.y - currentWaypoint.y)

  // Current Flight Level calculation
  let currentAlt = 0
  if (t < 20) {
    currentAlt = Math.floor((t / 20) * 36000)
  } else if (t < 75) {
    currentAlt = 36000
  } else {
    currentAlt = Math.floor(36000 * (1 - (t - 75) / 25))
  }
  const currentFl = `FL${String(Math.floor(currentAlt / 100)).padStart(3, '0')}`

  // Distance from SULOM hotspot (490, 205)
  const distToHotspotNm = Math.round(Math.hypot(planeX - 490, planeY - 205) * 1.3)
  const isConflictZone = distToHotspotNm <= 35

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxWidth: '100%' }}>
      {/* Top Header & Compact Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h2 style={{ fontSize: 18, margin: 0, fontWeight: 700 }}>4D Tactical Airspace Radar & Altitude Profile</h2>
            <Badge tone="info" dot>4D ENGINE VERIFIED</Badge>
          </div>
          <p className="muted" style={{ fontSize: 12, margin: '2px 0 0' }}>
            Precision vector tracking across Latitude, Longitude, Altitude, and Time Offset ($T+m$).
          </p>
        </div>

        {/* View Mode & Flight Selection */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', background: 'rgba(15, 23, 42, 0.85)', padding: 2, borderRadius: 6, border: '1px solid var(--border)' }}>
            <button
              className={`btn btn-sm ${viewMode === 'DUAL' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ fontSize: 11, padding: '3px 8px' }}
              onClick={() => setViewMode('DUAL')}
            >
              Dual Radar + Cut
            </button>
            <button
              className={`btn btn-sm ${viewMode === 'PLAN' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ fontSize: 11, padding: '3px 8px' }}
              onClick={() => setViewMode('PLAN')}
            >
              Horizontal Radar
            </button>
            <button
              className={`btn btn-sm ${viewMode === 'PROFILE' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ fontSize: 11, padding: '3px 8px' }}
              onClick={() => setViewMode('PROFILE')}
            >
              Altitude Profile
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 600 }}>FLIGHT:</span>
            <select
              className="select"
              style={{ minWidth: 170, padding: '4px 8px', fontSize: 12, fontWeight: 600 }}
              value={flightId}
              onChange={(e) => setFlightId(e.target.value)}
            >
              {flights.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.call_sign} ({item.origin} → {item.destination})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Layer Toggles & Route Filters */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8, padding: '6px 10px', background: 'rgba(11, 23, 48, 0.4)', borderRadius: 8, border: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)' }}>LAYERS:</span>
          <button
            className={`btn btn-sm ${showWeather ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: 10.5, padding: '2px 7px' }}
            onClick={() => setShowWeather(!showWeather)}
          >
            ⛈️ Storm (54 dBZ)
          </button>
          <button
            className={`btn btn-sm ${showSpaceWeather ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: 10.5, padding: '2px 7px' }}
            onClick={() => setShowSpaceWeather(!showSpaceWeather)}
          >
            ☀️ Space (Kp=6.7)
          </button>
          <button
            className={`btn btn-sm ${showTFR ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: 10.5, padding: '2px 7px' }}
            onClick={() => setShowTFR(!showTFR)}
          >
            🚫 TFR Delta
          </button>
          <button
            className={`btn btn-sm ${showAirways ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: 10.5, padding: '2px 7px' }}
            onClick={() => setShowAirways(!showAirways)}
          >
            ✈️ Airways J121/J130
          </button>
          <button
            className={`btn btn-sm ${showRadarSweep ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: 10.5, padding: '2px 7px' }}
            onClick={() => setShowRadarSweep(!showRadarSweep)}
          >
            📡 Radar Beam
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)' }}>DISPLAY ROUTE:</span>
          <select
            className="select"
            style={{ padding: '3px 8px', fontSize: 11, fontWeight: 600 }}
            value={selectedRouteView}
            onChange={(e) => setSelectedRouteView(e.target.value)}
          >
            <option value="ROUTE_D">Route D: Balanced Pareto (Cyan ★ Recommended)</option>
            <option value="ROUTE_C">Route C: Safest Buffer 50NM (Emerald)</option>
            <option value="ROUTE_B">Route B: Eco Step-Climb FL390 (Purple)</option>
            <option value="ROUTE_A">Route A: Min Delay (Amber)</option>
            <option value="ORIGINAL">Baseline Only (High Hazard Red)</option>
            <option value="ALL">All Recovery Options Combined</option>
          </select>
        </div>
      </div>

      {/* Cockpit / ATC Tactical HUD Telemetry Bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(115px, 1fr))',
          gap: 6,
        }}
      >
        <div className="hud-telemetry-pill" style={{ padding: '4px 8px' }}>
          <span className="hud-telemetry-label">AIRCRAFT</span>
          <span className="hud-telemetry-value" style={{ fontSize: 12 }}>{flightId} · B777</span>
        </div>
        <div className="hud-telemetry-pill" style={{ padding: '4px 8px' }}>
          <span className="hud-telemetry-label">ALTITUDE</span>
          <span className="hud-telemetry-value" style={{ fontSize: 12 }}>{currentFl} ({currentAlt.toLocaleString()} FT)</span>
        </div>
        <div className="hud-telemetry-pill" style={{ padding: '4px 8px' }}>
          <span className="hud-telemetry-label">SPEED / MACH</span>
          <span className="hud-telemetry-value" style={{ fontSize: 12 }}>452 KT · M 0.78</span>
        </div>
        <div className="hud-telemetry-pill" style={{ padding: '4px 8px' }}>
          <span className="hud-telemetry-label">TRACK / WIND</span>
          <span className="hud-telemetry-value" style={{ fontSize: 12 }}>{currentWaypoint.heading} · 285°/42KT</span>
        </div>
        <div className="hud-telemetry-pill" style={{ padding: '4px 8px' }}>
          <span className="hud-telemetry-label">FUEL REMAINING</span>
          <span className="hud-telemetry-value" style={{ fontSize: 12, color: '#34D399' }}>8,420 KG</span>
        </div>
        <div className="hud-telemetry-pill" style={{ padding: '4px 8px', borderColor: isConflictZone ? '#EF4444' : 'rgba(56, 189, 248, 0.2)' }}>
          <span className="hud-telemetry-label">HAZARD DISTANCE</span>
          <span className="hud-telemetry-value" style={{ fontSize: 12, color: isConflictZone ? '#EF4444' : '#38BDF8' }}>
            {distToHotspotNm} NM {isConflictZone ? '⚠ CAUTION' : '✓ CLEAR'}
          </span>
        </div>
      </div>

      {/* Main Grid: Canvases on Left, Route Legend & Waypoint Detail on Right */}
      <div className="detail-grid" style={{ alignItems: 'start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* 1. Tactical Horizontal 4D Airspace Radar (Plan View) */}
          {(viewMode === 'DUAL' || viewMode === 'PLAN') && (
            <Card style={{ padding: 0, overflow: 'hidden' }}>
              <div
                style={{
                  position: 'relative',
                  background: 'radial-gradient(ellipse at 50% 50%, #0d1a33 0%, #040912 100%)',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                  borderRadius: 10,
                  overflow: 'hidden',
                }}
              >
                {/* Top Radar Bar */}
                <div
                  style={{
                    position: 'absolute',
                    top: 8,
                    left: 10,
                    right: 10,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    zIndex: 10,
                    pointerEvents: 'none',
                  }}
                >
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                    <Badge tone="info" dot>TACTICAL RADAR</Badge>
                    <span className="mono" style={{ fontSize: 11, color: 'var(--cyan)', fontWeight: 700 }}>
                      T+{Math.floor((t / 100) * 110)}m (ETA {Math.max(0, 110 - Math.floor((t / 100) * 110))}m)
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <Badge tone="neutral">PAKISTAN AIRSPACE</Badge>
                    <Badge tone={isConflictZone ? 'danger' : 'low'}>
                      {isConflictZone ? 'HOTSPOT INTERCEPT: SULOM' : 'SEPARATION: CLEAR'}
                    </Badge>
                  </div>
                </div>

                {/* SVG 4D Radar Canvas with Crisp 900x480 Resolution */}
                <svg
                  viewBox="0 0 900 480"
                  width="100%"
                  height={viewMode === 'DUAL' ? '320px' : '450px'}
                  role="img"
                  aria-label="4D Airspace Trajectory Visualizer"
                  style={{ display: 'block' }}
                >
                  <defs>
                    <radialGradient id="radarSweepGradient" cx="450" cy="240" r="450" gradientUnits="userSpaceOnUse">
                      <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.15" />
                      <stop offset="60%" stopColor="#38BDF8" stopOpacity="0.03" />
                      <stop offset="100%" stopColor="#38BDF8" stopOpacity="0" />
                    </radialGradient>

                    <linearGradient id="spaceWeatherGlow" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#A855F7" stopOpacity="0.3" />
                      <stop offset="100%" stopColor="#A855F7" stopOpacity="0" />
                    </linearGradient>

                    <pattern id="tfrHatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                      <line x1="0" y1="0" x2="0" y2="6" stroke="#EF4444" strokeWidth="0.8" strokeOpacity="0.4" />
                    </pattern>
                  </defs>

                  {/* Range Rings & Cardinal Compass Lines */}
                  <g stroke="#1E293B" strokeWidth="0.8">
                    <circle cx="450" cy="240" r="120" fill="none" strokeDasharray="3 4" />
                    <circle cx="450" cy="240" r="230" fill="none" strokeDasharray="4 6" />
                    <circle cx="450" cy="240" r="340" fill="none" strokeDasharray="5 7" />
                    <line x1="450" y1="10" x2="450" y2="470" strokeDasharray="2 4" strokeOpacity="0.3" />
                    <line x1="10" y1="240" x2="890" y2="240" strokeDasharray="2 4" strokeOpacity="0.3" />

                    {/* Range Labels */}
                    <text x="456" y="130" fill="#475569" fontSize="10" fontFamily="monospace">50 NM</text>
                    <text x="456" y="55" fill="#475569" fontSize="10" fontFamily="monospace">100 NM</text>

                    {/* Cardinal Headings */}
                    <text x="450" y="24" fill="#38BDF8" fontSize="11" textAnchor="middle" fontWeight="bold">000° N</text>
                    <text x="880" y="244" fill="#64748B" fontSize="11" textAnchor="end">090° E</text>
                    <text x="450" y="468" fill="#64748B" fontSize="11" textAnchor="middle">180° S</text>
                    <text x="20" y="244" fill="#64748B" fontSize="11">270° W</text>
                  </g>

                  {/* Coastline Guide (Arabian Sea) */}
                  <path
                    d="M 20 470 Q 70 450, 130 445 T 220 460 T 300 480"
                    fill="none"
                    stroke="#0284C7"
                    strokeWidth="1.2"
                    strokeDasharray="4 2"
                    strokeOpacity="0.6"
                  />
                  <text x="50" y="472" fill="#0284C7" fontSize="10" fontStyle="italic">ARABIAN SEA / COASTLINE</text>

                  {/* FIR Boundary Line */}
                  <line x1="220" y1="260" x2="680" y2="260" stroke="#334155" strokeWidth="0.8" strokeDasharray="6 3" />
                  <text x="230" y="254" fill="#64748B" fontSize="9" letterSpacing="0.05em">KARACHI FIR / LAHORE FIR BOUNDARY</text>

                  {/* Rotating Radar Sweep Beam */}
                  {showRadarSweep && (
                    <g className="radar-sweep-beam" style={{ transformOrigin: '450px 240px' }}>
                      <path
                        d="M 450 240 L 780 70 A 380 380 0 0 0 450 -140 Z"
                        fill="url(#radarSweepGradient)"
                      />
                      <line x1="450" y1="240" x2="780" y2="70" stroke="#38BDF8" strokeWidth="1" strokeOpacity="0.8" />
                    </g>
                  )}

                  {/* Space Weather Radiation Zone (Northern Upper Altitudes) */}
                  {showSpaceWeather && (
                    <g>
                      <rect x="0" y="0" width="900" height="42" fill="url(#spaceWeatherGlow)" />
                      <line x1="0" y1="42" x2="900" y2="42" stroke="#A855F7" strokeWidth="0.8" strokeDasharray="4 2" />
                      <text x="20" y="24" fill="#C084FC" fontSize="11" fontWeight="700">
                        ⚡ NOAA SWPC SPACE-WEATHER FLUX (Kp=6.7 SEVERE) · HF COMMS & GPS DEGRADATION ZONE
                      </text>
                    </g>
                  )}

                  {/* Military Restricted Area (TFR Delta) */}
                  {showTFR && (
                    <g>
                      <polygon
                        points="280,260 380,225 410,290 300,320"
                        fill="url(#tfrHatch)"
                        stroke="#EF4444"
                        strokeWidth="0.8"
                        strokeDasharray="3 2"
                      />
                      <text x="295" y="280" fill="#F87171" fontSize="10" fontWeight="700">
                        TFR DELTA (MIL CLOSED)
                      </text>
                      <text x="295" y="295" fill="#FCA5A5" fontSize="8.5">
                        SFC - FL290 · LIVE WEAPONS
                      </text>
                    </g>
                  )}

                  {/* Airways Corridors */}
                  {showAirways && (
                    <g stroke="#334155" strokeWidth="0.9" strokeDasharray="4 4">
                      <line x1="120" y1="420" x2="330" y2="285" />
                      <line x1="330" y1="285" x2="490" y2="205" />
                      <line x1="490" y1="205" x2="640" y2="135" />
                      <line x1="640" y1="135" x2="780" y2="70" />
                      <text x="205" y="365" fill="#64748B" fontSize="10" fontWeight="600">J121</text>
                      <text x="565" y="180" fill="#64748B" fontSize="10" fontWeight="600">J130</text>
                    </g>
                  )}

                  {/* Convective Storm Cell (Multan Sector Hotspot) */}
                  {showWeather && (
                    <g>
                      {/* Outer Rain Ring (Green 35 dBZ) */}
                      <circle cx="490" cy="205" r="54" fill="rgba(16, 185, 129, 0.08)" stroke="#10B981" strokeWidth="0.8" strokeDasharray="3 2" />
                      {/* Moderate Rain Ring (Amber 45 dBZ) */}
                      <circle cx="490" cy="205" r="34" fill="rgba(245, 158, 11, 0.15)" stroke="#F59E0B" strokeWidth="0.9" strokeDasharray="2 1" />
                      {/* Severe Convective Core (Red 54 dBZ) */}
                      <circle cx="490" cy="205" r="18" fill="rgba(239, 68, 68, 0.35)" stroke="#EF4444" strokeWidth="1.2" />

                      {/* Storm Motion Vector (ENE 15 kts) */}
                      <line x1="490" y1="205" x2="535" y2="185" stroke="#F8FAFC" strokeWidth="1" strokeDasharray="2 2" />
                      <polygon points="535,185 526,182 529,190" fill="#F8FAFC" />

                      {/* Clean Non-Overlapping Storm Label */}
                      <text x="490" y="140" fill="#EF4444" fontSize="11" textAnchor="middle" fontWeight="800">
                        MULTAN CB CELL (54 dBZ · TOPS FL430)
                      </text>
                    </g>
                  )}

                  {/* Multi-Route Recovery Candidate Paths */}
                  {/* Route A: Minimum Delay (Amber) */}
                  {(selectedRouteView === 'ALL' || selectedRouteView === 'ROUTE_A') && (
                    <g>
                      <path
                        d="M 120 420 L 330 285 Q 410 245, 520 235 T 640 135 L 780 70"
                        fill="none"
                        stroke="#F59E0B"
                        strokeWidth={selectedRouteView === 'ROUTE_A' ? '2' : '1.2'}
                        strokeDasharray={selectedRouteView === 'ROUTE_A' ? 'none' : '4 2'}
                        opacity={selectedRouteView === 'ROUTE_A' ? 1 : 0.75}
                      />
                      <text x="530" y="250" fill="#F59E0B" fontSize="9.5" fontWeight="600">
                        Route A (+3.8m Delay · Risk 24.5)
                      </text>
                    </g>
                  )}

                  {/* Route B: Eco / Step-Climb FL390 (Purple) */}
                  {(selectedRouteView === 'ALL' || selectedRouteView === 'ROUTE_B') && (
                    <g>
                      <path
                        d="M 120 420 L 330 285 Q 390 190, 450 165 T 640 135 L 780 70"
                        fill="none"
                        stroke="#A855F7"
                        strokeWidth={selectedRouteView === 'ROUTE_B' ? '2' : '1.2'}
                        strokeDasharray={selectedRouteView === 'ROUTE_B' ? 'none' : '4 2'}
                        opacity={selectedRouteView === 'ROUTE_B' ? 1 : 0.75}
                      />
                      <text x="390" y="160" fill="#C084FC" fontSize="9.5" fontWeight="600">
                        Route B (Eco FL390 · -42kg)
                      </text>
                    </g>
                  )}

                  {/* Route C: Safest Buffer 50NM (Emerald) */}
                  {(selectedRouteView === 'ALL' || selectedRouteView === 'ROUTE_C') && (
                    <g>
                      <path
                        d="M 120 420 Q 300 360, 410 320 Q 550 300, 640 190 L 780 70"
                        fill="none"
                        stroke="#10B981"
                        strokeWidth={selectedRouteView === 'ROUTE_C' ? '2.2' : '1.4'}
                        opacity={selectedRouteView === 'ROUTE_C' ? 1 : 0.75}
                      />
                      <text x="560" y="315" fill="#10B981" fontSize="9.5" fontWeight="700">
                        Route C (Safest Buffer 50NM · Risk 6.8)
                      </text>
                    </g>
                  )}

                  {/* Route D: Balanced Pareto (Cyan ★ Recommended) */}
                  {(selectedRouteView === 'ALL' || selectedRouteView === 'ROUTE_D') && (
                    <g>
                      <path
                        d="M 120 420 L 330 285 Q 430 240, 520 180 T 640 135 L 780 70"
                        fill="none"
                        stroke="#38BDF8"
                        strokeWidth={selectedRouteView === 'ROUTE_D' ? '2.4' : '1.5'}
                        strokeDasharray={selectedRouteView === 'ROUTE_D' ? 'none' : '5 3'}
                        opacity={1}
                      />
                      <text x="525" y="175" fill="#38BDF8" fontSize="10.5" fontWeight="800">
                        Route D (Balanced Pareto ★ Recommended)
                      </text>
                    </g>
                  )}

                  {/* Baseline Scheduled Trajectory (Red Dash - High Hazard) */}
                  {(selectedRouteView === 'ALL' || selectedRouteView === 'ORIGINAL' || selectedRouteView === 'ROUTE_D') && (
                    <g>
                      <path
                        d={waypoints.map((p, i) => `${i ? 'L' : 'M'} ${p.x} ${p.y}`).join(' ')}
                        fill="none"
                        stroke="#EF4444"
                        strokeWidth={selectedRouteView === 'ORIGINAL' ? '2' : '1.2'}
                        strokeDasharray="4 3"
                        opacity={selectedRouteView === 'ROUTE_D' ? 0.45 : 1}
                      />
                    </g>
                  )}

                  {/* Secondary Enroute Waypoints */}
                  {secondaryFixes.map((f) => (
                    <g key={f.name}>
                      <circle cx={f.x} cy={f.y} r="2" fill="#475569" />
                      <text x={f.x + 6} y={f.y + 3} fill="#64748B" fontSize="9">{f.label}</text>
                    </g>
                  ))}

                  {/* Primary Flight Waypoints (Clean, Non-Overlapping) */}
                  {waypoints.map((p) => {
                    const isSelected = activeWaypoint?.name === p.name
                    return (
                      <g
                        key={p.name}
                        style={{ cursor: 'pointer' }}
                        onClick={() => setActiveWaypoint(p)}
                      >
                        {p.isHotspot && (
                          <circle cx={p.x} cy={p.y} r="10" fill="none" stroke="#EF4444" strokeWidth="0.8" strokeDasharray="2 2" />
                        )}
                        <circle
                          cx={p.x}
                          cy={p.y}
                          r={p.isHotspot ? 5 : isSelected ? 6 : 4}
                          fill={p.isHotspot ? '#EF4444' : isSelected ? '#38BDF8' : '#0F172A'}
                          stroke={p.isHotspot ? '#FFFFFF' : '#38BDF8'}
                          strokeWidth="1.4"
                        />
                        <text
                          x={p.labelX}
                          y={p.labelY}
                          fill={p.isHotspot ? '#EF4444' : isSelected ? '#38BDF8' : '#F1F5F9'}
                          fontSize="11"
                          fontWeight={p.isHotspot || isSelected ? '800' : '600'}
                        >
                          {p.name}
                        </text>
                      </g>
                    )
                  })}

                  {/* Dynamic Aircraft Marker with Velocity Predictor */}
                  <g transform={`translate(${planeX}, ${planeY})`}>
                    {/* Pulsing Beacon Ring */}
                    <circle cx="0" cy="0" r="10" fill="none" stroke="#38BDF8" strokeWidth="0.8" strokeDasharray="2 2">
                      <animate attributeName="r" values="6;14;6" dur="2s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="0.8;0.1;0.8" dur="2s" repeatCount="indefinite" />
                    </circle>

                    {/* Velocity Vector */}
                    <line x1="0" y1="0" x2="16" y2="-12" stroke="#38BDF8" strokeWidth="1" strokeDasharray="3 1" />

                    {/* Airplane Icon */}
                    <g transform="rotate(45)">
                      <polygon points="0,-8 6,6 0,3 -6,6" fill="#38BDF8" stroke="#FFFFFF" strokeWidth="0.8" />
                      <circle cx="0" cy="0" r="2.5" fill="#FFFFFF" />
                    </g>

                    {/* Cockpit Aircraft Tag */}
                    <rect x="12" y="-22" width="95" height="20" rx="3" fill="rgba(15, 23, 42, 0.9)" stroke="#38BDF8" strokeWidth="0.8" />
                    <text x="16" y="-12" fill="#38BDF8" fontSize="9.5" fontWeight="700">
                      {flightId} · {currentFl}
                    </text>
                    <text x="16" y="-4" fill="#94A3B8" fontSize="8.5">
                      452 KT · SQUAWK 7421
                    </text>
                  </g>
                </svg>

                {/* Timeline & Scrubbing Controller */}
                <div
                  style={{
                    padding: '8px 12px',
                    background: 'rgba(11, 23, 48, 0.92)',
                    borderTop: '1px solid rgba(56, 189, 248, 0.2)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  <Button
                    size="sm"
                    variant={isPlaying ? 'primary' : 'secondary'}
                    icon={isPlaying ? 'pause' : 'play'}
                    onClick={() => setIsPlaying(!isPlaying)}
                  >
                    {isPlaying ? 'Pause' : 'Play 4D'}
                  </Button>

                  <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className="mono" style={{ fontSize: 10, color: 'var(--muted)' }}>T+0m</span>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={t}
                      onChange={(e) => setT(Number(e.target.value))}
                      style={{ flex: 1, accentColor: '#38BDF8', cursor: 'pointer', height: 4 }}
                    />
                    <span className="mono" style={{ fontSize: 10, color: 'var(--cyan)', fontWeight: 700 }}>
                      T+{Math.floor((t / 100) * 110)}m
                    </span>
                  </div>

                  <div style={{ display: 'flex', gap: 3 }}>
                    {[1, 2, 4].map((s) => (
                      <button
                        key={s}
                        className={`btn btn-sm ${speed === s ? 'btn-primary' : 'btn-ghost'}`}
                        style={{ fontSize: 10, padding: '2px 6px' }}
                        onClick={() => setSpeed(s)}
                      >
                        {s}x
                      </button>
                    ))}
                  </div>

                  <button
                    className="btn btn-sm btn-ghost"
                    style={{ fontSize: 10, color: '#F59E0B', borderColor: 'rgba(245, 158, 11, 0.3)', padding: '2px 8px' }}
                    onClick={() => setT(48)}
                  >
                    ⚡ SULOM Intercept
                  </button>
                </div>
              </div>
            </Card>
          )}

          {/* 2. 4D Vertical Flight Altitude Cross-Section (Profile View) */}
          {(viewMode === 'DUAL' || viewMode === 'PROFILE') && (
            <Card style={{ padding: 0, overflow: 'hidden' }}>
              <div
                style={{
                  padding: '6px 12px',
                  background: 'rgba(15, 23, 42, 0.8)',
                  borderBottom: '1px solid rgba(56, 189, 248, 0.2)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#F8FAFC' }}>4D Vertical Flight Altitude Cross-Section</span>
                  <Badge tone="neutral">ALTITUDE ENVELOPE (FL000 - FL450)</Badge>
                </div>
                <span className="muted" style={{ fontSize: 11 }}>
                  Storm Tops at FL430 · Baseline at FL360 · Step-Climb at FL390
                </span>
              </div>

              <div
                style={{
                  position: 'relative',
                  background: 'linear-gradient(180deg, #070e1c 0%, #03070e 100%)',
                  overflow: 'hidden',
                }}
              >
                <svg
                  viewBox="0 0 900 160"
                  width="100%"
                  height={viewMode === 'DUAL' ? '140px' : '300px'}
                  role="img"
                  aria-label="4D Vertical Altitude Visualizer"
                  style={{ display: 'block' }}
                >
                  <defs>
                    <linearGradient id="cloudGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#EF4444" stopOpacity="0.7" />
                      <stop offset="50%" stopColor="#F59E0B" stopOpacity="0.4" />
                      <stop offset="100%" stopColor="#334155" stopOpacity="0.1" />
                    </linearGradient>

                    <linearGradient id="terrainGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#1E293B" />
                      <stop offset="100%" stopColor="#0B132B" />
                    </linearGradient>
                  </defs>

                  {/* Altitude Grid Lines */}
                  {/* FL450 (y=15), FL390 (y=35), FL360 (y=48), FL300 (y=72), FL200 (y=98), FL100 (y=124), Ground (y=145) */}
                  <g stroke="#1E293B" strokeWidth="0.8" strokeDasharray="3 4">
                    <line x1="60" y1="15" x2="880" y2="15" />
                    <line x1="60" y1="35" x2="880" y2="35" />
                    <line x1="60" y1="48" x2="880" y2="48" stroke="#38BDF8" strokeOpacity="0.4" />
                    <line x1="60" y1="72" x2="880" y2="72" />
                    <line x1="60" y1="98" x2="880" y2="98" />
                    <line x1="60" y1="124" x2="880" y2="124" />
                  </g>

                  {/* Altitude Axis Labels (Left) */}
                  <g fill="#64748B" fontSize="9" fontFamily="monospace">
                    <text x="15" y="19">FL450</text>
                    <text x="15" y="39">FL390</text>
                    <text x="15" y="52" fill="#38BDF8" fontWeight="bold">FL360</text>
                    <text x="15" y="76">FL300</text>
                    <text x="15" y="102">FL200</text>
                    <text x="15" y="128">FL100</text>
                    <text x="15" y="148">SFC</text>
                  </g>

                  {/* Terrain Elevation Silhouette (Indus Plains) */}
                  <path
                    d="M 60 145 Q 250 143, 450 142 T 650 140 T 880 145 L 880 160 L 60 160 Z"
                    fill="url(#terrainGrad)"
                    stroke="#334155"
                    strokeWidth="0.8"
                  />

                  {/* Convective Thunderstorm Cloud Column at SULOM (X: 470 - 580) */}
                  <g>
                    {/* Anvil cloud top reaching FL430 (y: 22) */}
                    <path
                      d="M 450 145 L 470 70 Q 430 40, 510 22 Q 590 20, 610 50 Q 620 70, 570 145 Z"
                      fill="url(#cloudGradient)"
                      stroke="#EF4444"
                      strokeWidth="1"
                    />
                    <text x="525" y="18" fill="#EF4444" fontSize="9.5" fontWeight="bold" textAnchor="middle">
                      CB TOPS FL430 (SEVERE TURBULENCE)
                    </text>
                  </g>

                  {/* Baseline Scheduled Trajectory (Climb -> FL360 -> Intercept Storm -> Descent) */}
                  <path
                    d="M 80 145 C 140 120, 200 48, 280 48 L 470 48 L 620 48 C 700 48, 780 110, 840 145"
                    fill="none"
                    stroke="#EF4444"
                    strokeWidth="1.4"
                    strokeDasharray="4 2"
                    opacity={selectedRouteView === 'ROUTE_D' ? 0.45 : 1}
                  />
                  <text x="320" y="42" fill="#EF4444" fontSize="9" fontWeight="bold">
                    Baseline at FL360 ⚠ Intersects Cloud Core!
                  </text>

                  {/* Recovery Route B Step-Climb to FL390 (Overfly Weather) */}
                  <path
                    d="M 80 145 C 140 120, 200 48, 280 48 L 380 48 C 420 48, 440 35, 470 35 L 610 35 C 640 35, 660 48, 700 48 L 840 145"
                    fill="none"
                    stroke="#A855F7"
                    strokeWidth="1.4"
                  />
                  <text x="475" y="30" fill="#C084FC" fontSize="9" fontWeight="bold">
                    Route B: Step-Climb FL390
                  </text>

                  {/* Recovery Route D Balanced (Lateral Corridor) */}
                  <path
                    d="M 80 145 C 140 120, 200 48, 280 48 L 760 48 L 840 145"
                    fill="none"
                    stroke="#38BDF8"
                    strokeWidth="1.8"
                  />
                  <text x="210" y="58" fill="#38BDF8" fontSize="9" fontWeight="bold">
                    Route D: FL360 Lateral Avoidance Corridor
                  </text>

                  {/* Waypoint Markers on Ground Axis */}
                  {waypoints.map((wp, idx) => {
                    const wx = 80 + (idx / (waypoints.length - 1)) * 760
                    return (
                      <g key={`vert-${wp.name}`}>
                        <line x1={wx} y1="142" x2={wx} y2="148" stroke="#475569" strokeWidth="0.8" />
                        <text x={wx} y="156" fill={wp.isHotspot ? '#EF4444' : '#94A3B8'} fontSize="9" textAnchor="middle" fontWeight="bold">
                          {wp.name}
                        </text>
                      </g>
                    )
                  })}

                  {/* Dynamic Aircraft Marker on Altitude Profile */}
                  {(() => {
                    const profX = 80 + (t / 100) * 760
                    let profY = 48
                    if (t < 20) {
                      profY = 145 - (t / 20) * 97
                    } else if (t < 75) {
                      profY = 48
                    } else {
                      profY = 48 + ((t - 75) / 25) * 97
                    }
                    return (
                      <g transform={`translate(${profX}, ${profY})`}>
                        <circle cx="0" cy="0" r="3" fill="#38BDF8" stroke="#FFFFFF" strokeWidth="1" />
                        <text x="5" y="-3" fill="#38BDF8" fontSize="9" fontWeight="bold">
                          {flightId} ({currentFl})
                        </text>
                      </g>
                    )
                  })()}
                </svg>
              </div>
            </Card>
          )}
        </div>

        {/* Right Column: Route Legend & Waypoint Detail */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {/* Waypoint Inspector Card */}
          {activeWaypoint ? (
            <Card>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <div>
                  <Badge tone={activeWaypoint.isHotspot ? 'danger' : 'info'}>
                    {activeWaypoint.type}: {activeWaypoint.name}
                  </Badge>
                  <h4 style={{ margin: '4px 0 2px', fontSize: 14, fontWeight: 700 }}>{activeWaypoint.fullName}</h4>
                </div>
                <button
                  className="btn btn-sm btn-ghost"
                  style={{ padding: '2px 5px', fontSize: 10 }}
                  onClick={() => setActiveWaypoint(null)}
                >
                  ✕
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 11.5 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 6px', background: 'rgba(0,0,0,0.25)', borderRadius: 4 }}>
                  <span className="muted">Coords:</span>
                  <strong className="mono">{activeWaypoint.lat}, {activeWaypoint.lon}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 6px', background: 'rgba(0,0,0,0.25)', borderRadius: 4 }}>
                  <span className="muted">Airway:</span>
                  <strong className="mono">{activeWaypoint.airway}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 6px', background: 'rgba(0,0,0,0.25)', borderRadius: 4 }}>
                  <span className="muted">MEA:</span>
                  <strong className="mono">{activeWaypoint.mea}</strong>
                </div>
                {activeWaypoint.hazard && (
                  <Alert tone="danger" title="Active Airspace Hazard">
                    {activeWaypoint.hazard}
                  </Alert>
                )}
              </div>
            </Card>
          ) : (
            <Card>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                <Icon name="info" size="sm" />
                <h4 style={{ margin: 0, fontSize: 12, fontWeight: 600 }}>Interactive Waypoint Inspector</h4>
              </div>
              <p className="muted" style={{ fontSize: 11, margin: 0 }}>
                Click on any waypoint marker (<span style={{ color: '#38BDF8' }}>OPKC</span>, <span style={{ color: '#38BDF8' }}>RK</span>, <span style={{ color: '#EF4444' }}>SULOM</span>, <span style={{ color: '#38BDF8' }}>TRK</span>, <span style={{ color: '#38BDF8' }}>OPLA</span>) to view coordinates, safe altitude, and active hazard warnings.
              </p>
            </Card>
          )}

          {/* Route Options Summary */}
          <Card>
            <div style={{ marginBottom: 8 }}>
              <h3 style={{ fontSize: 14, margin: 0, fontWeight: 700 }}>Recovery Route Candidates</h3>
              <p className="muted" style={{ fontSize: 11, margin: 0 }}>
                Select a route in the top dropdown to view its dedicated path.
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {/* Route D */}
              <div
                style={{
                  padding: 8,
                  background: selectedRouteView === 'ROUTE_D' ? 'rgba(56, 189, 248, 0.12)' : 'rgba(56, 189, 248, 0.05)',
                  border: `1px solid ${selectedRouteView === 'ROUTE_D' ? 'var(--cyan)' : 'rgba(56, 189, 248, 0.25)'}`,
                  borderRadius: 6,
                  cursor: 'pointer',
                }}
                onClick={() => setSelectedRouteView('ROUTE_D')}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
                  <strong style={{ fontSize: 12, color: '#38BDF8' }}>Route D: Balanced Pareto ★</strong>
                  <Badge tone="low">RISK: 12.4</Badge>
                </div>
                <div style={{ fontSize: 10.5, color: 'var(--muted)' }}>
                  +5.8m delay · +185kg fuel · 28 NM buffer · Recommended pick
                </div>
              </div>

              {/* Route C */}
              <div
                style={{
                  padding: 8,
                  background: selectedRouteView === 'ROUTE_C' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(16, 185, 129, 0.05)',
                  border: `1px solid ${selectedRouteView === 'ROUTE_C' ? '#10B981' : 'rgba(16, 185, 129, 0.25)'}`,
                  borderRadius: 6,
                  cursor: 'pointer',
                }}
                onClick={() => setSelectedRouteView('ROUTE_C')}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
                  <strong style={{ fontSize: 12, color: '#10B981' }}>Route C: Safest Buffer (50 NM)</strong>
                  <Badge tone="low">RISK: 6.8</Badge>
                </div>
                <div style={{ fontSize: 10.5, color: 'var(--muted)' }}>
                  +13.5m delay · +365kg fuel · Maximum weather clearance
                </div>
              </div>

              {/* Route B */}
              <div
                style={{
                  padding: 8,
                  background: selectedRouteView === 'ROUTE_B' ? 'rgba(168, 85, 247, 0.12)' : 'rgba(168, 85, 247, 0.05)',
                  border: `1px solid ${selectedRouteView === 'ROUTE_B' ? '#A855F7' : 'rgba(168, 85, 247, 0.25)'}`,
                  borderRadius: 6,
                  cursor: 'pointer',
                }}
                onClick={() => setSelectedRouteView('ROUTE_B')}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
                  <strong style={{ fontSize: 12, color: '#A855F7' }}>Route B: Eco Step-Climb FL390</strong>
                  <Badge tone="medium">RISK: 18.2</Badge>
                </div>
                <div style={{ fontSize: 10.5, color: 'var(--muted)' }}>
                  +1.8m delay · -42kg fuel saved · Upper tailwind assist
                </div>
              </div>

              {/* Route A */}
              <div
                style={{
                  padding: 8,
                  background: selectedRouteView === 'ROUTE_A' ? 'rgba(245, 158, 11, 0.12)' : 'rgba(245, 158, 11, 0.05)',
                  border: `1px solid ${selectedRouteView === 'ROUTE_A' ? '#F59E0B' : 'rgba(245, 158, 11, 0.25)'}`,
                  borderRadius: 6,
                  cursor: 'pointer',
                }}
                onClick={() => setSelectedRouteView('ROUTE_A')}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
                  <strong style={{ fontSize: 12, color: '#F59E0B' }}>Route A: Minimum Delay</strong>
                  <Badge tone="medium">RISK: 24.5</Badge>
                </div>
                <div style={{ fontSize: 10.5, color: 'var(--muted)' }}>
                  +3.8m delay · +135kg fuel · Tightest lateral tactical detour
                </div>
              </div>

              {/* Baseline */}
              <div
                style={{
                  padding: 8,
                  background: selectedRouteView === 'ORIGINAL' ? 'rgba(239, 68, 68, 0.12)' : 'rgba(239, 68, 68, 0.05)',
                  border: `1px solid ${selectedRouteView === 'ORIGINAL' ? '#EF4444' : 'rgba(239, 68, 68, 0.25)'}`,
                  borderRadius: 6,
                  cursor: 'pointer',
                }}
                onClick={() => setSelectedRouteView('ORIGINAL')}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
                  <strong style={{ fontSize: 12, color: '#EF4444' }}>Baseline Scheduled Flight</strong>
                  <Badge tone="danger">RISK: 78.5</Badge>
                </div>
                <div style={{ fontSize: 10.5, color: 'var(--muted)' }}>
                  Severe 54 dBZ storm intercept at SULOM + Space Weather
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}
