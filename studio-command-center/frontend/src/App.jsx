import { useState, useEffect, useMemo } from 'react'
import './styles/App.css'
import StatusBoard from './components/StatusBoard'
import TeamCapacity from './components/TeamCapacity'
import AtRiskTasks from './components/AtRiskTasks'
import UpcomingEvents from './components/UpcomingEvents'
import Header from './components/Header'
import FilterBar from './components/FilterBar'
import DetailModal from './components/DetailModal'
import ProjectInsights from './components/ProjectInsights'

function App() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Filter state
  const [filters, setFilters] = useState({
    search: '',
    project: '',
    teamMember: '',
    sortBy: 'date'
  })

  // Modal state
  const [selectedItem, setSelectedItem] = useState(null)
  const [modalType, setModalType] = useState(null)

  const fetchData = async () => {
    try {
      const response = await fetch('/api/dashboard')
      if (!response.ok) throw new Error('Failed to fetch data')
      const json = await response.json()
      setData(json)
      setLastUpdate(new Date())
      setError(null)
    } catch (err) {
      setError(err.message)
      console.error('Error fetching data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    setLoading(true)
    await fetch('/api/refresh')
    await fetchData()
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const openDetailModal = (item, type) => {
    setSelectedItem(item)
    setModalType(type)
  }

  const closeDetailModal = () => {
    setSelectedItem(null)
    setModalType(null)
  }

  // Filter and sort data
  const filteredData = useMemo(() => {
    if (!data) return null

    const filterBySearch = (items, getName) => {
      if (!filters.search) return items
      const search = filters.search.toLowerCase()
      return items.filter(item => getName(item).toLowerCase().includes(search))
    }

    const filterByProject = (items) => {
      if (!filters.project) return items
      return items.filter(item => item.project === filters.project)
    }

    const filterByTeamMember = (items) => {
      if (!filters.teamMember) return items
      return items.filter(item => item.assignee === filters.teamMember || item.name === filters.teamMember)
    }

    const sortItems = (items) => {
      const sorted = [...items]
      switch (filters.sortBy) {
        case 'name':
          return sorted.sort((a, b) => a.name.localeCompare(b.name))
        case 'name-desc':
          return sorted.sort((a, b) => b.name.localeCompare(a.name))
        case 'date-desc':
          return sorted.reverse()
        default: // 'date' or 'priority'
          return sorted
      }
    }

    // Filter at-risk tasks
    let filteredTasks = data.at_risk_tasks || []
    filteredTasks = filterBySearch(filteredTasks, t => t.name)
    filteredTasks = filterByProject(filteredTasks)
    filteredTasks = filterByTeamMember(filteredTasks)
    filteredTasks = sortItems(filteredTasks)

    // Filter shoots
    let filteredShoots = data.upcoming_shoots || []
    filteredShoots = filterBySearch(filteredShoots, s => s.name)
    filteredShoots = filterByProject(filteredShoots)
    filteredShoots = sortItems(filteredShoots)

    // Filter deadlines
    let filteredDeadlines = data.upcoming_deadlines || []
    filteredDeadlines = filterBySearch(filteredDeadlines, d => d.name)
    filteredDeadlines = filterByProject(filteredDeadlines)
    filteredDeadlines = sortItems(filteredDeadlines)

    // Filter team capacity
    let filteredTeam = data.team_capacity || []
    if (filters.teamMember) {
      filteredTeam = filteredTeam.filter(m => m.name === filters.teamMember)
    }

    return {
      ...data,
      at_risk_tasks: filteredTasks,
      upcoming_shoots: filteredShoots,
      upcoming_deadlines: filteredDeadlines,
      team_capacity: filteredTeam
    }
  }, [data, filters])

  // Initial fetch
  useEffect(() => {
    fetchData()
  }, [])

  // Auto-refresh every 2 minutes if enabled
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      fetchData()
    }, 120000) // 2 minutes

    return () => clearInterval(interval)
  }, [autoRefresh])

  if (loading && !data) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading Studio Command Center...</p>
      </div>
    )
  }

  if (error && !data) {
    return (
      <div className="error-container">
        <h2>⚠️ Error Loading Data</h2>
        <p>{error}</p>
        <button onClick={handleRefresh}>Retry</button>
      </div>
    )
  }

  return (
    <div className="app">
      <Header
        lastUpdate={lastUpdate}
        onRefresh={handleRefresh}
        autoRefresh={autoRefresh}
        onToggleAutoRefresh={() => setAutoRefresh(!autoRefresh)}
        loading={loading}
      />

      <main className="dashboard-grid">
        {/* Filter Bar */}
        <FilterBar
          filters={filters}
          onFilterChange={handleFilterChange}
          data={data}
        />

        {/* Top Row - Status Metrics */}
        <StatusBoard metrics={filteredData?.metrics} />

        {/* Second Row - Team Capacity */}
        <TeamCapacity
          team={filteredData?.team_capacity}
          onMemberClick={(member) => setFilters(prev => ({ ...prev, teamMember: member.name }))}
        />

        {/* Interactive Charts */}
        <ProjectInsights
          tasks={filteredData?.at_risk_tasks}
          team={filteredData?.team_capacity}
          shoots={filteredData?.upcoming_shoots}
          deadlines={filteredData?.upcoming_deadlines}
        />

        {/* Third Row - At-Risk and Upcoming Events */}
        <div className="grid-row-2col">
          <AtRiskTasks
            tasks={filteredData?.at_risk_tasks}
            onTaskClick={(task) => openDetailModal(task, 'task')}
          />
          <UpcomingEvents
            shoots={filteredData?.upcoming_shoots}
            deadlines={filteredData?.upcoming_deadlines}
            onShootClick={(shoot) => openDetailModal(shoot, 'shoot')}
            onDeadlineClick={(deadline) => openDetailModal(deadline, 'deadline')}
          />
        </div>
      </main>

      {/* Detail Modal */}
      {selectedItem && (
        <DetailModal
          item={selectedItem}
          type={modalType}
          onClose={closeDetailModal}
        />
      )}
    </div>
  )
}

export default App
