import './AtRiskTasks.css'

function AtRiskTasks({ tasks, onTaskClick }) {
  if (!tasks || tasks.length === 0) {
    return (
      <div className="card at-risk-tasks">
        <h2>⚠️ At-Risk Tasks</h2>
        <div className="no-tasks">
          <div className="success-icon">✅</div>
          <p>No tasks currently at risk!</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card at-risk-tasks">
      <h2>⚠️ At-Risk Tasks</h2>
      <div className="task-count">{tasks.length} task{tasks.length !== 1 ? 's' : ''} at risk</div>

      <div className="risk-list">
        {tasks.slice(0, 10).map((task, index) => (
          <div
            key={index}
            className="risk-item clickable"
            onClick={() => onTaskClick && onTaskClick(task)}
          >
            <div className="risk-header">
              <div className="task-name">{task.name}</div>
              <div className="task-project">{task.project}</div>
            </div>

            <div className="task-meta">
              <span>👤 {task.assignee}</span>
              {task.videographer && <span>🎥 {task.videographer}</span>}
              {task.due_on && <span>📅 {task.due_on}</span>}
            </div>

            <div className="risk-factors">
              {task.risks && task.risks.map((risk, i) => (
                <div key={i} className="risk-factor">• {risk}</div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AtRiskTasks
