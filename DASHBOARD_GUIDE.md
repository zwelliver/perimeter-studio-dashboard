# Capacity Dashboard - Usage Guide

## Overview

The Perimeter Studio Capacity Dashboard provides a unified, at-a-glance view of all capacity tracking metrics in both interactive HTML and static PNG formats.

**Location:** `Reports/capacity_dashboard.*`

**Updates:** Automatically every 15 minutes via cron

---

## Dashboard Formats

### 1. HTML Dashboard (Interactive)
**File:** `Reports/capacity_dashboard.html`

**How to Open:**
- Double-click the file to open in your default browser
- OR right-click → Open With → Chrome/Firefox/Safari
- OR drag and drop into browser window

**Features:**
- ✅ Interactive charts (hover for details)
- ✅ Real-time data from latest reports
- ✅ Perimeter Church brand styling
- ✅ Clean, professional layout
- ✅ Print-friendly (Cmd+P / Ctrl+P)
- ✅ Mobile-responsive

**Best For:**
- Daily capacity reviews
- Team meetings
- Leadership presentations
- Detailed analysis

---

### 2. PNG Dashboard (Static Image)
**File:** `Reports/capacity_dashboard.png`

**How to View:**
- Double-click to open in Preview/Photos
- Drag into Slack channels for sharing
- Attach to emails
- Include in presentations

**Features:**
- ✅ High-resolution (150 DPI)
- ✅ Perimeter Church brand styling
- ✅ Quick visual reference
- ✅ Easy to share

**Best For:**
- Quick glances
- Slack/email sharing
- Screenshot/screencasting
- Archiving snapshots

---

## Dashboard Sections

### 1. Header
- **Dashboard Title** - Perimeter Studio branding
- **Last Updated** - Timestamp showing when data was last refreshed
- **Subtitle** - Context about what's being tracked

### 2. Quick Stats (Top Right)
- **Active Tasks** - Total number of active tasks across all projects
- **Completed (30d)** - Tasks completed in last 30 days
- **On-Time Rate** - Percentage of tasks delivered on time

**Color Indicators:**
- 🟢 Green: >= 80% (Good)
- 🟡 Yellow: 60-79% (Warning)
- 🔴 Red: < 60% (Needs attention)

### 3. Category Allocation Chart (Top Left)
**Bar chart showing actual vs. target allocation by category**

- **Blue bars** - Actual allocation percentage
- **Gray dashed bars** - Target allocation percentage

**What to look for:**
- Bars significantly higher than target = overallocated category
- Bars significantly lower than target = underutilized category
- Bars aligned with targets = balanced capacity

### 4. Team Capacity (Middle Left)
**Individual capacity status for each team member**

Shows:
- Team member name
- Current utilization vs. maximum capacity
- Progress bar visualization

**Colors:**
- 🔵 Blue: Within capacity (OK)
- 🔴 Red: Over capacity (alert)

**Team Members:**
- Zach Welliver: 50% max (Preproduction)
- Nick Clark: 100% max (Production)
- Adriel Abella: 100% max (Post Production)
- John Meyer: 30% max (All phases)

### 5. Category Variance (Middle Right)
**Text-based breakdown of variance from targets**

**Symbols:**
- ✓ (checkmark) - Within 5% of target (good)
- ⚠ (warning) - 5-10% variance (monitor)
- ✗ (cross) - Over 10% variance (needs action)

Shows positive (+) or negative (-) variance for each category.

### 6. Delivery Performance (Bottom Right)
**Key delivery metrics from last 30 days**

- **On-Time Rate** - % of tasks completed on/before due date
- **Avg Days Variance** - Average days early (-) or late (+)
- **Allocation Accuracy** - % of tasks estimated within 10% of actual
- **Tasks w/ Actual Data** - Number of tasks with actual allocation tracked

---

## Interpreting the Dashboard

### Scenario 1: Healthy Capacity
```
Quick Stats:
  Active Tasks: 28
  Completed (30d): 15
  On-Time Rate: 85% (Green)

Category Variance:
  ✓ All categories within 5% of target

Team Capacity:
  All team members under 100% utilization
```

**Meaning:** System is running smoothly. Good balance across categories. Team has capacity for new projects.

**Action:** Maintain current trajectory. Consider taking on additional forecast projects.

---

### Scenario 2: Category Overallocation
```
Category Variance:
  ✗ Pastoral/Strategic: +21.8% (over target)
  ✓ Communications: +1.4%
  ✗ Creative Resources: -8.8% (under target)
```

**Meaning:** Too much capacity allocated to Pastoral/Strategic content. Creative Resources underutilized.

**Action:**
1. Review if Pastoral/Strategic overallocation is intentional (special season)
2. Consider if target needs adjustment
3. Look for opportunities to shift work to Creative Resources
4. Discuss with leadership if sustained

---

### Scenario 3: Delivery Issues
```
Delivery Performance:
  On-Time Rate: 45% (Red)
  Avg Days Variance: +7.2 days (late)
```

**Meaning:** Many projects finishing late. Consistent delay of about a week.

**Action:**
1. Review Grok AI scoring parameters - may be underestimating complexity
2. Check for systemic blockers (approvals, resources, dependencies)
3. Consider adding buffer time to due dates
4. Reduce concurrent active tasks

---

### Scenario 4: Estimation Issues
```
Delivery Performance:
  Allocation Accuracy: 35%
  Avg Allocation Variance: +8.5%
```

**Meaning:** Consistently underestimating effort required. Tasks taking ~50% longer than estimated.

**Action:**
1. Increase base multiplier in Grok scoring (currently 3.5, try 4.0)
2. Review which categories are consistently underestimated
3. Add more detail to task descriptions for better Grok analysis
4. Check if B-roll multiplier (1.5x) is sufficient

---

## Dashboard Refresh Schedule

**Automatic Updates:** Every 15 minutes via cron

**Manual Refresh:**
```bash
cd ~/Scripts/StudioProcesses
source venv/bin/activate
python generate_dashboard.py
```

**Or run full capacity tracking update:**
```bash
python video_scorer.py
```

---

## Sharing the Dashboard

### Share HTML Version
**For interactive viewing:**

1. **Email:**
   - Attach `capacity_dashboard.html`
   - Recipients can open in any browser
   - No special software required

2. **Shared Drive:**
   - Copy to Google Drive / Dropbox / OneDrive
   - Share link for always up-to-date view

3. **Local Network:**
   - Place on shared network drive
   - Team can bookmark location

### Share PNG Version
**For quick references:**

1. **Slack:**
   - Drag `capacity_dashboard.png` into channel
   - Add context: "Latest capacity snapshot"

2. **Email:**
   - Attach PNG for quick viewing
   - No need to open attachments

3. **Presentations:**
   - Insert PNG into PowerPoint/Keynote
   - Use as discussion starting point

---

## Printing the Dashboard

### Print HTML Version (Recommended)
1. Open `capacity_dashboard.html` in browser
2. File → Print (or Cmd+P / Ctrl+P)
3. Select "Save as PDF" or print to paper
4. Optimized for 8.5" x 11" landscape

**Features:**
- Print-optimized CSS
- Clean borders
- No page breaks within cards
- Professional appearance

### Print PNG Version
1. Open `capacity_dashboard.png`
2. File → Print
3. Select "Fit to Page"

---

## Dashboard vs. Individual Reports

**When to use the Dashboard:**
- ✅ Daily capacity check-ins
- ✅ Team standup meetings
- ✅ Quick status overview
- ✅ Leadership updates
- ✅ Identifying trends at a glance

**When to use Individual Reports:**
- ✅ Deep dive into specific categories
- ✅ Historical trend analysis (variance_tracking_history.csv)
- ✅ Task-level details (weighted_allocation_report.csv)
- ✅ Delivery performance deep dive (delivery_performance_log.csv)
- ✅ Audit trail and data export

**Best Practice:** Check dashboard daily, review detailed reports weekly.

---

## Troubleshooting

### Dashboard shows old data
**Cause:** Dashboard not regenerating automatically

**Fix:**
```bash
cd ~/Scripts/StudioProcesses
source venv/bin/activate
python generate_dashboard.py
```

Check cron is running:
```bash
crontab -l | grep video_scorer
```

---

### HTML dashboard won't open
**Cause:** File association issue

**Fix:**
1. Right-click `capacity_dashboard.html`
2. Open With → Chrome (or Firefox/Safari)
3. Set as default for HTML files

---

### PNG looks blurry
**Cause:** Image viewer scaling issue

**Fix:**
1. Open in different app (Preview on Mac, Photos on Windows)
2. Zoom to 100% for native resolution
3. Dashboard is rendered at 150 DPI (high quality)

---

### Charts not showing in HTML
**Cause:** Browser blocking Chart.js CDN

**Fix:**
1. Check internet connection (Chart.js loads from CDN)
2. Try different browser
3. Disable content blockers temporarily

---

## Customization

### Change Dashboard Layout
Edit `generate_dashboard.py` to modify:
- Section arrangement
- Color scheme
- Chart types
- Metrics displayed

### Add Custom Metrics
Modify `generate_dashboard.py` to include:
- Additional CSV data sources
- New calculated metrics
- Custom visualizations

### Adjust Brand Colors
Current colors (in `generate_dashboard.py`):
```python
BRAND_NAVY = '#09243F'
BRAND_BLUE = '#60BBE9'
BRAND_OFF_WHITE = '#f8f9fa'
```

Change these values to adjust branding.

---

## Summary

✅ **Two formats** - HTML (interactive) and PNG (static)
✅ **Auto-updates** - Every 15 minutes via cron
✅ **Branded** - Perimeter Church colors and styling
✅ **Comprehensive** - All key metrics in one view
✅ **Shareable** - Easy to distribute to team/leadership

**Primary Use Case:** Daily capacity monitoring and team communication

**Location:** `Reports/capacity_dashboard.*`

**Open:** Double-click HTML for interactive view, or drag PNG to share quickly

---

## Related Documentation

- **CAPACITY_TRACKING_OVERVIEW.md** - Complete system overview
- **DELIVERY_PERFORMANCE_GUIDE.md** - Delivery metrics explained
- **FORECAST_IMPLEMENTATION_GUIDE.md** - Pipeline visibility guide
- **BRAND_STYLING_SUMMARY.md** - Brand guidelines reference

---

## Contact

For questions about the dashboard or to request additional metrics, contact the Video Production Team.

**Dashboard Generator:** `/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py`
**Main Script:** `/Users/comstudio/Scripts/StudioProcesses/video_scorer.py`
**Cron Schedule:** Every 15 minutes (`*/15 * * * *`)
