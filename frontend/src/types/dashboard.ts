// Dashboard Data Types
export interface TeamMember {
  name: string
  current: number
  max: number
  status?: 'normal' | 'high' | 'overloaded'
  utilization?: number
}

export interface Task {
  id?: string
  name: string
  project: string
  assignee: string
  due_date?: string
  due_on?: string
  priority?: number
  status: string
  risks?: string[]
  reasons?: string[]
  videographer?: string
}

export interface Shoot {
  id?: string
  name: string
  date: string
  time?: string
  location?: string
  client?: string
  crew?: string[]
  status?: string
}

export interface Deadline {
  id?: string
  name: string
  date: string
  project: string
  assignee?: string
  priority?: 'low' | 'medium' | 'high' | 'critical'
  status?: string
  type?: string
}

export interface DashboardMetrics {
  total_tasks: number
  at_risk_count: number
  upcoming_shoots: number
  upcoming_deadlines: number
  team_utilization?: number
  overloaded_members?: number
}

export interface DashboardData {
  metrics: DashboardMetrics
  team_capacity: TeamMember[]
  at_risk_tasks: Task[]
  upcoming_shoots: Shoot[]
  upcoming_deadlines: Deadline[]
  categories?: string[]
  delivery_metrics?: any
}

// Filter and UI Types
export interface Filters {
  search: string
  project: string
  teamMember: string
  sortBy: 'date' | 'priority' | 'project' | 'assignee'
  dateRange?: {
    start: Date | null
    end: Date | null
  }
  status?: string[]
  priority?: string[]
}

export interface FilterOption {
  value: string
  label: string
  count?: number
}

// Modal Types
export type ModalType = 'task' | 'shoot' | 'deadline' | 'member' | null

export interface ModalProps {
  item: Task | Shoot | Deadline | TeamMember | null
  type: ModalType
  onClose: () => void
}

// Chart Data Types
export interface ChartDataPoint {
  name: string
  value: number
  color?: string
  label?: string
}

export interface TimeSeriesPoint {
  date: string
  value: number
  category?: string
}

// Theme Types
export type Theme = 'light' | 'dark'

export interface ThemeContextType {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

// Component Props Types
export interface HeaderProps {
  lastUpdate: Date | null
  onRefresh: () => void
  autoRefresh: boolean
  onToggleAutoRefresh: () => void
  loading: boolean
}

export interface StatusBoardProps {
  metrics: DashboardMetrics | undefined
}

export interface TeamCapacityProps {
  team: TeamMember[] | undefined
  onMemberClick?: (member: TeamMember) => void
}

export interface AtRiskTasksProps {
  tasks: Task[] | undefined
  onTaskClick?: (task: Task) => void
}

export interface UpcomingEventsProps {
  shoots: Shoot[] | undefined
  deadlines: Deadline[] | undefined
  onShootClick?: (shoot: Shoot) => void
  onDeadlineClick?: (deadline: Deadline) => void
}

export interface FilterBarProps {
  filters: Filters
  onFiltersChange: (filters: Filters) => void
  data: DashboardData | null
}

export interface ProjectInsightsProps {
  tasks: Task[] | undefined
  team: TeamMember[] | undefined
  shoots: Shoot[] | undefined
  deadlines: Deadline[] | undefined
}

// Error Boundary Types
export interface ErrorInfo {
  componentStack: string
}

export interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

export interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{
    error: Error | null
    errorInfo: ErrorInfo | null
    resetError: () => void
  }>
}

// API Response Types
export interface ApiResponse<T> {
  data: T
  success: boolean
  message?: string
  timestamp?: string
}

export interface ApiError {
  message: string
  code?: string | number
  details?: any
}

// Export Types
export type ExportFormat = 'pdf' | 'csv' | 'json'

export interface ExportOptions {
  format: ExportFormat
  includeCharts: boolean
  dateRange?: {
    start: Date
    end: Date
  }
  sections?: string[]
}