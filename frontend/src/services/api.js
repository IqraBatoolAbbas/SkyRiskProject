/**
 * Central API client for SkyRisk Auditor FastAPI backend.
 * Provides unified communication for all 5 system modules:
 * 1. Flight & 4D Trajectory
 * 2. Multi-Hazard Risk Assessment
 * 3. Recovery Decision Support & Approvals
 * 4. OFP & Cryptographic Audit Trail
 * 5. Role-Based Access Control (RBAC)
 * + Continuous 4D Airspace Risk & Conflict Monitoring
 */

export const DEFAULT_BACKEND_ORIGIN = 'http://127.0.0.1:8000'

export function getApiBaseUrl() {
  try {
    const custom = localStorage.getItem('skyrisk.backendUrl')
    if (custom) {
      return JSON.parse(custom)
    }
  } catch {
    /* ignore */
  }
  return import.meta.env.VITE_API_BASE_URL || DEFAULT_BACKEND_ORIGIN
}

export function setApiBaseUrl(url) {
  try {
    localStorage.setItem('skyrisk.backendUrl', JSON.stringify(url))
  } catch {
    /* ignore */
  }
}

async function request(path, options = {}) {
  const { timeoutMs = 12000, headers, ...rest } = options
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  const baseUrl = getApiBaseUrl()

  try {
    const response = await fetch(`${baseUrl}${path}`, {
      ...rest,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(rest.body ? { 'Content-Type': 'application/json' } : {}),
        ...headers,
      },
    })

    let payload = null
    const text = await response.text()
    if (text) {
      try {
        payload = JSON.parse(text)
      } catch {
        payload = { raw: text }
      }
    }

    if (!response.ok) {
      const detail = payload?.detail
      const message = typeof detail === 'string'
        ? detail
        : `Backend request failed with status ${response.status}`
      const error = new Error(message)
      error.status = response.status
      error.payload = payload
      throw error
    }

    return payload
  } catch (error) {
    if (error.name === 'AbortError') {
      const timeoutError = new Error('Backend request timed out.')
      timeoutError.code = 'TIMEOUT'
      throw timeoutError
    }
    if (error.status) throw error
    const networkError = new Error('Backend service unreachable (127.0.0.1:8000).')
    networkError.code = 'NETWORK'
    networkError.cause = error
    throw networkError
  } finally {
    window.clearTimeout(timer)
  }
}

// ------------------- System Health -------------------
export function getHealth() {
  return request('/health')
}

// ------------------- Module 1: Flights & 4D Trajectory -------------------
export function getFlights() {
  return request('/api/flights/')
}

export function getFlightTrajectory(flightId) {
  return request(`/api/flights/${encodeURIComponent(flightId)}`)
}

export function createFlightPlan(flightData) {
  return request('/api/flights/', {
    method: 'POST',
    body: JSON.stringify(flightData),
  })
}

export function getAerodromes() {
  return request('/api/flights/aerodromes')
}

// ------------------- Module 2: Multi-Hazard & Risk Assessment -------------------
export function getActiveHazards() {
  return request('/api/risk/hazards')
}

export function evaluateFlightRisk(flightId) {
  return request(`/api/risk/evaluate/${encodeURIComponent(flightId)}`)
}

export function classifyNotam(text) {
  return request('/api/risk/notam/classify', {
    method: 'POST',
    body: JSON.stringify({ text }),
  })
}

export function prepareNotam(text) {
  return request('/api/notam/prepare', {
    method: 'POST',
    body: JSON.stringify({ text }),
    timeoutMs: 45000,
  })
}

// ------------------- Module 3: Recovery Route Decision Support -------------------
export function getRecoverySummary() {
  return request('/api/recovery/summary')
}

export function getFlightRecovery(flightId) {
  return request(`/api/recovery/flights/${encodeURIComponent(flightId)}`)
}

export function generateRecoveryRoutes(flightId) {
  return request(`/api/recovery/generate/${encodeURIComponent(flightId)}`, {
    method: 'POST',
  })
}

export function approveRecoveryRoute({ recoveryPlanId, approvedBy, approvedRole, notes }) {
  return request('/api/recovery/approve', {
    method: 'POST',
    body: JSON.stringify({
      recovery_plan_id: recoveryPlanId,
      approved_by: approvedBy,
      approved_role: approvedRole,
      notes: notes,
    }),
  })
}

export function rejectRecoveryRoute({ recoveryPlanId, rejectedBy, rejectedRole, reason }) {
  return request('/api/recovery/reject', {
    method: 'POST',
    body: JSON.stringify({
      recovery_plan_id: recoveryPlanId,
      rejected_by: rejectedBy,
      rejected_role: rejectedRole,
      reason: reason,
    }),
  })
}

// ------------------- Module 4: OFP & Audit Management -------------------
export function getOfps() {
  return request('/api/ofp-audit/ofps')
}

export function getOfpDetail(ofpId) {
  return request(`/api/ofp-audit/ofps/${encodeURIComponent(ofpId)}`)
}

export function getAuditEvents() {
  return request('/api/ofp-audit/audit-events')
}

export function verifyAuditIntegrity() {
  return request('/api/ofp-audit/verify-audit')
}

// ------------------- Module 5: RBAC & Authentication -------------------
export function loginUser(username, password) {
  return request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export function getPersonnel() {
  return request('/api/auth/users')
}

export function getRoles() {
  return request('/api/auth/roles')
}

// ------------------- Continuous 4D Airspace Monitoring -------------------
export function getMonitoringStatus() {
  return request('/api/monitoring/status')
}

export function triggerAirspaceScan() {
  return request('/api/monitoring/scan-now', {
    method: 'POST',
  })
}

// ------------------- Local Fallback Simulator (Safety net) -------------------
export function simulateNotamClassification(text = '') {
  const t = text.toUpperCase()
  let category = 'RUNWAY_CLOSURE'
  let confidence = 94.6
  let airport = 'OPLA'
  let runway = 'RWY 36L'

  if (t.includes('VOR') || t.includes('NAV') || t.includes('DME') || t.includes('ILS')) {
    category = 'NAV_AID_OUTAGE'
    confidence = 91.2
    runway = null
  } else if (t.includes('RESTRICT') || t.includes('MILITARY') || t.includes('AIRSPACE') || t.includes('DRILL')) {
    category = 'AIRSPACE_RESTRICTION'
    confidence = 88.4
    runway = null
  } else if (t.includes('OBST') || t.includes('CRANE') || t.includes('TOWER')) {
    category = 'OBSTACLE_HAZARD'
    confidence = 86.8
    runway = null
  }

  const aptMatch = t.match(/\b(OP[A-Z]{2})\b/)
  if (aptMatch) airport = aptMatch[1]

  return {
    predicted_category: category,
    confidence_percent: confidence,
    airport: airport,
    runway: runway,
    status: 'ACTIVE_RESTRICTION',
    model: 'DistilBERT Fallback Simulator',
  }
}
