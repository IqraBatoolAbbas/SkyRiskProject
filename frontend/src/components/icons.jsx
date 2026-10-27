const sizeMap = { sm: 16, md: 18, lg: 22, xl: 28 }

export function Icon({ name, size = 'md', stroke = 1.7, className = '' }) {
  const px = sizeMap[size] || (typeof size === 'number' ? size : 18)
  const common = {
    width: px,
    height: px,
    viewBox: '0 0 24 24',
    fill: 'none',
    xmlns: 'http://www.w3.org/2000/svg',
    'aria-hidden': true,
    focusable: 'false',
    className,
  }
  const s = { stroke: 'currentColor', strokeWidth: stroke, strokeLinecap: 'round', strokeLinejoin: 'round' }

  switch (name) {
    case 'radar':
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" {...s} />
          <circle cx="12" cy="12" r="4" {...s} />
          <path d="M12 3v4M12 17v4M3 12h4M17 12h4" {...s} />
        </svg>
      )
    case 'layout':
      return (
        <svg {...common}>
          <rect x="3" y="3" width="7" height="9" rx="1" {...s} />
          <rect x="14" y="3" width="7" height="5" rx="1" {...s} />
          <rect x="14" y="12" width="7" height="9" rx="1" {...s} />
          <rect x="3" y="16" width="7" height="5" rx="1" {...s} />
        </svg>
      )
    case 'plane':
      return (
        <svg {...common}>
          <path d="M3 12l18-7-7 18-2.5-7.5L3 12z" {...s} />
        </svg>
      )
    case 'map':
      return (
        <svg {...common}>
          <path d="M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3V6z" {...s} />
          <path d="M9 3v15M15 6v15" {...s} />
        </svg>
      )
    case 'shield':
      return (
        <svg {...common}>
          <path d="M12 3l8 4v6c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V7l8-4z" {...s} />
        </svg>
      )
    case 'route':
      return (
        <svg {...common}>
          <circle cx="6" cy="6" r="2.5" {...s} />
          <circle cx="18" cy="18" r="2.5" {...s} />
          <path d="M8 8c6 0 2 8 8 8" {...s} />
        </svg>
      )
    case 'file':
      return (
        <svg {...common}>
          <path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z" {...s} />
          <path d="M14 3v6h6" {...s} />
        </svg>
      )
    case 'clipboard':
      return (
        <svg {...common}>
          <rect x="6" y="5" width="12" height="16" rx="2" {...s} />
          <path d="M9 5V4h6v1M8 10h8M8 14h6" {...s} />
        </svg>
      )
    case 'database':
      return (
        <svg {...common}>
          <ellipse cx="12" cy="6" rx="7" ry="3" {...s} />
          <path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" {...s} />
        </svg>
      )
    case 'users':
      return (
        <svg {...common}>
          <circle cx="9" cy="8" r="3" {...s} />
          <path d="M3.5 19c.8-3 3-4.5 5.5-4.5S13.7 16 14.5 19" {...s} />
          <circle cx="17" cy="9" r="2.2" {...s} />
          <path d="M16 14.5c2.2.3 3.8 1.6 4.5 4.5" {...s} />
        </svg>
      )
    case 'settings':
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="3" {...s} />
          <path d="M12 3v2.2M12 18.8V21M4.9 6.5l1.6 1.5M17.5 16l1.6 1.5M3 12h2.2M18.8 12H21M4.9 17.5l1.6-1.5M17.5 8l1.6-1.5" {...s} />
        </svg>
      )
    case 'search':
      return (
        <svg {...common}>
          <circle cx="11" cy="11" r="6.5" {...s} />
          <path d="M16 16l4.5 4.5" {...s} />
        </svg>
      )
    case 'bell':
      return (
        <svg {...common}>
          <path d="M6 16V11a6 6 0 1 1 12 0v5l1.5 2H4.5L6 16z" {...s} />
          <path d="M10 20a2 2 0 0 0 4 0" {...s} />
        </svg>
      )
    case 'menu':
      return (
        <svg {...common}>
          <path d="M4 7h16M4 12h16M4 17h16" {...s} />
        </svg>
      )
    case 'collapse':
      return (
        <svg {...common}>
          <path d="M15 6l-6 6 6 6" {...s} />
        </svg>
      )
    case 'expand':
      return (
        <svg {...common}>
          <path d="M9 6l6 6-6 6" {...s} />
        </svg>
      )
    case 'close':
      return (
        <svg {...common}>
          <path d="M6 6l12 12M18 6L6 18" {...s} />
        </svg>
      )
    case 'info':
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="9" {...s} />
          <path d="M12 10v7M12 7h.01" {...s} />
        </svg>
      )
    case 'warning':
      return (
        <svg {...common}>
          <path d="M12 4l9 16H3L12 4z" {...s} />
          <path d="M12 10v5M12 17h.01" {...s} />
        </svg>
      )
    case 'check':
      return (
        <svg {...common}>
          <path d="M5 12l5 5 9-10" {...s} />
        </svg>
      )
    case 'clock':
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" {...s} />
          <path d="M12 8v5l3 2" {...s} />
        </svg>
      )
    case 'user':
      return (
        <svg {...common}>
          <circle cx="12" cy="8" r="3.2" {...s} />
          <path d="M5 19c1.2-3.4 3.6-5 7-5s5.8 1.6 7 5" {...s} />
        </svg>
      )
    case 'external':
      return (
        <svg {...common}>
          <path d="M10 5H6a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-4" {...s} />
          <path d="M13 5h6v6M19 5l-8 8" {...s} />
        </svg>
      )
    case 'play':
      return (
        <svg {...common}>
          <polygon points="5,3 19,12 5,21" fill="currentColor" stroke="none" />
        </svg>
      )
    case 'pause':
      return (
        <svg {...common}>
          <rect x="6" y="4" width="4" height="16" fill="currentColor" stroke="none" />
          <rect x="14" y="4" width="4" height="16" fill="currentColor" stroke="none" />
        </svg>
      )
    case 'refresh':
      return (
        <svg {...common}>
          <path d="M20 11a8.1 8.1 0 0 0-15.5-2m-.5-4v4h4M4 13a8.1 8.1 0 0 0 15.5 2m.5 4v-4h-4" {...s} />
        </svg>
      )
    case 'filter':
      return (
        <svg {...common}>
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" {...s} />
        </svg>
      )
    case 'download':
      return (
        <svg {...common}>
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" {...s} />
        </svg>
      )
    case 'sliders':
      return (
        <svg {...common}>
          <line x1="4" y1="21" x2="4" y2="14" {...s} />
          <line x1="4" y1="10" x2="4" y2="3" {...s} />
          <line x1="12" y1="21" x2="12" y2="12" {...s} />
          <line x1="12" y1="8" x2="12" y2="3" {...s} />
          <line x1="20" y1="21" x2="20" y2="16" {...s} />
          <line x1="20" y1="12" x2="20" y2="3" {...s} />
          <line x1="1" y1="14" x2="7" y2="14" {...s} />
          <line x1="9" y1="8" x2="15" y2="8" {...s} />
          <line x1="17" y1="16" x2="23" y2="16" {...s} />
        </svg>
      )
    case 'layers':
      return (
        <svg {...common}>
          <polygon points="12 2 2 7 12 12 22 7 12 2" {...s} />
          <polyline points="2 17 12 22 22 17" {...s} />
          <polyline points="2 12 12 17 22 12" {...s} />
        </svg>
      )
    case 'arrowRight':
      return (
        <svg {...common}>
          <line x1="5" y1="12" x2="19" y2="12" {...s} />
          <polyline points="12 5 19 12 12 19" {...s} />
        </svg>
      )
    case 'activity':
      return (
        <svg {...common}>
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" {...s} />
        </svg>
      )
    case 'sparkles':
      return (
        <svg {...common}>
          <path d="M12 3l1.9 4.8L18.7 9.7l-4.8 1.9L12 16.4l-1.9-4.8L5.3 9.7l4.8-1.9L12 3z" {...s} />
          <path d="M19 15l.9 2.1 2.1.9-2.1.9-.9 2.1-.9-2.1-2.1-.9 2.1-.9.9-2.1z" {...s} />
        </svg>
      )
    default:
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" {...s} />
        </svg>
      )
  }
}
