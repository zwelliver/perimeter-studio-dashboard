import { useState, useEffect, useMemo, lazy, Suspense } from 'react'
import type { DashboardData, Filters, ModalType, TeamMember, Task, Shoot, Deadline } from './types/dashboard'
import { useTheme } from './hooks/useTheme'
import './styles/App.css'
import StatusBoard from './components/StatusBoard'
import TeamCapacity from './components/TeamCapacity'
import AtRiskTasks from './components/AtRiskTasks'
import UpcomingEvents from './components/UpcomingEvents'
import Header from './components/Header'
import AdvancedFilterBar from './components/AdvancedFilterBar'
import SkeletonCard from './components/SkeletonCard'

// Lazy load heavy components
const DetailModal = lazy(() => import('./components/DetailModal'))
const ProjectInsights = lazy(() => import('./components/ProjectInsights'))

function App() {
  // Theme management
  const { theme, toggleTheme } = useTheme()

  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)
  const [autoRefresh, setAutoRefresh] = useState<boolean>(true)

  // Filter state
  const [filters, setFilters] = useState<Filters>({
    search: '',
    project: '',
    teamMember: '',
    sortBy: 'date',
    status: [],
    priority: []
  })

  // Modal state
  const [selectedItem, setSelectedItem] = useState<Task | Shoot | Deadline | TeamMember | null>(null)
  const [modalType, setModalType] = useState<ModalType>(null)

  const fetchData = async (): Promise<void> => {
    try {
      const response = await fetch('/api/dashboard')
      if (!response.ok) throw new Error('Failed to fetch data')
      const json: DashboardData = await response.json()
      setData(json)
      setLastUpdate(new Date())
      setError(null)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(errorMessage)
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

  const openDetailModal = (item: Task | Shoot | Deadline | TeamMember, type: ModalType): void => {
    setSelectedItem(item)
    setModalType(type)
  }

  const closeDetailModal = (): void => {
    setSelectedItem(null)
    setModalType(null)
  }

  // Filter and sort data
  const filteredData = useMemo(() => {
    if (!data) return null

    const filterBySearch = (items: any[], getName: (item: any) => string) => {
      if (!filters.search) return items
      const search = filters.search.toLowerCase()
      return items.filter(item => {
        const name = getName(item)
        const project = item.project || ''
        const assignee = item.assignee || item.name || ''
        return name.toLowerCase().includes(search) ||
               project.toLowerCase().includes(search) ||
               assignee.toLowerCase().includes(search)
      })
    }

    const filterByProject = (items: any[]) => {
      if (!filters.project) return items
      return items.filter(item => item.project === filters.project)
    }

    const filterByTeamMember = (items: any[]) => {
      if (!filters.teamMember) return items
      return items.filter(item => item.assignee === filters.teamMember || item.name === filters.teamMember)
    }

    const filterByStatus = (items: any[]) => {
      if (!filters.status || filters.status.length === 0) return items
      return items.filter(item => item.status && filters.status!.includes(item.status))
    }

    const filterByPriority = (items: any[]) => {
      if (!filters.priority || filters.priority.length === 0) return items
      return items.filter(item => {
        const priority = item.priority?.toString() || ''
        return priority && filters.priority!.includes(priority)
      })
    }

    const sortItems = (items: any[]) => {
      const sorted = [...items]
      switch (filters.sortBy) {
        case 'priority':
          return sorted.sort((a, b) => {
            const aPriority = parseInt(a.priority?.toString() || '0')
            const bPriority = parseInt(b.priority?.toString() || '0')
            return bPriority - aPriority
          })
        case 'project':
          return sorted.sort((a, b) => (a.project || '').localeCompare(b.project || ''))
        case 'assignee':
          return sorted.sort((a, b) => (a.assignee || a.name || '').localeCompare(b.assignee || b.name || ''))
        case 'date':
        default:
          return sorted.sort((a, b) => {
            const aDate = new Date(a.due_date || a.due_on || a.date || 0)
            const bDate = new Date(b.due_date || b.due_on || b.date || 0)
            return aDate.getTime() - bDate.getTime()
          })
      }
    }

    // Filter at-risk tasks
    let filteredTasks = data.at_risk_tasks || []
    filteredTasks = filterBySearch(filteredTasks, t => t.name)
    filteredTasks = filterByProject(filteredTasks)
    filteredTasks = filterByTeamMember(filteredTasks)
    filteredTasks = filterByStatus(filteredTasks)
    filteredTasks = filterByPriority(filteredTasks)
    filteredTasks = sortItems(filteredTasks)

    // Filter shoots
    let filteredShoots = data.upcoming_shoots || []
    filteredShoots = filterBySearch(filteredShoots, s => s.name)
    filteredShoots = filterByStatus(filteredShoots)
    filteredShoots = sortItems(filteredShoots)

    // Filter deadlines
    let filteredDeadlines = data.upcoming_deadlines || []
    filteredDeadlines = filterBySearch(filteredDeadlines, d => d.name)
    filteredDeadlines = filterByProject(filteredDeadlines)
    filteredDeadlines = filterByTeamMember(filteredDeadlines)
    filteredDeadlines = filterByStatus(filteredDeadlines)
    filteredDeadlines = filterByPriority(filteredDeadlines)
    filteredDeadlines = sortItems(filteredDeadlines)

    // Filter team capacity
    let filteredTeam = data.team_capacity || []
    if (filters.teamMember) {
      filteredTeam = filteredTeam.filter(m => m.name === filters.teamMember)
    }
    if (filters.status && filters.status.length > 0) {
      filteredTeam = filteredTeam.filter(m => {
        const utilization = m.max > 0 ? (m.current / m.max * 100) : 0
        const status = utilization > 100 ? 'overloaded' : utilization > 80 ? 'high' : 'normal'
        return filters.status!.includes(status) || filters.status!.includes(m.status || '')
      })
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
      <div className="app">
        <Header
          lastUpdate={null}
          onRefresh={() => {}}
          autoRefresh={autoRefresh}
          onToggleAutoRefresh={() => setAutoRefresh(!autoRefresh)}
          loading={true}
          theme={theme}
          onToggleTheme={toggleTheme}
          data={null}
        />

        <main className="dashboard-grid">
          <SkeletonCard type="default" />
          <SkeletonCard type="team" />
          <SkeletonCard type="chart" height="300px" />
          <div className="grid-row-2col">
            <SkeletonCard type="list" />
            <SkeletonCard type="list" />
          </div>
        </main>
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
        theme={theme}
        onToggleTheme={toggleTheme}
        data={data}
      />

      <main className="dashboard-grid">
        {/* Advanced Filter Bar */}
        <AdvancedFilterBar
          filters={filters}
          onFiltersChange={setFilters}
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
        <Suspense fallback={<SkeletonCard type="chart" height="300px" />}>
          <ProjectInsights
            tasks={filteredData?.at_risk_tasks}
            team={filteredData?.team_capacity}
            shoots={filteredData?.upcoming_shoots}
            deadlines={filteredData?.upcoming_deadlines}
          />
        </Suspense>

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
        <Suspense fallback={<div className="modal-loading">Loading details...</div>}>
          <DetailModal
            item={selectedItem}
            type={modalType}
            onClose={closeDetailModal}
          />
        </Suspense>
      )}
    </div>
  )
}

export default App
