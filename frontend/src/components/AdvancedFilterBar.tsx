import { useState, useEffect, useMemo } from 'react'
import type { Filters, FilterOption, DashboardData } from '../types/dashboard'
import './AdvancedFilterBar.css'

interface AdvancedFilterBarProps {
  filters: Filters
  onFiltersChange: (filters: Filters) => void
  data: DashboardData | null
}

function AdvancedFilterBar({ filters, onFiltersChange, data }: AdvancedFilterBarProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [searchValue, setSearchValue] = useState(filters.search)

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onFiltersChange({ ...filters, search: searchValue })
    }, 300)

    return () => clearTimeout(timer)
  }, [searchValue])

  // Generate filter options from data
  const filterOptions = useMemo(() => {
    if (!data) return { projects: [], teamMembers: [], statuses: [], priorities: [] }

    const projects = new Set<string>()
    const teamMembers = new Set<string>()
    const statuses = new Set<string>()
    const priorities = new Set<string>()

    // Collect from tasks
    data.at_risk_tasks?.forEach(task => {
      if (task.project) projects.add(task.project)
      if (task.assignee) teamMembers.add(task.assignee)
      if (task.status) statuses.add(task.status)
      if (task.priority !== undefined) priorities.add(task.priority.toString())
    })

    // Collect from team
    data.team_capacity?.forEach(member => {
      teamMembers.add(member.name)
      if (member.status) statuses.add(member.status)
    })

    // Collect from shoots and deadlines
    data.upcoming_shoots?.forEach(shoot => {
      if (shoot.status) statuses.add(shoot.status)
    })

    data.upcoming_deadlines?.forEach(deadline => {
      if (deadline.project) projects.add(deadline.project)
      if (deadline.assignee) teamMembers.add(deadline.assignee)
      if (deadline.status) statuses.add(deadline.status)
      if (deadline.priority) priorities.add(deadline.priority)
    })

    return {
      projects: Array.from(projects).sort().map(p => ({ value: p, label: p })),
      teamMembers: Array.from(teamMembers).sort().map(m => ({ value: m, label: m })),
      statuses: Array.from(statuses).sort().map(s => ({ value: s, label: s })),
      priorities: Array.from(priorities).sort().map(p => ({ value: p, label: p }))
    }
  }, [data])

  const handleFilterChange = (key: keyof Filters, value: any) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const handleMultiSelectChange = (key: keyof Filters, value: string, checked: boolean) => {
    const currentValues = (filters[key] as string[]) || []
    const newValues = checked
      ? [...currentValues, value]
      : currentValues.filter(v => v !== value)

    handleFilterChange(key, newValues)
  }

  const clearAllFilters = () => {
    setSearchValue('')
    onFiltersChange({
      search: '',
      project: '',
      teamMember: '',
      sortBy: 'date',
      status: [],
      priority: []
    })
  }

  const hasActiveFilters =
    filters.search ||
    filters.project ||
    filters.teamMember ||
    (filters.status && filters.status.length > 0) ||
    (filters.priority && filters.priority.length > 0)

  return (
    <div className="advanced-filter-bar">
      <div className="filter-header">
        <div className="search-section">
          <div className="search-input-wrapper">
            <span className="search-icon" aria-hidden="true">🔍</span>
            <input
              type="text"
              placeholder="Search tasks, projects, team members..."
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              className="search-input"
              aria-label="Search dashboard content"
            />
            {searchValue && (
              <button
                className="clear-search"
                onClick={() => setSearchValue('')}
                aria-label="Clear search"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        <div className="filter-controls">
          <button
            className="filter-toggle"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-expanded={isExpanded}
            aria-label={`${isExpanded ? 'Hide' : 'Show'} advanced filters`}
          >
            <span aria-hidden="true">🔧</span>
            Filters
            <span className={`chevron ${isExpanded ? 'expanded' : ''}`} aria-hidden="true">▼</span>
          </button>

          {hasActiveFilters && (
            <button
              className="clear-filters"
              onClick={clearAllFilters}
              aria-label="Clear all filters"
            >
              <span aria-hidden="true">✕</span>
              Clear All
            </button>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="filter-panel">
          <div className="filter-grid">
            {/* Sort By */}
            <div className="filter-group">
              <label htmlFor="sort-select" className="filter-label">Sort By</label>
              <select
                id="sort-select"
                value={filters.sortBy}
                onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                className="filter-select"
              >
                <option value="date">Date</option>
                <option value="priority">Priority</option>
                <option value="project">Project</option>
                <option value="assignee">Assignee</option>
              </select>
            </div>

            {/* Project Filter */}
            <div className="filter-group">
              <label htmlFor="project-select" className="filter-label">Project</label>
              <select
                id="project-select"
                value={filters.project}
                onChange={(e) => handleFilterChange('project', e.target.value)}
                className="filter-select"
              >
                <option value="">All Projects</option>
                {filterOptions.projects.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Team Member Filter */}
            <div className="filter-group">
              <label htmlFor="team-select" className="filter-label">Team Member</label>
              <select
                id="team-select"
                value={filters.teamMember}
                onChange={(e) => handleFilterChange('teamMember', e.target.value)}
                className="filter-select"
              >
                <option value="">All Members</option>
                {filterOptions.teamMembers.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Multi-select filters */}
          <div className="multi-select-section">
            {/* Status Filter */}
            <div className="filter-group">
              <div className="filter-label">Status</div>
              <div className="checkbox-group">
                {filterOptions.statuses.map(option => (
                  <label key={option.value} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={(filters.status || []).includes(option.value)}
                      onChange={(e) => handleMultiSelectChange('status', option.value, e.target.checked)}
                      className="checkbox-input"
                    />
                    <span className="checkbox-text">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Priority Filter */}
            <div className="filter-group">
              <div className="filter-label">Priority</div>
              <div className="checkbox-group">
                {filterOptions.priorities.map(option => (
                  <label key={option.value} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={(filters.priority || []).includes(option.value)}
                      onChange={(e) => handleMultiSelectChange('priority', option.value, e.target.checked)}
                      className="checkbox-input"
                    />
                    <span className="checkbox-text">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Active filter chips */}
      {hasActiveFilters && (
        <div className="active-filters">
          <span className="active-filters-label">Active filters:</span>
          {filters.search && (
            <span className="filter-chip">
              Search: "{filters.search}"
              <button onClick={() => setSearchValue('')} aria-label="Remove search filter">✕</button>
            </span>
          )}
          {filters.project && (
            <span className="filter-chip">
              Project: {filters.project}
              <button onClick={() => handleFilterChange('project', '')} aria-label="Remove project filter">✕</button>
            </span>
          )}
          {filters.teamMember && (
            <span className="filter-chip">
              Team: {filters.teamMember}
              <button onClick={() => handleFilterChange('teamMember', '')} aria-label="Remove team member filter">✕</button>
            </span>
          )}
          {(filters.status || []).map(status => (
            <span key={status} className="filter-chip">
              Status: {status}
              <button onClick={() => handleMultiSelectChange('status', status, false)} aria-label={`Remove status filter: ${status}`}>✕</button>
            </span>
          ))}
          {(filters.priority || []).map(priority => (
            <span key={priority} className="filter-chip">
              Priority: {priority}
              <button onClick={() => handleMultiSelectChange('priority', priority, false)} aria-label={`Remove priority filter: ${priority}`}>✕</button>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

export default AdvancedFilterBar