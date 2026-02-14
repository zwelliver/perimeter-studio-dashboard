import jsPDF from 'jspdf'
import html2canvas from 'html2canvas'
import Papa from 'papaparse'
import { formatISO } from 'date-fns'
import type { DashboardData, ExportFormat, ExportOptions, Task, TeamMember, Shoot, Deadline } from '../types/dashboard'

// Export dashboard to PDF
export const exportToPDF = async (options: { includeCharts?: boolean } = {}): Promise<void> => {
  try {
    const { includeCharts = true } = options

    // Create new PDF document
    const pdf = new jsPDF('p', 'mm', 'a4')
    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    let yPosition = 20

    // Add header
    pdf.setFontSize(20)
    pdf.setTextColor(96, 187, 233)
    pdf.text('Studio Command Center Report', pageWidth / 2, yPosition, { align: 'center' })
    yPosition += 15

    // Add timestamp
    pdf.setFontSize(12)
    pdf.setTextColor(128, 128, 128)
    const timestamp = new Date().toLocaleString()
    pdf.text(`Generated: ${timestamp}`, pageWidth / 2, yPosition, { align: 'center' })
    yPosition += 20

    // If including charts, capture screenshots
    if (includeCharts) {
      const dashboardElement = document.querySelector('.dashboard-grid')
      if (dashboardElement) {
        try {
          const canvas = await html2canvas(dashboardElement as HTMLElement, {
            scale: 1,
            useCORS: true,
            allowTaint: true,
            backgroundColor: null
          })

          const imgData = canvas.toDataURL('image/png')
          const imgWidth = pageWidth - 20
          const imgHeight = (canvas.height * imgWidth) / canvas.width

          // Check if image fits on current page
          if (yPosition + imgHeight > pageHeight - 20) {
            pdf.addPage()
            yPosition = 20
          }

          pdf.addImage(imgData, 'PNG', 10, yPosition, imgWidth, imgHeight)
          yPosition += imgHeight + 10

        } catch (error) {
          console.warn('Failed to capture dashboard screenshot:', error)

          // Add fallback text
          pdf.setFontSize(14)
          pdf.setTextColor(255, 0, 0)
          pdf.text('Dashboard visualization could not be captured', 20, yPosition)
          yPosition += 20
        }
      }
    }

    // Add summary data
    const data = getDashboardDataFromDOM()
    if (data) {
      // Add new page for data
      pdf.addPage()
      yPosition = 20

      pdf.setFontSize(16)
      pdf.setTextColor(0, 0, 0)
      pdf.text('Dashboard Summary', 20, yPosition)
      yPosition += 15

      // Metrics
      if (data.metrics) {
        pdf.setFontSize(12)
        pdf.text(`Total Tasks: ${data.metrics.total_tasks}`, 20, yPosition)
        yPosition += 8
        pdf.text(`At-Risk Tasks: ${data.metrics.at_risk_count}`, 20, yPosition)
        yPosition += 8
        pdf.text(`Upcoming Shoots: ${data.metrics.upcoming_shoots}`, 20, yPosition)
        yPosition += 8
        pdf.text(`Upcoming Deadlines: ${data.metrics.upcoming_deadlines}`, 20, yPosition)
        yPosition += 15
      }
    }

    // Save PDF
    const filename = `studio-dashboard-${formatISO(new Date(), { representation: 'date' })}.pdf`
    pdf.save(filename)

  } catch (error) {
    console.error('PDF export failed:', error)
    throw new Error('Failed to export PDF. Please try again.')
  }
}

// Export data to CSV
export const exportToCSV = (data: DashboardData, type: 'tasks' | 'team' | 'shoots' | 'deadlines' | 'all'): void => {
  try {
    let csvData: any[] = []
    let filename = ''

    switch (type) {
      case 'tasks':
        csvData = formatTasksForCSV(data.at_risk_tasks)
        filename = `at-risk-tasks-${formatISO(new Date(), { representation: 'date' })}.csv`
        break

      case 'team':
        csvData = formatTeamForCSV(data.team_capacity)
        filename = `team-capacity-${formatISO(new Date(), { representation: 'date' })}.csv`
        break

      case 'shoots':
        csvData = formatShootsForCSV(data.upcoming_shoots)
        filename = `upcoming-shoots-${formatISO(new Date(), { representation: 'date' })}.csv`
        break

      case 'deadlines':
        csvData = formatDeadlinesForCSV(data.upcoming_deadlines)
        filename = `upcoming-deadlines-${formatISO(new Date(), { representation: 'date' })}.csv`
        break

      case 'all':
        csvData = formatAllDataForCSV(data)
        filename = `studio-dashboard-${formatISO(new Date(), { representation: 'date' })}.csv`
        break

      default:
        throw new Error('Invalid export type')
    }

    const csv = Papa.unparse(csvData)
    downloadCSV(csv, filename)

  } catch (error) {
    console.error('CSV export failed:', error)
    throw new Error('Failed to export CSV. Please try again.')
  }
}

// Export to JSON
export const exportToJSON = (data: DashboardData): void => {
  try {
    const exportData = {
      timestamp: new Date().toISOString(),
      data: data,
      metadata: {
        version: '1.0',
        source: 'Studio Command Center'
      }
    }

    const json = JSON.stringify(exportData, null, 2)
    const filename = `studio-dashboard-${formatISO(new Date(), { representation: 'date' })}.json`

    downloadJSON(json, filename)

  } catch (error) {
    console.error('JSON export failed:', error)
    throw new Error('Failed to export JSON. Please try again.')
  }
}

// Helper functions
const formatTasksForCSV = (tasks: Task[]): any[] => {
  return tasks.map(task => ({
    'Task Name': task.name,
    'Project': task.project,
    'Assignee': task.assignee,
    'Due Date': task.due_date || task.due_on || '',
    'Status': task.status,
    'Priority': task.priority || '',
    'Risk Factors': task.risks?.join('; ') || task.reasons?.join('; ') || '',
    'Videographer': task.videographer || ''
  }))
}

const formatTeamForCSV = (team: TeamMember[]): any[] => {
  return team.map(member => {
    const utilization = member.max > 0 ? (member.current / member.max * 100).toFixed(1) : '0'
    return {
      'Name': member.name,
      'Current Hours': member.current,
      'Max Hours': member.max,
      'Utilization %': utilization,
      'Available Hours': member.max - member.current,
      'Status': member.status || (parseFloat(utilization) > 100 ? 'overloaded' : parseFloat(utilization) > 80 ? 'high' : 'normal')
    }
  })
}

const formatShootsForCSV = (shoots: Shoot[]): any[] => {
  return shoots.map(shoot => ({
    'Shoot Name': shoot.name,
    'Date': shoot.date,
    'Time': shoot.time || '',
    'Location': shoot.location || '',
    'Client': shoot.client || '',
    'Crew': Array.isArray(shoot.crew) ? shoot.crew.join('; ') : shoot.crew || '',
    'Status': shoot.status || ''
  }))
}

const formatDeadlinesForCSV = (deadlines: Deadline[]): any[] => {
  return deadlines.map(deadline => ({
    'Deadline Name': deadline.name,
    'Date': deadline.date,
    'Project': deadline.project,
    'Assignee': deadline.assignee || '',
    'Priority': deadline.priority || '',
    'Status': deadline.status || '',
    'Type': deadline.type || ''
  }))
}

const formatAllDataForCSV = (data: DashboardData): any[] => {
  const summary = [{
    'Type': 'Summary',
    'Total Tasks': data.metrics.total_tasks,
    'At-Risk Tasks': data.metrics.at_risk_count,
    'Upcoming Shoots': data.metrics.upcoming_shoots,
    'Upcoming Deadlines': data.metrics.upcoming_deadlines,
    'Team Utilization': data.metrics.team_utilization || '',
    'Overloaded Members': data.metrics.overloaded_members || ''
  }]

  return summary
}

// DOM helpers
const getDashboardDataFromDOM = (): DashboardData | null => {
  // Try to get data from the React app's state
  // This is a fallback method - ideally we'd pass the data directly
  return null
}

// Download helpers
const downloadCSV = (csv: string, filename: string): void => {
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)

  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}

const downloadJSON = (json: string, filename: string): void => {
  const blob = new Blob([json], { type: 'application/json;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)

  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'

  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}