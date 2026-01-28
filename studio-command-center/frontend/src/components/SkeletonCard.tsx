import './SkeletonCard.css'

interface SkeletonCardProps {
  type?: 'default' | 'chart' | 'team' | 'list'
  height?: string
}

function SkeletonCard({ type = 'default', height }: SkeletonCardProps) {
  return (
    <div className={`skeleton-card ${type}`} style={{ height }}>
      <div className="skeleton-header">
        <div className="skeleton-title"></div>
        <div className="skeleton-badge"></div>
      </div>

      <div className="skeleton-content">
        {type === 'chart' && (
          <div className="skeleton-chart">
            <div className="skeleton-chart-bar" style={{ height: '60%' }}></div>
            <div className="skeleton-chart-bar" style={{ height: '80%' }}></div>
            <div className="skeleton-chart-bar" style={{ height: '45%' }}></div>
            <div className="skeleton-chart-bar" style={{ height: '70%' }}></div>
            <div className="skeleton-chart-bar" style={{ height: '35%' }}></div>
          </div>
        )}

        {type === 'team' && (
          <div className="skeleton-team">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="skeleton-team-member">
                <div className="skeleton-member-header">
                  <div className="skeleton-member-name"></div>
                  <div className="skeleton-member-util"></div>
                </div>
                <div className="skeleton-progress-bar"></div>
                <div className="skeleton-member-details"></div>
              </div>
            ))}
          </div>
        )}

        {type === 'list' && (
          <div className="skeleton-list">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="skeleton-list-item">
                <div className="skeleton-list-content">
                  <div className="skeleton-list-title"></div>
                  <div className="skeleton-list-subtitle"></div>
                  <div className="skeleton-list-meta"></div>
                </div>
              </div>
            ))}
          </div>
        )}

        {type === 'default' && (
          <div className="skeleton-default">
            <div className="skeleton-line"></div>
            <div className="skeleton-line"></div>
            <div className="skeleton-line short"></div>
            <div className="skeleton-line medium"></div>
          </div>
        )}
      </div>
    </div>
  )
}

export default SkeletonCard