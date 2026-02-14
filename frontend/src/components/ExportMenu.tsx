import { useState, useRef, useEffect } from 'react'
import type { DashboardData, ExportFormat } from '../types/dashboard'
import { exportToPDF, exportToCSV, exportToJSON } from '../utils/exportUtils'
import './ExportMenu.css'

interface ExportMenuProps {
  data: DashboardData | null
  disabled?: boolean
}

function ExportMenu({ data, disabled = false }: ExportMenuProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [exportType, setExportType] = useState<string>('')
  const menuRef = useRef<HTMLDivElement>(null)

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleExport = async (format: ExportFormat, type?: string) => {
    if (!data || isExporting) return

    setIsExporting(true)
    setExportType(format)
    setIsOpen(false)

    try {
      switch (format) {
        case 'pdf':
          await exportToPDF({ includeCharts: true })
          break

        case 'csv':
          if (type) {
            exportToCSV(data, type as 'tasks' | 'team' | 'shoots' | 'deadlines' | 'all')
          } else {
            exportToCSV(data, 'all')
          }
          break

        case 'json':
          exportToJSON(data)
          break

        default:
          throw new Error('Unsupported export format')
      }

      // Show success message
      showNotification('Export completed successfully!', 'success')

    } catch (error) {
      console.error('Export failed:', error)
      showNotification('Export failed. Please try again.', 'error')
    } finally {
      setIsExporting(false)
      setExportType('')
    }
  }

  const showNotification = (message: string, type: 'success' | 'error') => {
    // Create a temporary notification
    const notification = document.createElement('div')
    notification.className = `export-notification ${type}`
    notification.textContent = message

    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 12px 20px;
      border-radius: 8px;
      color: white;
      font-weight: 500;
      z-index: 10000;
      animation: slideInRight 0.3s ease;
      background: ${type === 'success' ? '#22c55e' : '#ef4444'};
    `

    document.body.appendChild(notification)

    // Remove after 3 seconds
    setTimeout(() => {
      notification.style.animation = 'slideOutRight 0.3s ease'
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification)
        }
      }, 300)
    }, 3000)
  }

  return (
    <div className="export-menu" ref={menuRef}>
      <button
        className="export-trigger"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || !data || isExporting}
        aria-label="Export dashboard data"
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        {isExporting ? (
          <>
            <span className="spinner" aria-hidden="true">⏳</span>
            Exporting...
          </>
        ) : (
          <>
            <span aria-hidden="true">📥</span>
            Export
          </>
        )}
      </button>

      {isOpen && !isExporting && (
        <div className="export-dropdown" role="menu">
          {/* PDF Export */}
          <div className="export-section">
            <div className="export-section-title">PDF Report</div>
            <button
              className="export-option"
              onClick={() => handleExport('pdf')}
              role="menuitem"
            >
              <span className="export-icon">📄</span>
              <div className="export-details">
                <div className="export-name">Full Dashboard</div>
                <div className="export-description">Complete report with charts</div>
              </div>
            </button>
          </div>

          {/* CSV Export */}
          <div className="export-section">
            <div className="export-section-title">CSV Data</div>
            <button
              className="export-option"
              onClick={() => handleExport('csv', 'all')}
              role="menuitem"
            >
              <span className="export-icon">📊</span>
              <div className="export-details">
                <div className="export-name">Summary Data</div>
                <div className="export-description">Key metrics and counts</div>
              </div>
            </button>
            <button
              className="export-option"
              onClick={() => handleExport('csv', 'tasks')}
              role="menuitem"
            >
              <span className="export-icon">⚠️</span>
              <div className="export-details">
                <div className="export-name">At-Risk Tasks</div>
                <div className="export-description">Task details and risk factors</div>
              </div>
            </button>
            <button
              className="export-option"
              onClick={() => handleExport('csv', 'team')}
              role="menuitem"
            >
              <span className="export-icon">👥</span>
              <div className="export-details">
                <div className="export-name">Team Capacity</div>
                <div className="export-description">Member utilization data</div>
              </div>
            </button>
            <button
              className="export-option"
              onClick={() => handleExport('csv', 'shoots')}
              role="menuitem"
            >
              <span className="export-icon">🎬</span>
              <div className="export-details">
                <div className="export-name">Upcoming Shoots</div>
                <div className="export-description">Shoot schedule and details</div>
              </div>
            </button>
            <button
              className="export-option"
              onClick={() => handleExport('csv', 'deadlines')}
              role="menuitem"
            >
              <span className="export-icon">📅</span>
              <div className="export-details">
                <div className="export-name">Deadlines</div>
                <div className="export-description">Upcoming deadline list</div>
              </div>
            </button>
          </div>

          {/* JSON Export */}
          <div className="export-section">
            <div className="export-section-title">Raw Data</div>
            <button
              className="export-option"
              onClick={() => handleExport('json')}
              role="menuitem"
            >
              <span className="export-icon">🗂️</span>
              <div className="export-details">
                <div className="export-name">JSON Export</div>
                <div className="export-description">Complete data structure</div>
              </div>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default ExportMenu