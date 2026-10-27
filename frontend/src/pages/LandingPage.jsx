import { capabilities, PROJECT, workflowSteps } from '../data/demoData.js'
import { Badge, Button, Card } from '../components/ui.jsx'
import { Icon } from '../components/icons.jsx'
import { Link, useRouter } from '../utils/router.jsx'

function RadarVisual() {
  return (
    <div className="radar-stage" aria-hidden="true">
      <div className="radar-grid" />
      <svg className="radar-svg" viewBox="0 0 400 400">
        <defs>
          <radialGradient id="scan" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#35C7E8" stopOpacity="0.22" />
            <stop offset="60%" stopColor="#35C7E8" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#35C7E8" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="routeGlow" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#35C7E8" />
            <stop offset="50%" stopColor="#648BFF" />
            <stop offset="100%" stopColor="#22C55E" />
          </linearGradient>
          <filter id="cyanGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Range rings */}
        <circle className="radar-pulse" cx="200" cy="200" r="160" fill="none" stroke="#35C7E8" strokeOpacity="0.3" />
        <circle cx="200" cy="200" r="160" fill="none" stroke="#253650" strokeWidth="1.2" />
        <circle cx="200" cy="200" r="120" fill="none" stroke="#253650" strokeWidth="1" strokeDasharray="4 4" />
        <circle cx="200" cy="200" r="80" fill="none" stroke="#253650" strokeWidth="1" />
        <circle cx="200" cy="200" r="40" fill="none" stroke="#648BFF" strokeOpacity="0.5" strokeWidth="1" />

        {/* Tactical crosshairs */}
        <line x1="200" y1="20" x2="200" y2="380" stroke="#253650" strokeWidth="0.8" />
        <line x1="20" y1="200" x2="380" y2="200" stroke="#253650" strokeWidth="0.8" />

        {/* Compass cardinal ticks */}
        <text x="200" y="36" fill="#91A4BD" fontSize="9" textAnchor="middle" fontWeight="600">360°</text>
        <text x="368" y="203" fill="#91A4BD" fontSize="9" textAnchor="middle" fontWeight="600">090°</text>
        <text x="200" y="372" fill="#91A4BD" fontSize="9" textAnchor="middle" fontWeight="600">180°</text>
        <text x="32" y="203" fill="#91A4BD" fontSize="9" textAnchor="middle" fontWeight="600">270°</text>

        {/* Radar sweep beam */}
        <g className="radar-sweep">
          <path d="M200 200 L200 40 A160 160 0 0 1 340 240 Z" fill="url(#scan)" />
          <line x1="200" y1="200" x2="200" y2="40" stroke="#35C7E8" strokeWidth="1.5" strokeOpacity="0.8" />
        </g>

        {/* Illustrative 4D flight trajectory */}
        <path
          d="M60 310 Q 140 260 210 200 T 340 90"
          fill="none"
          stroke="url(#routeGlow)"
          strokeWidth="2.5"
          filter="url(#cyanGlow)"
        />

        {/* Candidate lateral offset route */}
        <path
          d="M60 310 Q 120 240 180 170 T 340 90"
          fill="none"
          stroke="#648BFF"
          strokeWidth="1.6"
          strokeDasharray="4 3"
          strokeOpacity="0.75"
        />

        {/* Hotspot proxy zone */}
        <circle cx="210" cy="200" r="28" fill="rgba(245, 158, 11, 0.12)" stroke="#F59E0B" strokeWidth="1.2" strokeDasharray="3 3" />
        <text x="210" y="196" fill="#F59E0B" fontSize="8" textAnchor="middle" fontWeight="600">HOTSPOT PROXY</text>
        <text x="210" y="207" fill="#F59E0B" fontSize="7" textAnchor="middle">SULOM AREA</text>

        {/* Waypoint nodes */}
        <circle cx="60" cy="310" r="4.5" fill="#35C7E8" />
        <text x="60" y="326" fill="#91A4BD" fontSize="8" textAnchor="middle">OPKC</text>

        <circle cx="140" cy="254" r="3" fill="#E8F0FC" />
        <text x="140" y="246" fill="#91A4BD" fontSize="8" textAnchor="middle">RK</text>

        <circle cx="210" cy="200" r="4" fill="#F59E0B" />
        <text x="228" y="188" fill="#FDE68A" fontSize="8">FL360</text>

        <circle cx="280" cy="140" r="3" fill="#E8F0FC" />
        <text x="280" y="132" fill="#91A4BD" fontSize="8" textAnchor="middle">BODRO</text>

        <circle cx="340" cy="90" r="4.5" fill="#22C55E" />
        <text x="340" y="80" fill="#91A4BD" fontSize="8" textAnchor="middle">OPLA</text>

        {/* Moving aircraft symbol */}
        <g className="hero-plane">
          <g transform="translate(196, 178) rotate(42)">
            <path d="M12 2 L14 8 L22 11 L14 13 L15 19 L12 17 L9 19 L10 13 L2 11 L10 8 Z" fill="#E8F0FC" stroke="#35C7E8" strokeWidth="1" />
          </g>
        </g>
      </svg>
    </div>
  )
}

export default function LandingPage() {
  const { navigate } = useRouter()

  return (
    <div className="landing">
      <header className="landing-nav">
        <div className="brand" style={{ border: 0, height: 'auto', padding: 0 }}>
          <div className="brand-mark">
            <Icon name="radar" size="lg" />
          </div>
          <div>
            <strong style={{ fontSize: 16 }}>{PROJECT.name}</strong>
            <small style={{ display: 'block', color: 'var(--muted)', fontSize: 11 }}>
              {PROJECT.subtitle}
            </small>
          </div>
        </div>
        <nav aria-label="Landing page navigation">
          <a href="#capabilities">Capabilities</a>
          <a href="#engine">4D Engine</a>
          <a href="#workflow">Workflow</a>
          <a href="#limits">Limitations</a>
        </nav>
        <Button variant="primary" onClick={() => navigate('/workspace')}>
          Explore Command Center
        </Button>
      </header>

      <section className="hero">
        <div>
          <div className="kicker">
            <Icon name="sparkles" size="sm" />
            <span>Academic Research Prototype · Final Year Project</span>
          </div>
          <h1>Understand the Risk. See the Route in 4D.</h1>
          <p className="lead">
            SkyRisk Auditor is an academic 4D multi-hazard flight risk assessment and
            recovery decision-support prototype. It unifies historical trajectory inspection,
            experimental NOTAM NLP classification, and exploratory waypoint recovery comparisons.
          </p>
          <div className="lead-disclaimer">
            <strong>Research Prototype Notice:</strong> Not a certified aviation safety system.
            It does not issue operational ATC clearances, approve operational flight plans,
            or replace human dispatcher and pilot judgment.
          </div>
          <div className="cta-row">
            <Button variant="primary" size="lg" icon="radar" onClick={() => navigate('/workspace')}>
              Explore Command Center
            </Button>
            <Button
              size="lg"
              icon="layers"
              onClick={() => document.getElementById('capabilities')?.scrollIntoView({ behavior: 'smooth' })}
            >
              Explore Capabilities
            </Button>
          </div>
        </div>
        <RadarVisual />
      </section>

      <section className="landing-section" id="capabilities">
        <div className="section-heading">
          <div>
            <h2>Tactical Intelligence Capabilities</h2>
            <p>Six specialized research modules bounded by available datasets and explicit assumptions.</p>
          </div>
        </div>
        <div className="caps">
          {capabilities.map((item) => (
            <article key={item.title}>
              <div className="engine-icon-wrap">
                <Icon name={item.icon || 'shield'} size="lg" />
              </div>
              <h3>{item.title}</h3>
              <p className="muted" style={{ marginTop: 8, fontSize: 13.5, lineHeight: 1.5 }}>
                {item.body}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-section" id="engine">
        <div className="section-heading">
          <div>
            <h2>The 4D Engine Dimensions</h2>
            <p>Risk exposure analyzed across spatial coordinates, altitude profile, time window, and neighborhood context.</p>
          </div>
        </div>
        <div className="engine">
          <Card>
            <div className="engine-icon-wrap">
              <Icon name="route" size="lg" />
            </div>
            <h3>1. Trajectory (Space)</h3>
            <p className="muted" style={{ marginTop: 6, fontSize: 13 }}>
              Latitude and longitude waypoint path. Evaluated against historical FIR archives rather than live transponder feeds.
            </p>
          </Card>
          <Card>
            <div className="engine-icon-wrap">
              <Icon name="clock" size="lg" />
            </div>
            <h3>2. Time (4D Evolution)</h3>
            <p className="muted" style={{ marginTop: 6, fontSize: 13 }}>
              Temporal validity along route legs. Reflects historical 20–22 Oct 2026 windows without claiming live aircraft clock-sync.
            </p>
          </Card>
          <Card>
            <div className="engine-icon-wrap">
              <Icon name="activity" size="lg" />
            </div>
            <h3>3. Altitude (Vertical)</h3>
            <p className="muted" style={{ marginTop: 6, fontSize: 13 }}>
              Vertical flight levels (FL0 to FL400). Displays cruise snapshots; terrain clearance remains an explicit limitation.
            </p>
          </Card>
          <Card>
            <div className="engine-icon-wrap">
              <Icon name="radar" size="lg" />
            </div>
            <h3>4. Spatial Context</h3>
            <p className="muted" style={{ marginTop: 6, fontSize: 13 }}>
              Proximity to weather proxies and NOTAM boundaries. Proxies represent neighborhood likelihood, not in-situ telemetry.
            </p>
          </Card>
        </div>
      </section>

      <section className="landing-section" id="workflow">
        <div className="section-heading">
          <div>
            <h2>Human-in-the-Loop Review Workflow</h2>
            <p>A structured four-step methodology aligning data readiness, automated screening, and human decision-support.</p>
          </div>
        </div>
        <div className="steps">
          {workflowSteps.map((item) => (
            <article key={item.step}>
              <div className="step-num">STAGE {item.step}</div>
              <h3>{item.title}</h3>
              <p className="muted" style={{ marginTop: 8, fontSize: 13.5, lineHeight: 1.5 }}>
                {item.body}
              </p>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-section" id="limits">
        <Card style={{ borderLeft: '4px solid #38BDF8' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Badge tone="low">System Verification & Academic Scope</Badge>
            <span className="muted" style={{ fontSize: 12 }}>Continuous 4D Decision-Support Architecture</span>
          </div>
          <h2 style={{ margin: '14px 0 8px', fontSize: 18 }}>System Scope & Verification Pipeline</h2>
          <p className="muted" style={{ fontSize: 14, lineHeight: 1.6 }}>
            SkyRisk Auditor is an advanced academic research decision-support platform. All recovery candidates,
            4D spatial trajectories, and multi-hazard envelopes undergo verification through our{' '}
            <code style={{ color: '#38BDF8' }}>4D_VALIDATION_ACTIVE</code> pipeline and{' '}
            <code style={{ color: '#10B981' }}>CASCADING_ENGINE_VERIFIED</code> mathematical checks. NOTAM NLP
            confidence reflects transformer sequence certainty, and final dispatch release remains subject to
            human-in-the-loop Flight Dispatcher authorization.
          </p>
        </Card>
      </section>

      <section className="card final-cta">
        <div>
          <h2 style={{ fontSize: 22, color: '#ffffff' }}>Launch the Airspace Command Center</h2>
          <p className="muted" style={{ marginTop: 6 }}>
            Explore 10 interconnected modules with curated historical datasets, interactive 4D visualization, and live backend readiness checks.
          </p>
        </div>
        <Button variant="primary" size="lg" icon="radar" onClick={() => navigate('/workspace')}>
          Enter Command Center
        </Button>
      </section>

      <footer className="footer">
        <div>
          <strong style={{ color: 'var(--text)' }}>{PROJECT.name}</strong>
          <div style={{ marginTop: 4 }}>{PROJECT.disclaimer}</div>
        </div>
        <div style={{ display: 'flex', gap: 16 }}>
          <Link to="/workspace">Workspace</Link>
          <a href="#top" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>Back to Top</a>
        </div>
      </footer>
    </div>
  )
}
