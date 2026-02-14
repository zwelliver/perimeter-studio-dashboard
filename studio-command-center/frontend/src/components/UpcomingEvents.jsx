import { format, parseISO, differenceInDays } from 'date-fns'
import './UpcomingEvents.css'

function UpcomingEvents({ shoots, deadlines, onShootClick, onDeadlineClick }) {
  return (
    <div className="card upcoming-events">
      <h2>📅 Upcoming Events</h2>

      <div className="events-sections">
        {/* Shoots */}
        <div className="event-section">
          <h3>🎬 Shoots</h3>
          {!shoots || shoots.length === 0 ? (
            <div className="no-events">No upcoming shoots</div>
          ) : (
            <div className="event-list">
              {shoots.slice(0, 5).map((shoot, index) => {
                const shootDate = parseISO(shoot.datetime)
                const daysUntil = differenceInDays(shootDate, new Date())

                return (
                  <div
                    key={index}
                    className="event-item shoot clickable"
                    onClick={() => onShootClick && onShootClick(shoot)}
                  >
                    <div className="event-header">
                      <div className="event-name">{shoot.name}</div>
                      <div className={`days-badge ${daysUntil <= 2 ? 'urgent' : ''}`}>
                        {daysUntil === 0 ? 'Today' : daysUntil === 1 ? 'Tomorrow' : `${daysUntil}d`}
                      </div>
                    </div>
                    <div className="event-meta">
                      <span>📅 {format(shootDate, 'MMM d, h:mm a')}</span>
                      <span>📁 {shoot.project}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Deadlines */}
        <div className="event-section">
          <h3>⏰ Deadlines</h3>
          {!deadlines || deadlines.length === 0 ? (
            <div className="no-events">No upcoming deadlines</div>
          ) : (
            <div className="event-list">
              {deadlines.slice(0, 5).map((deadline, index) => {
                const dueDate = parseISO(deadline.due_date)
                const daysUntil = deadline.days_until

                return (
                  <div
                    key={index}
                    className="event-item deadline clickable"
                    onClick={() => onDeadlineClick && onDeadlineClick(deadline)}
                  >
                    <div className="event-header">
                      <div className="event-name">{deadline.name}</div>
                      <div className={`days-badge ${daysUntil <= 2 ? 'urgent' : daysUntil <= 5 ? 'warning' : ''}`}>
                        {daysUntil === 0 ? 'Today' : daysUntil === 1 ? 'Tomorrow' : `${daysUntil}d`}
                      </div>
                    </div>
                    <div className="event-meta">
                      <span>📅 {format(dueDate, 'MMM d, yyyy')}</span>
                      <span>📁 {deadline.project}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default UpcomingEvents
