import { useState } from 'react'
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import './ProjectInsights.css'

function ProjectInsights({ tasks, team, shoots, deadlines }) {
  const [activeChart, setActiveChart] = useState('projects')

  // Calculate project distribution
  const projectData = () => {
    if (!tasks) return []

    const projectCounts = {}
    tasks.forEach(task => {
      projectCounts[task.project] = (projectCounts[task.project] || 0) + 1
    })

    return Object.entries(projectCounts)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8)
  }

  // Calculate team workload
  const teamData = () => {
    if (!team) return []

    return team.map(member => ({
      name: member.name,
      current: member.current,
      max: member.max,
      utilization: member.max > 0 ? (member.current / member.max * 100).toFixed(0) : 0
    }))
  }

  // Calculate upcoming workload by week
  const timelineData = () => {
    if (!shoots && !deadlines) return []

    const weeks = {}
    const now = new Date()

    // Add shoots
    shoots?.forEach(shoot => {
      const date = new Date(shoot.datetime)
      const weekNum = Math.floor((date - now) / (7 * 24 * 60 * 60 * 1000))
      if (weekNum >= 0 && weekNum < 4) {
        const weekLabel = weekNum === 0 ? 'This Week' : `Week +${weekNum}`
        weeks[weekLabel] = weeks[weekLabel] || { shoots: 0, deadlines: 0 }
        weeks[weekLabel].shoots++
      }
    })

    // Add deadlines
    deadlines?.forEach(deadline => {
      const date = new Date(deadline.due_date)
      const weekNum = Math.floor((date - now) / (7 * 24 * 60 * 60 * 1000))
      if (weekNum >= 0 && weekNum < 4) {
        const weekLabel = weekNum === 0 ? 'This Week' : `Week +${weekNum}`
        weeks[weekLabel] = weeks[weekLabel] || { shoots: 0, deadlines: 0 }
        weeks[weekLabel].deadlines++
      }
    })

    return Object.entries(weeks).map(([week, data]) => ({
      week,
      ...data
    }))
  }

  const COLORS = [
    '#60BBE9', // accent
    '#4ecca3', // success
    '#ffc107', // warning
    '#dc3545', // danger
    '#ff4757', // critical
    '#a8c5da', // text-dim
    '#09243F', // bg-medium
    '#0a1628'  // bg-dark
  ]

  const renderProjectChart = () => {
    const data = projectData()

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(96, 187, 233, 0.2)" />
          <XAxis
            dataKey="name"
            stroke="#a8c5da"
            angle={-45}
            textAnchor="end"
            height={100}
          />
          <YAxis stroke="#a8c5da" />
          <Tooltip
            contentStyle={{
              background: 'rgba(9, 36, 63, 0.95)',
              border: '1px solid rgba(96, 187, 233, 0.3)',
              borderRadius: '8px',
              color: '#e0e6ed'
            }}
          />
          <Bar dataKey="value" name="At-Risk Tasks" fill="#60BBE9" />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  const renderTeamChart = () => {
    const data = teamData()

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(96, 187, 233, 0.2)" />
          <XAxis dataKey="name" stroke="#a8c5da" />
          <YAxis stroke="#a8c5da" />
          <Tooltip
            contentStyle={{
              background: 'rgba(9, 36, 63, 0.95)',
              border: '1px solid rgba(96, 187, 233, 0.3)',
              borderRadius: '8px',
              color: '#e0e6ed'
            }}
          />
          <Legend />
          <Bar dataKey="current" name="Current Hours" fill="#60BBE9" />
          <Bar dataKey="max" name="Max Capacity" fill="#4ecca3" />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  const renderTimelineChart = () => {
    const data = timelineData()

    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(96, 187, 233, 0.2)" />
          <XAxis dataKey="week" stroke="#a8c5da" />
          <YAxis stroke="#a8c5da" />
          <Tooltip
            contentStyle={{
              background: 'rgba(9, 36, 63, 0.95)',
              border: '1px solid rgba(96, 187, 233, 0.3)',
              borderRadius: '8px',
              color: '#e0e6ed'
            }}
          />
          <Legend />
          <Bar dataKey="shoots" name="Shoots" fill="#60BBE9" stackId="a" />
          <Bar dataKey="deadlines" name="Deadlines" fill="#ffc107" stackId="a" />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  return (
    <div className="card project-insights">
      <h2>📊 Interactive Analytics</h2>

      <div className="chart-selector">
        <button
          className={activeChart === 'projects' ? 'active' : ''}
          onClick={() => setActiveChart('projects')}
        >
          📁 At-Risk by Project
        </button>
        <button
          className={activeChart === 'team' ? 'active' : ''}
          onClick={() => setActiveChart('team')}
        >
          👥 Team Workload
        </button>
        <button
          className={activeChart === 'timeline' ? 'active' : ''}
          onClick={() => setActiveChart('timeline')}
        >
          📅 4-Week Timeline
        </button>
      </div>

      <div className="chart-container">
        {activeChart === 'projects' && renderProjectChart()}
        {activeChart === 'team' && renderTeamChart()}
        {activeChart === 'timeline' && renderTimelineChart()}
      </div>
    </div>
  )
}

export default ProjectInsights
