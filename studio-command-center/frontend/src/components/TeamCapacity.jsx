import './TeamCapacity.css'

function TeamCapacity({ team, onMemberClick }) {
  if (!team || team.length === 0) return null

  return (
    <div className="card team-capacity">
      <h2>👥 Team Capacity</h2>

      <div className="team-grid">
        {team.map((member, index) => {
          const utilization = member.max > 0 ? (member.current / member.max * 100) : 0
          const status = utilization > 100 ? 'overloaded' : utilization > 80 ? 'high' : 'normal'

          return (
            <div
              key={index}
              className={`team-member ${status} clickable`}
              onClick={() => onMemberClick && onMemberClick(member)}
            >
              <div className="member-header">
                <div className="member-name">{member.name}</div>
                <div className="member-utilization">
                  {utilization.toFixed(0)}%
                </div>
              </div>

              <div className="capacity-bar-bg">
                <div
                  className={`capacity-bar ${status}`}
                  style={{ width: `${Math.min(utilization, 100)}%` }}
                ></div>
              </div>

              <div className="capacity-numbers">
                <span>{member.current}h / {member.max}h</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default TeamCapacity
