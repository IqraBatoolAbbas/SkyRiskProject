import { useEffect, useState } from 'react'
import { Icon } from './icons.jsx'
import { statusTone } from '../utils/format.js'

export function Badge({ children, tone, dot = false, className = '' }) {
  return (
    <span className={`badge ${tone || 'neutral'} ${className}`}>
      {dot ? <span className="badge-dot" /> : null}
      {children}
    </span>
  )
}

export function StatusBadge({ value }) {
  return <Badge tone={statusTone(value)} dot>{value}</Badge>
}

export function Button({
  variant = 'default',
  size = 'md',
  icon,
  children,
  className = '',
  ...rest
}) {
  const classes = [
    'btn',
    variant === 'primary' && 'btn-primary',
    variant === 'ghost' && 'btn-ghost',
    size === 'sm' && 'btn-sm',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <button className={classes} {...rest}>
      {icon ? <Icon name={icon} size={size === 'sm' ? 'sm' : 'md'} /> : null}
      {children}
    </button>
  )
}

export function Card({ children, className = '', interactive = false, ...rest }) {
  return (
    <section
      className={`card card-pad ${interactive ? 'card-interactive' : ''} ${className}`}
      {...rest}
    >
      {children}
    </section>
  )
}

export function SectionHeading({ title, subtitle, action }) {
  return (
    <div className="section-heading">
      <div>
        <h2>{title}</h2>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      {action ? <div>{action}</div> : null}
    </div>
  )
}

export function Alert({ tone = 'info', title, children, className = '' }) {
  let iconName = 'info'
  if (tone === 'warning') iconName = 'warning'
  if (tone === 'critical') iconName = 'warning'
  if (tone === 'success') iconName = 'check'

  return (
    <div className={`alert ${tone} ${className}`} role="status">
      <Icon name={iconName} size="md" />
      <div>
        {title ? <strong>{title} </strong> : null}
        {children}
      </div>
    </div>
  )
}

export function EmptyState({ title = 'No data available', children, icon = 'info' }) {
  return (
    <div className="empty">
      <div style={{ marginBottom: 10, color: 'var(--muted)' }}>
        <Icon name={icon} size="lg" />
      </div>
      <strong style={{ display: 'block', color: 'var(--text)', marginBottom: 4 }}>
        {title}
      </strong>
      <p className="muted" style={{ maxWidth: 440, margin: '0 auto' }}>
        {children}
      </p>
    </div>
  )
}

export function LoadingState({ label = 'Loading…' }) {
  return (
    <div className="loading" role="status" aria-live="polite">
      <div className="loading-dot" />
      <p>{label}</p>
    </div>
  )
}

export function SearchField({ value, onChange, placeholder = 'Search records…', id }) {
  return (
    <label className="search" htmlFor={id}>
      <Icon name="search" size="sm" />
      <input
        id={id}
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        autoComplete="off"
        spellCheck="false"
      />
      {value ? (
        <button
          type="button"
          className="btn btn-ghost"
          style={{ padding: 0, minHeight: 'auto', border: 0 }}
          onClick={() => onChange('')}
          aria-label="Clear search"
        >
          <Icon name="close" size="sm" />
        </button>
      ) : null}
    </label>
  )
}

export function Modal({ title, children, onClose, footer }) {
  useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header>
          <h3 id="modal-title">{title}</h3>
          <button
            className="btn btn-icon btn-ghost btn-sm"
            onClick={onClose}
            aria-label="Close dialog"
          >
            <Icon name="close" />
          </button>
        </header>
        <div className="body">{children}</div>
        {footer ? <footer>{footer}</footer> : null}
      </div>
    </div>
  )
}

export function DataTable({ columns, rows, onSelect, selectedId, empty = 'No records found.' }) {
  const [sortKey, setSortKey] = useState(null)
  const [sortAsc, setSortAsc] = useState(true)

  if (!rows || !rows.length) {
    return <EmptyState title="No records">{empty}</EmptyState>
  }

  const sortedRows = [...rows].sort((a, b) => {
    if (!sortKey) return 0
    const valA = a[sortKey]
    const valB = b[sortKey]
    if (valA === valB) return 0
    if (valA == null) return 1
    if (valB == null) return -1
    const res = valA > valB ? 1 : -1
    return sortAsc ? res : -res
  })

  const handleHeaderClick = (key) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc)
    } else {
      setSortKey(key)
      setSortAsc(true)
    }
  }

  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                onClick={() => handleHeaderClick(col.key)}
                style={{ cursor: 'pointer', userSelect: 'none' }}
                title={`Sort by ${col.label}`}
              >
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  {col.label}
                  {sortKey === col.key ? (
                    <span style={{ color: 'var(--cyan)' }}>{sortAsc ? '▲' : '▼'}</span>
                  ) : null}
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, index) => (
            <tr
              key={row.id ?? index}
              className={`${onSelect ? 'interactive' : ''} ${selectedId === row.id ? 'is-selected' : ''}`}
              onClick={() => onSelect?.(row)}
              tabIndex={onSelect ? 0 : undefined}
              onKeyDown={(event) => {
                if (onSelect && (event.key === 'Enter' || event.key === ' ')) {
                  event.preventDefault()
                  onSelect(row)
                }
              }}
            >
              {columns.map((col) => (
                <td key={col.key}>{col.render ? col.render(row) : row[col.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function Tabs({ tabs, activeId, onChange }) {
  return (
    <div className="tabs" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          role="tab"
          aria-selected={activeId === tab.id}
          className={`tab ${activeId === tab.id ? 'is-active' : ''}`}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

export function BarChart({ items, max = 100 }) {
  const height = 160
  const width = 460
  const barW = items.length ? Math.min(48, (width - 60) / items.length - 12) : 24

  return (
    <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Relative comparison bar chart">
      {/* Background gridlines */}
      <line x1="30" y1="20" x2={width - 20} y2="20" stroke="#253650" strokeDasharray="3 3" />
      <line x1="30" y1="75" x2={width - 20} y2="75" stroke="#253650" strokeDasharray="3 3" />
      <line x1="30" y1="130" x2={width - 20} y2="130" stroke="#253650" />

      {items.map((item, index) => {
        const value = Number(item.value) || 0
        const h = Math.min(110, (value / max) * 110)
        const x = 40 + index * ((width - 70) / Math.max(items.length, 1))
        return (
          <g key={item.label || index}>
            <rect
              x={x}
              y={130 - h}
              width={barW}
              height={Math.max(4, h)}
              rx="4"
              fill="url(#cyanBlueGrad)"
              opacity="0.9"
            />
            <text x={x + barW / 2} y={124 - h} textAnchor="middle" fill="#E8F0FC" fontSize="10" fontWeight="600">
              {value}%
            </text>
            <text x={x + barW / 2} y={148} textAnchor="middle" fill="#91A4BD" fontSize="9.5">
              {item.label}
            </text>
          </g>
        )
      })}
      <defs>
        <linearGradient id="cyanBlueGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#35C7E8" />
          <stop offset="100%" stopColor="#648BFF" />
        </linearGradient>
      </defs>
    </svg>
  )
}

export function ProfileChart({ points, cursorTime = null }) {
  if (!points || !points.length) return null

  const width = 420
  const height = 180
  const maxFl = 400

  const coords = points.map((p) => {
    const x = 30 + (p.t / 100) * (width - 50)
    const y = 150 - (p.fl / maxFl) * 120
    return { ...p, x, y }
  })

  const d = coords.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')
  const areaD = `${d} L ${width - 20} 150 L 30 150 Z`

  let cursorX = null
  let cursorY = null
  if (cursorTime !== null) {
    cursorX = 30 + (cursorTime / 100) * (width - 50)
    // Approximate altitude by linear interpolation
    for (let i = 0; i < points.length - 1; i++) {
      if (cursorTime >= points[i].t && cursorTime <= points[i + 1].t) {
        const ratio = (cursorTime - points[i].t) / (points[i + 1].t - points[i].t || 1)
        const fl = points[i].fl + ratio * (points[i + 1].fl - points[i].fl)
        cursorY = 150 - (fl / maxFl) * 120
        break
      }
    }
  }

  return (
    <svg className="chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Altitude profile graph">
      {/* Grid lines */}
      <line x1="30" y1="30" x2={width - 20} y2="30" stroke="#253650" strokeDasharray="3 3" />
      <text x="24" y="34" fill="#91A4BD" fontSize="9" textAnchor="end">FL380</text>
      <line x1="30" y1="90" x2={width - 20} y2="90" stroke="#253650" strokeDasharray="3 3" />
      <text x="24" y="94" fill="#91A4BD" fontSize="9" textAnchor="end">FL200</text>
      <line x1="30" y1="150" x2={width - 20} y2="150" stroke="#314766" />
      <text x="24" y="154" fill="#91A4BD" fontSize="9" textAnchor="end">GND</text>

      {/* Profile area & line */}
      <path d={areaD} fill="url(#altitudeGrad)" />
      <path d={d} fill="none" stroke="#648BFF" strokeWidth="2.5" />

      {/* Key points */}
      {coords.map((p) => (
        <circle key={p.t} cx={p.x} cy={p.y} r="3" fill="#35C7E8" />
      ))}

      {/* Scrubbed cursor indicator */}
      {cursorX !== null && cursorY !== null ? (
        <g>
          <line x1={cursorX} y1="20" x2={cursorX} y2="150" stroke="#35C7E8" strokeWidth="1.5" strokeDasharray="2 2" />
          <circle cx={cursorX} cy={cursorY} r="5" fill="#35C7E8" stroke="#080F1D" strokeWidth="2" />
        </g>
      ) : null}

      <defs>
        <linearGradient id="altitudeGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#648BFF" stopOpacity="0.25" />
          <stop offset="100%" stopColor="#648BFF" stopOpacity="0.02" />
        </linearGradient>
      </defs>
    </svg>
  )
}
