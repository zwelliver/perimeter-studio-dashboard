import { useState } from 'react'
import { format, parseISO } from 'date-fns'
import './DetailModal.css'

function DetailModal({ item, type, onClose }) {
  const [filmedStatus, setFilmedStatus] = useState('idle') // idle | loading | success | error
  const [errorMsg, setErrorMsg] = useState('')

  if (!item) return null

  const handleMarkFilmed = async () => {
    if (!item.gid) return
    setFilmedStatus('loading')
    setErrorMsg('')
    try {
      const resp = await fetch(`/api/tasks/${item.gid}/mark-filmed`, { method: 'POST' })
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to mark as filmed')
      }
      setFilmedStatus('success')
    } catch (err) {
      setErrorMsg(err.message)
      setFilmedStatus('error')
    }
  }

  const renderTaskDetails = () => (
    <div className="detail-content">
      <div className="detail-header">
        <h2>{item.name}</h2>
        <button className="close-modal" onClick={onClose}>✕</button>
      </div>

      <div className="detail-grid">
        <div className="detail-item">
          <span className="detail-label">📁 Project</span>
          <span className="detail-value">{item.project}</span>
        </div>

        <div className="detail-item">
          <span className="detail-label">👤 Assignee</span>
          <span className="detail-value">{item.assignee || 'Unassigned'}</span>
        </div>

        {item.videographer && (
          <div className="detail-item">
            <span className="detail-label">🎥 Videographer</span>
            <span className="detail-value">{item.videographer}</span>
          </div>
        )}

        {item.due_on && (
          <div className="detail-item">
            <span className="detail-label">📅 Due Date</span>
            <span className="detail-value">{item.due_on}</span>
          </div>
        )}
      </div>

      {item.risks && item.risks.length > 0 && (
        <div className="risk-section">
          <h3>⚠️ Risk Factors</h3>
          <ul className="risk-list-detail">
            {item.risks.map((risk, i) => (
              <li key={i}>{risk}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="detail-actions">
        <a
          href={`https://app.asana.com/0/0/${item.gid || ''}/f`}
          target="_blank"
          rel="noopener noreferrer"
          className="asana-link-btn"
        >
          Open in Asana →
        </a>
      </div>
    </div>
  )

  const renderShootDetails = () => (
    <div className="detail-content">
      <div className="detail-header">
        <h2>🎬 {item.name}</h2>
        <button className="close-modal" onClick={onClose}>✕</button>
      </div>

      <div className="detail-grid">
        <div className="detail-item">
          <span className="detail-label">📁 Project</span>
          <span className="detail-value">{item.project}</span>
        </div>

        <div className="detail-item">
          <span className="detail-label">📅 Film Date</span>
          <span className="detail-value">
            {format(parseISO(item.datetime), 'EEEE, MMMM d, yyyy')}
          </span>
        </div>

        <div className="detail-item">
          <span className="detail-label">🕐 Time</span>
          <span className="detail-value">
            {format(parseISO(item.datetime), 'h:mm a')}
          </span>
        </div>

        {item.start_on && (
          <div className="detail-item">
            <span className="detail-label">▶️ Start Date</span>
            <span className="detail-value">{item.start_on}</span>
          </div>
        )}

        {item.due_on && (
          <div className="detail-item">
            <span className="detail-label">🏁 Due Date</span>
            <span className="detail-value">{item.due_on}</span>
          </div>
        )}
      </div>

      <div className="detail-actions">
        {item.gid && (
          <button
            className={`mark-filmed-btn ${filmedStatus}`}
            onClick={handleMarkFilmed}
            disabled={filmedStatus === 'loading' || filmedStatus === 'success'}
          >
            {filmedStatus === 'idle' && 'Mark Filmed'}
            {filmedStatus === 'loading' && (
              <><span className="spinner" /> Updating...</>
            )}
            {filmedStatus === 'success' && <><span className="checkmark">✓</span> Filmed</>}
            {filmedStatus === 'error' && 'Retry — Mark Filmed'}
          </button>
        )}
        <a
          href={`https://app.asana.com/0/0/${item.gid || ''}/f`}
          target="_blank"
          rel="noopener noreferrer"
          className="asana-link-btn"
        >
          Open in Asana →
        </a>
      </div>
      {filmedStatus === 'error' && errorMsg && (
        <p className="filmed-error">{errorMsg}</p>
      )}
    </div>
  )

  const renderDeadlineDetails = () => (
    <div className="detail-content">
      <div className="detail-header">
        <h2>⏰ {item.name}</h2>
        <button className="close-modal" onClick={onClose}>✕</button>
      </div>

      <div className="detail-grid">
        <div className="detail-item">
          <span className="detail-label">📁 Project</span>
          <span className="detail-value">{item.project}</span>
        </div>

        <div className="detail-item">
          <span className="detail-label">📅 Due Date</span>
          <span className="detail-value">
            {format(parseISO(item.due_date), 'EEEE, MMMM d, yyyy')}
          </span>
        </div>

        <div className="detail-item">
          <span className="detail-label">⏳ Days Until</span>
          <span className={`detail-value ${item.days_until <= 2 ? 'urgent' : item.days_until <= 5 ? 'warning' : ''}`}>
            {item.days_until === 0 ? 'Due Today!' : item.days_until === 1 ? 'Due Tomorrow' : `${item.days_until} days`}
          </span>
        </div>

        {item.start_on && (
          <div className="detail-item">
            <span className="detail-label">▶️ Start Date</span>
            <span className="detail-value">{item.start_on}</span>
          </div>
        )}
      </div>

      <div className="detail-actions">
        <a
          href={`https://app.asana.com/0/0/${item.gid || ''}/f`}
          target="_blank"
          rel="noopener noreferrer"
          className="asana-link-btn"
        >
          Open in Asana →
        </a>
      </div>
    </div>
  )

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        {type === 'task' && renderTaskDetails()}
        {type === 'shoot' && renderShootDetails()}
        {type === 'deadline' && renderDeadlineDetails()}
      </div>
    </div>
  )
}

export default DetailModal
