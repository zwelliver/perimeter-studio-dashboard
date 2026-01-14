import './StatusBoard.css'

function StatusBoard({ metrics }) {
  if (!metrics) return null

  const stats = [
    {
      label: 'Active Tasks',
      value: metrics.total_tasks,
      icon: '📋',
      color: 'var(--color-accent)'
    },
    {
      label: 'At Risk',
      value: metrics.at_risk_count,
      icon: '⚠️',
      color: metrics.at_risk_count > 0 ? 'var(--color-warning)' : 'var(--color-success)'
    },
    {
      label: 'Upcoming Shoots',
      value: metrics.upcoming_shoots,
      icon: '🎬',
      color: 'var(--color-accent)'
    },
    {
      label: 'Upcoming Deadlines',
      value: metrics.upcoming_deadlines,
      icon: '⏰',
      color: 'var(--color-accent)'
    }
  ]

  return (
    <div className="status-board">
      {stats.map((stat, index) => (
        <div key={index} className="stat-card" style={{ borderColor: stat.color }}>
          <div className="stat-icon">{stat.icon}</div>
          <div className="stat-content">
            <div className="stat-value" style={{ color: stat.color }}>
              {stat.value}
            </div>
            <div className="stat-label">{stat.label}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default StatusBoard
