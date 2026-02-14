import { memo } from 'react'
import type { TeamCapacityProps, TeamMember } from '../types/dashboard'
import './TeamCapacity.css'

function TeamCapacity({ team, onMemberClick }: TeamCapacityProps) {
  if (!team || team.length === 0) return null

  const handleKeyPress = (event: React.KeyboardEvent, member: TeamMember): void => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      onMemberClick && onMemberClick(member)
    }
  }

  return (
    <div className="card team-capacity">
      <h2 id="team-capacity-heading">👥 Team Capacity</h2>

      <div className="team-grid" role="list" aria-labelledby="team-capacity-heading">
        {team.map((member, index) => {
          const utilization = member.max > 0 ? (member.current / member.max * 100) : 0
          const status = utilization > 100 ? 'overloaded' : utilization > 80 ? 'high' : 'normal'
          const statusDescription = status === 'overloaded' ? 'overloaded' :
                                  status === 'high' ? 'high capacity' : 'normal capacity'

          return (
            <div
              key={index}
              className={`team-member ${status} clickable`}
              role="listitem button"
              tabIndex={0}
              aria-label={`${member.name} - ${utilization.toFixed(0)}% capacity utilized, ${statusDescription}. Current: ${member.current} hours, Maximum: ${member.max} hours. Press Enter or Space to view details.`}
              onClick={() => onMemberClick && onMemberClick(member)}
              onKeyDown={(e) => handleKeyPress(e, member)}
            >
              <div className="member-header">
                <div className="member-name" aria-hidden="true">{member.name}</div>
                <div className="member-utilization" aria-hidden="true">
                  {utilization.toFixed(0)}%
                </div>
              </div>

              <div className="capacity-bar-bg">
                <div
                  className={`capacity-bar ${status}`}
                  style={{ width: `${Math.min(utilization, 100)}%` }}
                  role="progressbar"
                  aria-valuenow={utilization}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`Capacity utilization: ${utilization.toFixed(1)}%`}
                  aria-hidden="true"
                ></div>
              </div>

              <div className="capacity-numbers" aria-hidden="true">
                <span>{member.current}h / {member.max}h</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default memo(TeamCapacity)
