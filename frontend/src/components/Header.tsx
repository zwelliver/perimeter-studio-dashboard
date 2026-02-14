import { formatDistanceToNow } from 'date-fns'
import type { HeaderProps } from '../types/dashboard'
import type { Theme, DashboardData } from '../types/dashboard'
import ThemeToggle from './ThemeToggle'
import ExportMenu from './ExportMenu'
import './Header.css'

interface ExtendedHeaderProps extends HeaderProps {
  theme?: Theme
  onToggleTheme?: () => void
  data?: DashboardData | null
}

function Header({ lastUpdate, onRefresh, autoRefresh, onToggleAutoRefresh, loading, theme, onToggleTheme, data }: ExtendedHeaderProps) {
  return (
    <header className="header">
      <div className="header-content">
        <h1>✦ Studio Command Center ✦</h1>

        <div className="header-controls">
          <div className="last-update" role="status" aria-live="polite">
            {lastUpdate && (
              <span>
                Last updated {formatDistanceToNow(lastUpdate, { addSuffix: true })}
              </span>
            )}
          </div>

          <div className="control-group">
            <ExportMenu data={data} disabled={loading} />

            {theme && onToggleTheme && (
              <ThemeToggle theme={theme} onToggle={onToggleTheme} />
            )}

            <button
              className="auto-refresh-toggle"
              onClick={onToggleAutoRefresh}
              aria-label={`Auto-refresh is currently ${autoRefresh ? 'enabled' : 'disabled'}. Click to ${autoRefresh ? 'disable' : 'enable'} auto-refresh.`}
              aria-pressed={autoRefresh}
              title={autoRefresh ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}
            >
              <span
                className={`status-dot ${autoRefresh ? 'normal' : ''}`}
                aria-hidden="true"
              ></span>
              Auto-refresh
            </button>

            <button
              className="refresh-btn"
              onClick={onRefresh}
              disabled={loading}
              aria-label={loading ? 'Refreshing dashboard data...' : 'Refresh dashboard data'}
            >
              <span className={loading ? 'spinning' : ''} aria-hidden="true">🔄</span>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
