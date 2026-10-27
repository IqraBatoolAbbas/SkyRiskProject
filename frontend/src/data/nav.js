export const workspaceNav = [
  { to: '/workspace', label: 'Overview', icon: 'layout' },
  { to: '/workspace/flights', label: 'Flight Operations', icon: 'plane' },
  { to: '/workspace/trajectory', label: '4D Trajectory', icon: 'map' },
  { to: '/workspace/risk', label: 'Risk Assessment', icon: 'shield' },
  { to: '/workspace/recovery', label: 'Recovery Planning', icon: 'route' },
  { to: '/workspace/ofp', label: 'Flight Plans', icon: 'file' },
  { to: '/workspace/audit', label: 'Approvals & Audit', icon: 'clipboard' },
  { to: '/workspace/sources', label: 'Data Sources', icon: 'database' },
  { to: '/workspace/users', label: 'Users & Roles', icon: 'users' },
  { to: '/workspace/settings', label: 'Settings', icon: 'settings' },
]

export const pageMeta = {
  '/workspace': {
    title: 'Overview Dashboard',
    subtitle: 'Historical assessments, readiness, and exploratory recovery context.',
  },
  '/workspace/flights': {
    title: 'Flight Operations',
    subtitle: 'Search historical and demonstration trajectory records.',
  },
  '/workspace/trajectory': {
    title: '4D Trajectory Visualization',
    subtitle: 'Interactive 4D tactical airspace radar and vertical altitude cross-section.',
  },
  '/workspace/risk': {
    title: 'Multi-Hazard Risk Assessment',
    subtitle: '4D multi-hazard scoring engine validated against convective, space weather, and NOTAM hazards.',
  },
  '/workspace/recovery': {
    title: 'Recovery Route Planning',
    subtitle: 'Pareto multi-route recovery generation with fuel burn and delay trade-off analysis.',
  },
  '/workspace/ofp': {
    title: 'Operational Flight Plan Management',
    subtitle: 'ICAO-standard operational flight plans with human-in-the-loop dispatch release.',
  },
  '/workspace/audit': {
    title: 'Approvals & Audit Logs',
    subtitle: 'Immutable SHA-256 tamper-evident cryptographic audit ledger and verification.',
  },
  '/workspace/sources': {
    title: 'Data Sources & Pipelines',
    subtitle: 'Connected live pipelines: PostgreSQL 16 (skyrisk), DistilBERT NLP, NOAA SWPC, and Open-Meteo.',
  },
  '/workspace/users': {
    title: 'User & Role Management',
    subtitle: 'Prototype directory. Not production-grade authorization.',
  },
  '/workspace/settings': {
    title: 'Settings',
    subtitle: 'Display preferences, prototype scope, and data limitations.',
  },
}
