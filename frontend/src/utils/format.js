export function formatUtc(date = new Date()) {
  return date.toISOString().replace('.000', '')
}

export function formatClock(date = new Date(), mode = 'utc') {
  if (mode === 'local') {
    return date.toLocaleString(undefined, {
      hour12: false,
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  const iso = date.toISOString()
  return `${iso.slice(0, 10)} ${iso.slice(11, 19)} UTC`
}

export function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '—'
  }
  return Number(value).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: Number.isInteger(Number(value)) ? 0 : Math.min(digits, 2),
  })
}

export function statusTone(status) {
  const value = String(status || '').toUpperCase()
  if (value.includes('CRITICAL')) return 'critical'
  if (value.includes('HIGH')) return 'high'
  if (value.includes('ELEVATED') || value.includes('NEEDS')) return 'elevated'
  if (value.includes('LOW') || value.includes('HEALTHY') || value.includes('READY')) {
    return 'low'
  }
  if (value.includes('NOT_VALIDATED') || value.includes('NOT VALIDATED')) return 'high'
  if (value.includes('NOT_CHECKED') || value.includes('NOT CHECKED')) return 'elevated'
  if (value.includes('DEMO') || value.includes('ILLUSTRATIVE')) return 'info'
  if (value.includes('HISTORICAL')) return 'info'
  return 'neutral'
}

export function storageGet(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw === null ? fallback : JSON.parse(raw)
  } catch {
    return fallback
  }
}

export function storageSet(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    /* ignore quota / private-mode failures */
  }
}
