import { useState } from 'react'
import './FilterBar.css'

function FilterBar({ filters, onFilterChange, data }) {
  const [showFilters, setShowFilters] = useState(false)

  // Extract unique values for filter dropdowns
  const projects = data ? [...new Set([
    ...data.at_risk_tasks?.map(t => t.project) || [],
    ...data.upcoming_shoots?.map(s => s.project) || [],
    ...data.upcoming_deadlines?.map(d => d.project) || []
  ])].sort() : []

  const teamMembers = data?.team_capacity?.map(m => m.name).sort() || []

  return (
    <div className="filter-bar">
      <div className="filter-bar-main">
        {/* Search Input */}
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search tasks, shoots, deadlines..."
            value={filters.search}
            onChange={(e) => onFilterChange('search', e.target.value)}
            className="search-input"
          />
          {filters.search && (
            <button
              className="clear-search"
              onClick={() => onFilterChange('search', '')}
            >
              ✕
            </button>
          )}
        </div>

        {/* Toggle Filters Button */}
        <button
          className={`toggle-filters-btn ${showFilters ? 'active' : ''}`}
          onClick={() => setShowFilters(!showFilters)}
        >
          <span>🎛️</span>
          Filters
          {(filters.project || filters.teamMember) && (
            <span className="active-filter-badge">
              {[filters.project, filters.teamMember].filter(Boolean).length}
            </span>
          )}
        </button>

        {/* Clear All */}
        {(filters.search || filters.project || filters.teamMember) && (
          <button
            className="clear-all-btn"
            onClick={() => {
              onFilterChange('search', '')
              onFilterChange('project', '')
              onFilterChange('teamMember', '')
            }}
          >
            Clear All
          </button>
        )}
      </div>

      {/* Expandable Filter Panel */}
      {showFilters && (
        <div className="filter-panel">
          <div className="filter-group">
            <label>Project</label>
            <select
              value={filters.project}
              onChange={(e) => onFilterChange('project', e.target.value)}
            >
              <option value="">All Projects</option>
              {projects.map(project => (
                <option key={project} value={project}>{project}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Team Member</label>
            <select
              value={filters.teamMember}
              onChange={(e) => onFilterChange('teamMember', e.target.value)}
            >
              <option value="">All Team Members</option>
              {teamMembers.map(member => (
                <option key={member} value={member}>{member}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Sort By</label>
            <select
              value={filters.sortBy}
              onChange={(e) => onFilterChange('sortBy', e.target.value)}
            >
              <option value="date">Date (Earliest First)</option>
              <option value="date-desc">Date (Latest First)</option>
              <option value="name">Name (A-Z)</option>
              <option value="name-desc">Name (Z-A)</option>
              <option value="priority">Priority</option>
            </select>
          </div>
        </div>
      )}
    </div>
  )
}

export default FilterBar
