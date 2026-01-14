import { formatDistanceToNow } from 'date-fns'
import './Header.css'

function Header({ lastUpdate, onRefresh, autoRefresh, onToggleAutoRefresh, loading }) {
  return (
    <header className="header">
      <div className="header-content">
        <h1>✦ Studio Command Center ✦</h1>

        <div className="header-controls">
          <div className="last-update">
            {lastUpdate && (
              <span>
                Last updated {formatDistanceToNow(lastUpdate, { addSuffix: true })}
              </span>
            )}
          </div>

          <button
            className="auto-refresh-toggle"
            onClick={onToggleAutoRefresh}
            title={autoRefresh ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}
          >
            <span className={`status-dot ${autoRefresh ? 'normal' : ''}`}></span>
            Auto-refresh
          </button>

          <button
            className="refresh-btn"
            onClick={onRefresh}
            disabled={loading}
          >
            <span className={loading ? 'spinning' : ''}>🔄</span>
            Refresh
          </button>
        </div>
      </div>
    </header>
  )
}

export default Header
