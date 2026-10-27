/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

const RouterContext = createContext(null)

function currentPath() {
  return window.location.pathname || '/'
}

export function Router({ children }) {
  const [path, setPath] = useState(currentPath)

  useEffect(() => {
    const onPop = () => setPath(currentPath())
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  const navigate = useCallback((to, options = {}) => {
    const next = to.startsWith('/') ? to : `/${to}`
    if (next === window.location.pathname) {
      setPath(next)
      return
    }
    if (options.replace) {
      window.history.replaceState({}, '', next)
    } else {
      window.history.pushState({}, '', next)
    }
    setPath(next)
    if (options.scroll !== false) {
      window.scrollTo(0, 0)
    }
  }, [])

  const value = useMemo(() => ({ path, navigate }), [path, navigate])

  return <RouterContext.Provider value={value}>{children}</RouterContext.Provider>
}

export function useRouter() {
  const ctx = useContext(RouterContext)
  if (!ctx) {
    throw new Error('useRouter must be used inside Router')
  }
  return ctx
}

export function Link({ to, className, children, onClick, end = false, ...rest }) {
  const { navigate, path } = useRouter()
  const active = end ? path === to : path === to || path.startsWith(`${to}/`)

  return (
    <a
      href={to}
      className={className}
      aria-current={active ? 'page' : undefined}
      onClick={(event) => {
        if (
          event.defaultPrevented ||
          event.button !== 0 ||
          event.metaKey ||
          event.ctrlKey ||
          event.shiftKey ||
          event.altKey
        ) {
          return
        }
        event.preventDefault()
        onClick?.(event)
        navigate(to)
      }}
      {...rest}
    >
      {children}
    </a>
  )
}
