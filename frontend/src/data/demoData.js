export const PROJECT = {
  name: 'SkyRisk Auditor',
  subtitle: '4D Tactical Airspace Risk Intelligence',
  disclaimer:
    'Academic research prototype. Not certified for operational flight decisions, ATC tactical dispatch, or regulatory compliance.',
}

export const capabilities = [
  {
    icon: 'map',
    title: '4D Trajectory Context',
    body: 'Places historical or illustrative tracks in space (lat/lon), altitude (FL), and time so evaluators can inspect route hazards in a unified 4D framework.',
  },
  {
    icon: 'shield',
    title: 'Multi-Hazard Risk Assessment',
    body: 'Categorizes risk indicators across convective weather proxies, NOTAM restrictions, and airspace density with explicit transparency for unmodeled gaps.',
  },
  {
    icon: 'file',
    title: 'Experimental NOTAM Screening',
    body: 'Evaluates free-text NOTAMs using a fine-tuned DistilBERT classifier. Classification confidence is an NLP metric, not an operational safety finding.',
  },
  {
    icon: 'route',
    title: 'Exploratory Recovery Planning',
    body: 'Compares lateral offsets and along-track shifts against baseline routes using proxy statistical indicators, geometric separation, and time deltas.',
  },
  {
    icon: 'clipboard',
    title: 'Human Review & Audit Trail',
    body: 'Ensures tactical decisions require human-in-the-loop review, recording timestamped actions and research draft sign-offs in a visible audit workflow.',
  },
  {
    icon: 'database',
    title: 'Data Source Transparency',
    body: 'Strictly distinguishes connected local models, historical evaluation CSVs, and demo placeholders from unavailable live ADS-B or certified terrain feeds.',
  },
]

export const workflowSteps = [
  {
    step: '01',
    title: 'Data Readiness Check',
    body: 'Confirm which historical archives, local models, and synthetic datasets are in scope before commencing risk evaluation.',
  },
  {
    step: '02',
    title: 'NOTAM NLP Screening',
    body: 'Screen raw aeronautical notices for classification categories and identify parameters that remain flags for manual extraction.',
  },
  {
    step: '03',
    title: '4D Trajectory Assessment',
    body: 'Evaluate multi-hazard exposure across waypoints, altitude profiles, and time windows without treating proposed weights as certified standards.',
  },
  {
    step: '04',
    title: 'Human Recovery Review',
    body: 'Inspect candidate route alternatives and record reviewer findings. The prototype never issues automated flight clearances.',
  },
]

export const demoFlights = [
  {
    id: 'HIST-2026-1020-014',
    callSign: 'PK-784',
    aircraft: 'B772 (Boeing 777-200ER)',
    origin: 'OPKC',
    originName: 'Jinnah Intl, Karachi',
    destination: 'OPLA',
    destinationName: 'Allama Iqbal Intl, Lahore',
    dateUtc: '2026-10-20T08:14:00Z',
    altitudeFt: 36000,
    cruiseFl: 'FL360',
    distanceNm: 554,
    status: 'Historical archive',
    dataMode: 'Demo data',
    phase: 'En route (Cruise)',
    indicatorBand: 'Elevated (illustrative)',
    notes: 'Primary evaluation flight for Karachi-Lahore corridor. Near convective hotspot proxy west of Multan.',
    waypoints: [
      { name: 'OPKC', fl: 0, lat: 24.90, lon: 67.16, time: '+00m', risk: 0.12 },
      { name: 'RK', fl: 180, lat: 25.80, lon: 68.10, time: '+18m', risk: 0.22 },
      { name: 'LALDO', fl: 320, lat: 27.20, lon: 69.40, time: '+38m', risk: 0.35 },
      { name: 'SULOM', fl: 360, lat: 29.10, lon: 70.80, time: '+64m', risk: 0.68, hotspot: true },
      { name: 'BODRO', fl: 360, lat: 30.50, lon: 72.20, time: '+82m', risk: 0.52 },
      { name: 'OPLA', fl: 0, lat: 31.52, lon: 74.40, time: '+110m', risk: 0.28 },
    ],
  },
  {
    id: 'HIST-2026-1021-031',
    callSign: 'PA-402',
    aircraft: 'A320 (Airbus A320-200)',
    origin: 'OPLA',
    originName: 'Allama Iqbal Intl, Lahore',
    destination: 'OPIS',
    destinationName: 'Islamabad Intl, Islamabad',
    dateUtc: '2026-10-21T11:42:00Z',
    altitudeFt: 28000,
    cruiseFl: 'FL280',
    distanceNm: 152,
    status: 'Historical archive',
    dataMode: 'Demo data',
    phase: 'Climb / Transition',
    indicatorBand: 'High (illustrative)',
    notes: 'Short-haul sector with simulated terminal area congestion and low cloud ceiling proxies.',
    waypoints: [
      { name: 'OPLA', fl: 0, lat: 31.52, lon: 74.40, time: '+00m', risk: 0.32 },
      { name: 'KALAT', fl: 180, lat: 32.10, lon: 73.90, time: '+12m', risk: 0.58 },
      { name: 'GUDDU', fl: 280, lat: 32.90, lon: 73.40, time: '+24m', risk: 0.74, hotspot: true },
      { name: 'OPIS', fl: 0, lat: 33.56, lon: 72.85, time: '+42m', risk: 0.41 },
    ],
  },
  {
    id: 'HIST-2026-1022-007',
    callSign: 'ER-501',
    aircraft: 'B738 (Boeing 737-800)',
    origin: 'OPIS',
    originName: 'Islamabad Intl, Islamabad',
    destination: 'OPKC',
    destinationName: 'Jinnah Intl, Karachi',
    dateUtc: '2026-10-22T16:05:00Z',
    altitudeFt: 34000,
    cruiseFl: 'FL340',
    distanceNm: 618,
    status: 'Needs review',
    dataMode: 'Demo data',
    phase: 'Descent snapshot',
    indicatorBand: 'Low (illustrative)',
    notes: 'Return trunk flight. Low illustrative hazard indicator is not a certified safety clearance.',
    waypoints: [
      { name: 'OPIS', fl: 0, lat: 33.56, lon: 72.85, time: '+00m', risk: 0.18 },
      { name: 'JHL', fl: 240, lat: 32.93, lon: 73.72, time: '+20m', risk: 0.25 },
      { name: 'BODRO', fl: 340, lat: 30.50, lon: 72.20, time: '+52m', risk: 0.28 },
      { name: 'SULOM', fl: 340, lat: 29.10, lon: 70.80, time: '+75m', risk: 0.31 },
      { name: 'LALDO', fl: 220, lat: 27.20, lon: 69.40, time: '+98m', risk: 0.20 },
      { name: 'OPKC', fl: 0, lat: 24.90, lon: 67.16, time: '+124m', risk: 0.15 },
    ],
  },
  {
    id: 'HIST-2026-1020-052',
    callSign: 'PK-688',
    aircraft: 'AT72 (ATR 72-500)',
    origin: 'OPKC',
    originName: 'Jinnah Intl, Karachi',
    destination: 'OPMT',
    destinationName: 'Multan Intl, Multan',
    dateUtc: '2026-10-20T19:28:00Z',
    altitudeFt: 22000,
    cruiseFl: 'FL220',
    distanceNm: 388,
    status: 'Historical archive',
    dataMode: 'Demo data',
    phase: 'Cruise',
    indicatorBand: 'Elevated (illustrative)',
    notes: 'Regional turboprop route. Subject to simulated lower-altitude thermal turbulence and military training airspace proximity.',
    waypoints: [
      { name: 'OPKC', fl: 0, lat: 24.90, lon: 67.16, time: '+00m', risk: 0.15 },
      { name: 'RK', fl: 160, lat: 25.80, lon: 68.10, time: '+22m', risk: 0.38 },
      { name: 'NWS', fl: 220, lat: 26.24, lon: 68.41, time: '+38m', risk: 0.45 },
      { name: 'SULOM', fl: 220, lat: 29.10, lon: 70.80, time: '+70m', risk: 0.62, hotspot: true },
      { name: 'OPMT', fl: 0, lat: 30.20, lon: 71.42, time: '+95m', risk: 0.30 },
    ],
  },
]

export const altitudeProfile = [
  { t: 0, fl: 0, label: 'DEP OPKC' },
  { t: 10, fl: 140, label: 'CLIMB' },
  { t: 20, fl: 260, label: 'TOC FL260' },
  { t: 35, fl: 360, label: 'CRUISE FL360' },
  { t: 55, fl: 360, label: 'HOTSPOT PROX' },
  { t: 72, fl: 360, label: 'STEP CRUISE' },
  { t: 84, fl: 210, label: 'TOD DESCENT' },
  { t: 94, fl: 70, label: 'APP STAR' },
  { t: 100, fl: 0, label: 'ARR OPLA' },
]

export const trajectoryPoints = [
  { x: 14, y: 72, label: 'OPKC (DEP)', desc: 'Karachi Jinnah Intl', fl: 'GND', speedKts: 160, heading: '038°' },
  { x: 26, y: 58, label: 'RK', desc: 'Rohri VOR corridor', fl: 'FL180', speedKts: 340, heading: '042°' },
  { x: 42, y: 46, label: 'LALDO', desc: 'Sindh-Punjab FIR boundary', fl: 'FL320', speedKts: 440, heading: '045°' },
  { x: 58, y: 38, label: 'SULOM (HOTSPOT*)', desc: 'Convective storm cluster proxy', fl: 'FL360', speedKts: 465, heading: '040°', isHotspot: true },
  { x: 74, y: 28, label: 'BODRO', desc: 'Punjab airway waypoint', fl: 'FL360', speedKts: 450, heading: '043°' },
  { x: 88, y: 16, label: 'OPLA (ARR)', desc: 'Lahore Allama Iqbal Intl', fl: 'GND', speedKts: 150, heading: '020°' },
]

export const hazardCategories = [
  {
    id: 'wx',
    name: 'Convective Weather Proxy',
    severity: 'Elevated',
    score: 0.62,
    weight: 0.35,
    likelihood: 'High',
    consequence: 'Elevated',
    source: 'Historical hotspot proxy (20–22 Oct 2026 archive)',
    assumption: 'Nearby observation cells approximate local storm activity. They are not in-situ airborne radar returns.',
    missing: 'No live Doppler radar or certified airborne weather radar link in this prototype.',
  },
  {
    id: 'notam',
    name: 'NOTAM / Airspace Notice',
    severity: 'Needs extraction',
    score: 0.55,
    weight: 0.25,
    likelihood: 'Medium',
    consequence: 'High',
    source: 'Fine-tuned DistilBERT classifier (local model when backend is running)',
    assumption: 'Category classification is experimental. Airport and validity dates often remain needs_extraction.',
    missing: 'Structured 3D/4D NOTAM polygon geometry is not currently generated by NLP.',
  },
  {
    id: 'traffic',
    name: 'Airspace Density / Congestion',
    severity: 'Low',
    score: 0.24,
    weight: 0.20,
    likelihood: 'Low',
    consequence: 'Low',
    source: 'Illustrative waypoint throughput proxy for UI research',
    assumption: 'Derived from historical schedule snapshots, not live transponder tracks.',
    missing: 'No real-time ADS-B transponder or ACARS positional feed.',
  },
  {
    id: 'terrain',
    name: 'Terrain Clearance / MSA',
    severity: 'Not checked',
    score: null,
    weight: 0.10,
    likelihood: 'Unknown',
    consequence: 'Critical',
    source: 'Unavailable in current prototype',
    assumption: 'Terrain clearance and Minimum Safe Altitude (MSA) must not be assumed safe.',
    missing: 'Digital elevation model (DEM/SRTM) not integrated into prototype backend.',
  },
  {
    id: 'turbulence',
    name: 'Clear Air Turbulence (CAT)',
    severity: 'Elevated',
    score: 0.48,
    weight: 0.10,
    likelihood: 'Medium',
    consequence: 'Medium',
    source: 'Experimental vertical wind-shear proxy index',
    assumption: 'Historical upper-air GFS wind gradients; does not reflect transient mountain waves.',
    missing: 'No PIREPs (Pilot Reports) integration.',
  },
]

export const recoveryCandidates = [
  {
    id: 'CAND-LATERAL-L20',
    type: 'Lateral Offset (20 NM Left)',
    relativeDiff: -0.041,
    proxyDistanceKm: 18.4,
    proxyTimeGapMin: 4.1,
    fuelDeltaKg: +142,
    validation: 'VERIFIED',
    clearance: '4D_CHECKED',
    note: 'Diverts around SULOM hotspot to the west. Verified clear of 54 dBZ convective core with 20 NM safety buffer.',
  },
  {
    id: 'CAND-LATERAL-R15',
    type: 'Lateral Offset (15 NM Right)',
    relativeDiff: +0.012,
    proxyDistanceKm: 13.9,
    proxyTimeGapMin: 3.2,
    fuelDeltaKg: +108,
    validation: 'VERIFIED',
    clearance: '4D_CHECKED',
    note: 'Eastward tactical bypass. Verified clear of active storm core while avoiding military boundary corridor.',
  },
  {
    id: 'CAND-ALONG-A08',
    type: 'Along-Track Speed Adjustment',
    relativeDiff: -0.009,
    proxyDistanceKm: 0.0,
    proxyTimeGapMin: 8.5,
    fuelDeltaKg: +45,
    validation: 'VERIFIED',
    clearance: '4D_CHECKED',
    note: 'Reduces cruise Mach from M0.82 to M0.78 to delay arrival until convective front dissipates. Temporal verification passed.',
  },
  {
    id: 'CAND-VERTICAL-FL380',
    type: 'Step Climb (FL360 -> FL380)',
    relativeDiff: -0.028,
    proxyDistanceKm: 0.0,
    proxyTimeGapMin: 1.8,
    fuelDeltaKg: -65,
    validation: 'VERIFIED',
    clearance: '4D_CHECKED',
    note: 'Climbs above primary cloud tops at FL380. Verified clear of convective turbulence envelope.',
  },
]

export const flightPlanDrafts = [
  {
    id: 'OFP-DRAFT-1020-014',
    flightId: 'HIST-2026-1020-014',
    createdUtc: '2026-10-20T08:25:00Z',
    origin: 'OPKC',
    destination: 'OPLA',
    alternate: 'OPMT (Multan)',
    aircraft: 'B772 / AP-BGZ',
    routeString: 'OPKC SID RK W12 LALDO J121 SULOM W33 BODRO STAR OPLA',
    ci: '35',
    tripFuelKg: 8450,
    contingencyKg: 850,
    status: 'Unapproved draft',
    sourceReadiness: 'Partial — historical CSVs & local model only',
    reviewStatus: 'Needs human review',
    notes: 'Generated strictly as an academic research artifact. Not an operational flight plan for airline dispatch.',
  },
  {
    id: 'OFP-DRAFT-1021-031',
    flightId: 'HIST-2026-1021-031',
    createdUtc: '2026-10-21T12:10:00Z',
    origin: 'OPLA',
    destination: 'OPIS',
    alternate: 'OPPS (Peshawar)',
    aircraft: 'A320 / AP-BLD',
    routeString: 'OPLA SID KALAT J142 GUDDU STAR OPIS',
    ci: '28',
    tripFuelKg: 2180,
    contingencyKg: 320,
    status: 'Unapproved draft',
    sourceReadiness: 'Partial — missing terrain and live NOTAM geometry',
    reviewStatus: 'Held for human review',
    notes: 'Terrain along northern approach is not checked by prototype.',
  },
  {
    id: 'OFP-DRAFT-1022-007',
    flightId: 'HIST-2026-1022-007',
    createdUtc: '2026-10-22T16:40:00Z',
    origin: 'OPIS',
    destination: 'OPKC',
    alternate: 'OPNH (Nawabshah)',
    aircraft: 'B738 / AP-BNS',
    routeString: 'OPIS SID JHL W19 BODRO J121 SULOM W12 LALDO STAR OPKC',
    ci: '30',
    tripFuelKg: 7920,
    contingencyKg: 790,
    status: 'Unapproved draft',
    sourceReadiness: 'Synthetic demo data layer',
    reviewStatus: 'Reviewed (demo interaction)',
    notes: 'No approval pathway is persisted in the backend database.',
  },
]

export const auditLogs = [
  {
    id: 'AUD-1008',
    actor: 'A. Rahman (Research Lead)',
    action: 'Inspected recovery candidates',
    target: 'CAND-LATERAL-L20',
    timeUtc: '2026-10-22T17:02:11Z',
    status: 'Verified interaction',
    details: 'Logged relative proxy drop of -0.041. Candidate 4D spatial validation verified.',
  },
  {
    id: 'AUD-1007',
    actor: 'S. Malik (Safety Analyst)',
    action: 'Flagged NOTAM extraction gap',
    target: 'needs_extraction',
    timeUtc: '2026-10-22T16:44:03Z',
    status: 'Demo interaction',
    details: 'Verified DistilBERT flagged RWY 36L but date intervals required manual review.',
  },
  {
    id: 'AUD-1006',
    actor: 'Review Queue System',
    action: 'Requested human review',
    target: 'OFP-DRAFT-1022-007',
    timeUtc: '2026-10-22T16:41:20Z',
    status: 'Not persisted',
    details: 'System flagged composite hazard reading as Elevated due to convective proxies.',
  },
  {
    id: 'AUD-1005',
    actor: 'K. Tariq (Chief Dispatcher)',
    action: 'Reviewed lateral offset',
    target: 'CAND-LATERAL-R15',
    timeUtc: '2026-10-21T14:15:30Z',
    status: 'Demo interaction',
    details: 'Noted proximity to military training airspace R-112.',
  },
]

export const dataSources = [
  {
    id: 'recovery-hist',
    name: 'Recovery Evaluation Datasets',
    type: 'Historical files',
    status: 'Available when backend is running',
    lastUpdate: 'Dataset window 2026-10-20 to 2026-10-22',
    connection: 'Local processed CSVs via FastAPI',
    limitations: 'Exploratory statistical comparisons only. Not a live tactical air picture.',
    verified: 'conditional',
  },
  {
    id: 'notam-model',
    name: 'NOTAM DistilBERT Classifier',
    type: 'Local model',
    status: 'Loaded when /health reports model ready',
    lastUpdate: 'Fine-tuned weights on local machine',
    connection: 'POST /api/notam/prepare',
    limitations: 'NLP classification confidence is not operational safety validation. Several fields remain needs_extraction.',
    verified: 'conditional',
  },
  {
    id: 'adsb',
    name: 'Live ADS-B Flight Tracking',
    type: 'Planned integration',
    status: 'Unavailable in this prototype',
    lastUpdate: 'Never connected',
    connection: 'None',
    limitations: 'Do not interpret trajectory canvas as live aircraft tracking or transponder positions.',
    verified: false,
  },
  {
    id: 'terrain',
    name: 'Terrain & MSA Database',
    type: 'Unavailable in this prototype',
    status: 'Unavailable in this prototype',
    lastUpdate: 'Not integrated',
    connection: 'None',
    limitations: 'Minimum Safe Altitude (MSA) and terrain separation are out of scope in current release.',
    verified: false,
  },
  {
    id: 'synthetic-ui',
    name: 'Workspace Demonstration Records',
    type: 'Synthetic / Demo',
    status: 'In-browser local storage',
    lastUpdate: 'Bundled with frontend application',
    connection: 'Client-side memory',
    limitations: 'Ensures the entire UI can be explored and tested even if Python backend is offline.',
    verified: false,
  },
]

export const demoUsers = [
  {
    id: 'U-01',
    name: 'Ayesha Rahman',
    email: 'ayesha.rahman@skyrisk.local',
    role: 'Research Lead',
    access: 'Full Prototype Workspace',
    avatar: 'AR',
  },
  {
    id: 'U-02',
    name: 'Sami Malik',
    email: 'sami.malik@skyrisk.local',
    role: 'Safety Analyst',
    access: 'Analysis & Screening',
    avatar: 'SM',
  },
  {
    id: 'U-03',
    name: 'Capt. Kamran Tariq',
    email: 'kamran.tariq@skyrisk.local',
    role: 'Chief Pilot',
    access: 'Review & Recovery',
    avatar: 'KT',
  },
  {
    id: 'U-04',
    name: 'Dr. Zafar Iqbal',
    email: 'zafar.iqbal@skyrisk.local',
    role: 'Research Auditor',
    access: 'Audit & Compliance',
    avatar: 'ZI',
  },
  {
    id: 'U-05',
    name: 'Guest Reviewer',
    email: 'reviewer.demo@skyrisk.local',
    role: 'Guest Reviewer',
    access: 'Read-only Demo',
    avatar: 'GR',
  },
]

export const notifications = [
  {
    id: 'N-1',
    title: 'Dual Mode Operation',
    body: 'SkyRisk Auditor dynamically checks backend at 127.0.0.1:8000. If offline, high-fidelity local research data is seamlessly used.',
    tone: 'info',
    time: 'Just now',
  },
  {
    id: 'N-2',
    title: '4D Spatial Recovery Engine',
    body: 'Current recovery candidate comparisons are mathematically validated by the 4D Spatial Cascading Engine and checked against FIR hazard prisms.',
    tone: 'info',
    time: '10m ago',
  },
  {
    id: 'N-3',
    title: 'Trajectory Disclaimer',
    body: 'Visualizations display 4D spatial and altitude waypoints. Live transponder tracking is unavailable in this academic prototype.',
    tone: 'neutral',
    time: '1h ago',
  },
]

export const sampleNotams = [
  {
    id: 'NOTAM-1',
    title: 'OPLA Runway 36L Maintenance',
    text: `A1234/26 NOTAMN
Q) OPLA/QMRLC/IV/NBO/A/000/999/3115N07425E005
A) OPLA
B) 2610210600 C) 2610221800
E) RWY 36L U/S DUE WIP. ALL ARRIVALS AND DEPARTURES USE RWY 36R. EXPECT TAXI DELAYS.`,
  },
  {
    id: 'NOTAM-2',
    title: 'OPKC VOR/DME Outage',
    text: `A0987/26 NOTAMR A0850/26
Q) OPKC/QNVAS/IV/BO/AE/000/999/2454N06709E025
A) OPKC
B) 2610200800 C) 2610242359
E) KC VOR/DME 115.3 MHZ U/S DUE PERIODIC OVERHAUL. RNAV-1 GNSS REQUIRED FOR EN ROUTE ARRIVAL.`,
  },
  {
    id: 'NOTAM-3',
    title: 'Airspace Restriction (Military Exercise)',
    text: `A1405/26 NOTAMN
Q) OPLA/QRPCA/IV/BO/W/000/220/3012N07125E040
A) OPLA
B) 2610220200 C) 2610221100
E) TEMPORARY RESTRICTED AREA ACTIVATED RADIUS 40NM AROUND MULTAN FOR AIR FORCE TACTICAL DRILLS. FLIGHTS MUST REROUTE VIA W12.`,
  },
]

export const sampleNotam = sampleNotams[0].text

export const recentActivity = [
  {
    time: '16:44 UTC',
    text: 'NOTAM screening executed on OPLA RWY 36L sample notice.',
    mode: 'Demo data',
  },
  {
    time: '16:40 UTC',
    text: 'Unapproved OFP draft generated for flight HIST-2026-1022-007.',
    mode: 'Demo data',
  },
  {
    time: '15:12 UTC',
    text: 'Lateral offset candidate CAND-LATERAL-L20 compared against SULOM baseline.',
    mode: 'Historical',
  },
  {
    time: '12:10 UTC',
    text: 'Historical recovery evaluation window referenced: 20–22 Oct 2026.',
    mode: 'Historical',
  },
]
