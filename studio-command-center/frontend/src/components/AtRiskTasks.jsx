import { memo } from 'react'
import './AtRiskTasks.css'

function AtRiskTasks({ tasks, onTaskClick }) {
  const handleKeyPress = (event, task) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onTaskClick && onTaskClick(task)
    }
  }

  if (!tasks || tasks.length === 0) {
    return (
      <div className="card at-risk-tasks">
        <h2 id="at-risk-heading">⚠️ At-Risk Tasks</h2>
        <div className="no-tasks" role="status" aria-live="polite">
          <div className="success-icon" aria-hidden="true">✅</div>
          <p>No tasks currently at risk!</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card at-risk-tasks">
      <h2 id="at-risk-heading">⚠️ At-Risk Tasks</h2>
      <div className="task-count" aria-live="polite">
        {tasks.length} task{tasks.length !== 1 ? 's' : ''} at risk
      </div>

      <div className="risk-list" role="list" aria-labelledby="at-risk-heading">
        {tasks.slice(0, 10).map((task, index) => {
          const riskFactors = task.risks ? task.risks.join(', ') : 'No specific risk factors listed'

          return (
            <div
              key={index}
              className="risk-item clickable"
              role="listitem button"
              tabIndex={0}
              aria-label={`At-risk task: ${task.name} in project ${task.project}. Assigned to ${task.assignee}${task.due_on ? `, due ${task.due_on}` : ''}. Risk factors: ${riskFactors}. Press Enter or Space for details.`}
              onClick={() => onTaskClick && onTaskClick(task)}
              onKeyDown={(e) => handleKeyPress(e, task)}
            >
              <div className="risk-header">
                <div className="task-name" aria-hidden="true">{task.name}</div>
                <div className="task-project" aria-hidden="true">{task.project}</div>
              </div>

              <div className="task-meta" aria-hidden="true">
                <span>👤 {task.assignee}</span>
                {task.videographer && <span>🎥 {task.videographer}</span>}
                {task.due_on && <span>📅 {task.due_on}</span>}
              </div>

              <div className="risk-factors" aria-hidden="true">
                {task.risks && task.risks.map((risk, i) => (
                  <div key={i} className="risk-factor">• {risk}</div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default memo(AtRiskTasks)
