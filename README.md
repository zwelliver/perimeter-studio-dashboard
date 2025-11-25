# Perimeter Studio Capacity Dashboard

Interactive capacity tracking dashboard for Perimeter Church video production team.

## Live Dashboard

View the latest capacity dashboard: [capacity_dashboard.html](Reports/capacity_dashboard.html)

**Last Updated:** Auto-updates every 15 minutes

## What This Dashboard Shows

### Quick Stats
- **Active Tasks** - Total active tasks across all production phases
- **Completed (30 days)** - Tasks completed in the last 30 days
- **Avg Days Variance** - Average days early (-) or late (+)

### Delivery Performance
- **On-Time Completion Rate** - Percentage of tasks with due dates completed on-time or early
- **Average Capacity Variance** - How actual allocation compares to estimates
- **Projects Completed (30d)** - Total completions in last 30 days
- **Delayed Due to Capacity** - Tasks late due to capacity overruns

### Team Capacity
Real-time capacity utilization for each team member:
- **Zach Welliver** - 50% max capacity (Preproduction)
- **Nick Clark** - 100% max capacity (Production)
- **Adriel Abella** - 120% max capacity (Post Production)
- **John Meyer** - 30% max capacity (All phases)

### Category Allocation
- Current allocation vs target percentages by content category
- Historical trends over time
- Individual category breakdowns

## Viewing the Dashboard

### Option 1: GitHub Pages (Recommended for Sharing)
Once enabled, access at: `https://[your-username].github.io/[repo-name]/Reports/capacity_dashboard.html`

### Option 2: Download and Open Locally
1. Download `Reports/capacity_dashboard.html`
2. Open in any web browser
3. Works offline (requires internet for Chart.js charts)

### Option 3: Clone Repository
```bash
git clone [repository-url]
cd StudioProcesses
open Reports/capacity_dashboard.html
```

## How It Works

The dashboard is automatically updated every 15 minutes via a cron job that:
1. Fetches active tasks from Asana
2. Calculates capacity metrics using Grok AI scoring
3. Generates the interactive HTML dashboard
4. Commits updates to this repository

## Data Sources

All data is pulled from Asana projects:
- **Preproduction** - Pre-production tasks and planning
- **Production** - Video shooting and production
- **Post Production** - Editing and finalization

## Questions?

Contact the Perimeter Studio Video Production Team for questions about capacity tracking or dashboard metrics.

---

**Generated with Grok AI Capacity Tracking System**
