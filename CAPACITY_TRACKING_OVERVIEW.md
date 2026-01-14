# Perimeter Studio Capacity Tracking System - Complete Overview

## System Components

The capacity tracking system consists of five integrated components working together to provide comprehensive visibility into video production workload:

1. **Grok AI Scoring** - Automatic priority and complexity analysis
2. **Weighted Capacity Tracking** - Real-time workload allocation
3. **Forecast Planning** - Pipeline visibility for future projects
4. **Visual Heatmaps** - Brand-styled capacity calendars
5. **Delivery Performance** - Historical accuracy and on-time metrics

---

## 1. Grok AI Scoring

**What it does:**
- Analyzes task descriptions automatically
- Assigns priority scores (1-12)
- Calculates complexity scores (1-12)
- Maps to categories (Spiritual Formation, Communications, etc.)
- Determines B-roll requirements
- Calculates % allocation based on all factors

**Key Benefits:**
- No manual scoring required
- Consistent prioritization across all tasks
- Considers video duration, audience, scope, and production requirements
- Updates every 15 minutes via cron

**How it works:**
```
Task Description → Grok AI → Priority + Complexity + Category → Allocation %
```

**Example:**
```
Task: "3-minute Holy Week promotional video with testimonies"
Grok Output:
  • Priority: 8 (seasonal, church-wide, enriching)
  • Complexity: 7 (3 min duration, testimonies, B-roll)
  • Category: Communications
  • B-roll Required: Yes (1.5x multiplier)
  • Allocation: ~10.2% per week
```

---

## 2. Weighted Capacity Tracking

**What it does:**
- Tracks all active tasks across 4 projects (Preproduction, Production, Post Production, Forecast)
- Calculates total capacity allocation by category
- Monitors team member capacity (Zach 50%, Nick 100%, Adriel 100%, John 30%)
- Generates alerts when capacity exceeds safe thresholds
- Compares actual allocation vs. target allocation by category

**Key Reports:**
- **`weighted_allocation_report.csv`** - Current snapshot of all active tasks and allocations
- **`variance_tracking_history.csv`** - Daily historical tracking of category allocations

**Target Allocations:**
- Spiritual Formation: 25%
- Communications: 30%
- Creative Resources: 15%
- Pastoral/Strategic: 20%
- Partners: 5%
- **Total Max: 100%** (distributed across team)

**Current Status** (as of last run):
```
Category                Actual    Target   Variance
Spiritual Formation     17.7%     25.0%    -7.3%
Communications          31.4%     30.0%    +1.4%
Creative Resources       6.2%     15.0%    -8.8%
Pastoral/Strategic      41.8%     20.0%   +21.8% ⚠️
Partners                 2.9%      5.0%    -2.1%
```

---

## 3. Forecast Planning (Pipeline Visibility)

**What it does:**
- Tracks pipeline/future projects before they're formally submitted
- Uses same Grok AI scoring as active projects
- Includes forecast capacity in Combined heatmap
- Helps identify future capacity bottlenecks 3-6 months out

**Asana Project:** Perimeter Studio Forecast (GID: 1212059678473189)

**How to add forecast tasks:**
1. Create task in "Perimeter Studio Forecast" project
2. Add detailed description (use FORECAST_INTAKE_FORM.md questions)
3. Set estimated start/due dates
4. Grok scores automatically within 15 minutes
5. Task appears in Forecast heatmap

**Key Questions for Accurate Forecasting:**
- Video duration (primary complexity driver)
- Purpose/Type (Equipping, Enriching, Ministry Support, Partner Support)
- Target audience (Church-wide, Community, People Groups, Ministry Groups)
- Scope/Longevity (Evergreen, Seasonal, Event-Driven, Short-Term)
- B-roll requirements (significantly affects capacity)
- Timeline (start and due dates)

**See:** `FORECAST_IMPLEMENTATION_GUIDE.md` for complete details
**See:** `FORECAST_INTAKE_FORM.md` for intake form questions

---

## 4. Visual Heatmaps (Brand-Styled)

**What it does:**
- Generates capacity heatmaps showing workload distribution over 12 months
- Color-coded by intensity (green = low, yellow = medium, red = high)
- Shows 2 months back + 10 months forward
- Applies Perimeter Church brand styling (Navy #09243F, Blue #60BBE9)
- Updates every 15 minutes

**Generated Heatmaps:**
1. **`Pre_heatmap_weighted.png`** - Preproduction capacity
2. **`Production_heatmap_weighted.png`** - Production capacity
3. **`Post_heatmap_weighted.png`** - Post Production capacity
4. **`Forecast_heatmap_weighted.png`** - Pipeline/Forecast capacity
5. **`Combined_heatmap_weighted.png`** - All phases combined

**Visual Features:**
- Current month highlighted in brand blue
- Today's date shown in bold
- Peak capacity metrics displayed
- Professional spacing and layout
- Perimeter Church color palette throughout

**See:** `BRAND_STYLING_SUMMARY.md` for complete styling details

---

## 5. Delivery Performance Tracking

**What it does:**
- Tracks all completed tasks from last 30 days
- Monitors on-time delivery rates
- Calculates allocation accuracy (estimated vs. actual)
- Identifies patterns in over/underestimation
- Generates performance summaries by category and phase

**Key Metrics Tracked:**

**Completion Metrics:**
- On-time delivery rate
- Average days variance (early/late)
- Performance by category
- Performance by project phase

**Allocation Accuracy Metrics:**
- Estimated vs. actual allocation
- Allocation variance percentage
- Accuracy rating (Accurate, Moderate, Significant Variance)
- Average allocation variance

**Generated Reports:**
1. **`delivery_performance_log.csv`** - Detailed log of all completed tasks
2. **`delivery_performance_summary.csv`** - Summary with overall metrics and breakdowns

**Current Status** (last 30 days):
```
Total Completed Tasks: 11
On-Time Deliveries: 2
Late Deliveries: 0
On-Time Delivery Rate: 18.2%
Average Days Variance: -1.0 days (early)

Allocation Accuracy: No data yet (setup required)
```

**See:** `DELIVERY_PERFORMANCE_GUIDE.md` for complete details and setup instructions

---

## System Workflow

### Daily Automated Process (Every 15 Minutes)

1. **Query Asana** for all active and recently completed tasks
2. **Send to Grok AI** for scoring (new/modified tasks only)
3. **Calculate capacity** allocation for each task
4. **Update Asana** with allocation percentages
5. **Generate reports** (allocation, variance, delivery performance)
6. **Generate heatmaps** (5 heatmaps with brand styling)
7. **Send alerts** if capacity thresholds exceeded
8. **Log everything** for audit trail

**Cron Schedule:** `*/15 * * * *` (every 15 minutes)

---

## Key Files and Locations

### Scripts
- **`video_scorer.py`** - Main capacity tracking script (1,200+ lines)
- **`capacity_alerts.py`** - Alert system (Slack/email/file)

### Reports (Generated Every 15 Minutes)
- **`Reports/weighted_allocation_report.csv`** - Current capacity snapshot
- **`Reports/variance_tracking_history.csv`** - Historical category tracking
- **`Reports/delivery_performance_log.csv`** - Completed task details
- **`Reports/delivery_performance_summary.csv`** - Performance summary
- **`Reports/Pre_heatmap_weighted.png`** - Preproduction heatmap
- **`Reports/Production_heatmap_weighted.png`** - Production heatmap
- **`Reports/Post_heatmap_weighted.png`** - Post Production heatmap
- **`Reports/Forecast_heatmap_weighted.png`** - Forecast heatmap
- **`Reports/Combined_heatmap_weighted.png`** - Combined heatmap

### Documentation
- **`CAPACITY_TRACKING_OVERVIEW.md`** - This file (system overview)
- **`FORECAST_IMPLEMENTATION_GUIDE.md`** - Forecast component guide
- **`FORECAST_INTAKE_FORM.md`** - Questions for forecast requests
- **`DELIVERY_PERFORMANCE_GUIDE.md`** - Performance tracking guide
- **`BRAND_STYLING_SUMMARY.md`** - Brand styling details

### Logs
- **`video_scorer.log`** - Main execution log
- **`manipulation_audit.log`** - Security/manipulation detection log

---

## Asana Configuration

### Projects Tracked
1. **Preproduction** (GID: 1208336083003480)
2. **Production** (GID: 1209597979075357)
3. **Post Production** (GID: 1209581743268502)
4. **Forecast** (GID: 1212059678473189)

### Custom Fields Required
- **% Allocation** (GID: 1208923995383367) - Auto-populated by system ✅
- **Category** - Enum field (Spiritual Formation, Communications, etc.) ✅
- **Actual Allocation** - Number field (optional, for performance tracking) ⏳ Not yet set up

### Task Fields Used
- Task name
- Task notes/description
- Start date (`start_on`)
- Due date (`due_on`)
- Completed status
- Completed date (`completed_at`)
- Custom fields (Category, % Allocation, Actual Allocation)

---

## Team Capacity Configuration

**Total Available Capacity: 300% weekly**

| Team Member    | Capacity | Projects                                      |
|----------------|----------|-----------------------------------------------|
| Zach Welliver  | 50%      | Preproduction                                 |
| Nick Clark     | 100%     | Production                                    |
| Adriel Abella  | 100%     | Post Production                               |
| John Meyer     | 30%      | Preproduction, Production, Post Production    |

**Daily Max Capacity:** 60% per day (300% / 5 days)

---

## Grok AI Scoring Parameters

### Phase Multipliers
- Preproduction: 0.8
- Production: 1.0
- Post Production: 0.6
- Forecast: 1.0

### Base Calculation
```
Base = (Complexity × 3.5) × Phase_Multiplier
Priority_Factor = 0.5 + (Priority / 24)
Allocation = (Base × Priority_Factor) / Duration_in_Weeks
If B-roll Required: Allocation × 1.5
```

### Priority Score Factors (0-12 scale)
- **Audience** (Church-wide = highest, Ministry Groups = lower)
- **Content Scope** (Evergreen = highest, Short-term = lower)
- **Content Type** (Equipping/Enriching = higher, Partner Support = lower)
- **Key People** (Jeff Norris = +2 boost)

### Complexity Score Factors (0-12 scale)
- **Video Duration** (PRIMARY driver: <1 min = 2, 15+ min = 11)
- **Production Requirements** (B-roll, motion graphics, multiple locations)
- **Number of Interviews/Testimonies**
- **Editing Complexity**

---

## Usage Examples

### Example 1: Adding a New Project to Preproduction

**Action:** Create task "Easter Campaign Video - Promotional"

**Task Description:**
```
3-minute promotional video for Easter services
Audience: Church-wide
Purpose: Enriching - Seasonal invitation
Requirements:
- 2-3 testimonies from congregation members
- B-roll of church campus and activities
- Motion graphics for event details
- Upbeat music

Timeline: Start March 1, Due April 1 (4 weeks)
```

**System Response (within 15 minutes):**
- Grok scores: Priority 9, Complexity 7
- Category: Communications
- B-roll: Yes
- Allocation: ~12.3% per week
- Appears in Preproduction heatmap
- Appears in Combined heatmap

---

### Example 2: Reviewing Capacity for Next Quarter

**Action:** Open `Combined_heatmap_weighted.png`

**What you see:**
- January: Heavy workload (orange/red)
- February: Moderate workload (yellow)
- March: Low workload (green)

**Decision:** "We can take on the new teaching series project in March without overloading the team"

---

### Example 3: Checking Delivery Performance

**Action:** Open `delivery_performance_summary.csv`

**What you see:**
```
Total Completed Tasks: 11
On-Time Delivery Rate: 18.2%
Average Days Variance: -1.0 days

By Category:
  Communications: 10.0% on-time
  Partners: 100% on-time
```

**Insight:** "Most tasks don't have due dates set. Need to improve due date discipline."

**Action:** Set due dates for all new tasks going forward

---

### Example 4: Monitoring Category Balance

**Action:** Open `variance_tracking_history.csv`

**What you see:**
```
Date,Category,Actual %,Target %,Variance
2025-11-25,Pastoral/Strategic,41.8,20.0,+21.8
```

**Insight:** "We're spending 2x target capacity on Pastoral/Strategic content"

**Possible Actions:**
- Review if this is intentional (special season)
- Consider if other categories are being neglected
- Discuss with leadership if target should be adjusted
- Look for ways to reduce Pastoral/Strategic scope

---

## Alert System

**Capacity Alerts Trigger When:**
- Daily capacity > 60% (MAX_CAPACITY / 5)
- Any category exceeds safe threshold
- Multiple concurrent high-priority tasks

**Alert Channels:**
- **File:** `capacity_alerts.log`
- **Slack:** (if configured)
- **Email:** (if configured)

**Current Status:** File-based alerts active ✅

---

## Monthly Review Checklist

### Capacity Balance Review
- [ ] Review `variance_tracking_history.csv` for trends
- [ ] Compare actual vs. target by category
- [ ] Identify over/underallocated categories
- [ ] Discuss with team if patterns need addressing

### Delivery Performance Review
- [ ] Review `delivery_performance_summary.csv`
- [ ] Check on-time delivery rate trend
- [ ] Analyze allocation accuracy (when available)
- [ ] Identify categories with consistent variance

### Forecast Planning Review
- [ ] Review `Forecast_heatmap_weighted.png`
- [ ] Identify potential capacity bottlenecks 3-6 months out
- [ ] Balance pipeline with current capacity
- [ ] Update forecast tasks with latest information

### Scoring Accuracy Review
- [ ] Review completed tasks with large allocation variance
- [ ] Adjust Grok scoring parameters if needed
- [ ] Update base multiplier if consistent over/underestimation
- [ ] Refine intake forms to capture missing complexity factors

---

## Next Steps

### Immediate (Already Working)
✅ Grok AI scoring for all 4 projects
✅ Capacity tracking with weighted allocations
✅ Forecast pipeline visibility
✅ Brand-styled heatmaps
✅ Delivery completion tracking

### To Enable Full Performance Tracking
⏳ Create "Actual Allocation" custom field in Asana
⏳ Update `ACTUAL_ALLOCATION_FIELD_GID` in video_scorer.py
⏳ Choose time tracking method (manual, Toggl, Harvest, etc.)
⏳ Populate actual allocation data for completed tasks
⏳ Review allocation accuracy in monthly reports

### Future Enhancements (Optional)
- Add Perimeter logo to heatmaps
- Install custom brand fonts (Freight DispPro, Sweet Sans Pro)
- PowerPoint export integration
- Slack/email alert configuration
- Predictive capacity modeling

---

## Troubleshooting

**Issue:** Script isn't running automatically
**Check:** `crontab -l` to verify cron job exists
**Fix:** Re-add cron job if missing

**Issue:** Allocation percentages aren't updating
**Check:** `video_scorer.log` for errors
**Common causes:** API rate limits, network issues, malformed task descriptions

**Issue:** Heatmaps look wrong
**Check:** Task start/due dates in Asana
**Common causes:** Missing dates, dates far in past/future

**Issue:** Forecast tasks not appearing
**Check:** Tasks are in correct project (GID 1212059678473189)
**Check:** Tasks have dates within heatmap window (last 2 months + next 10 months)

---

## System Requirements

- Python 3.x
- Virtual environment (`venv/`)
- Required packages: `requests`, `pandas`, `numpy`, `matplotlib`, `aiohttp`, `tenacity`, `python-dotenv`
- Asana API token (in `.env` file)
- Grok API key (in `.env` file)
- Cron access (macOS/Linux)

---

## Contact & Support

**System Location:** `/Users/comstudio/Scripts/StudioProcesses/`

**For Questions:**
- Grok AI scoring parameters
- Capacity allocation calculations
- Forecast intake forms
- Performance tracking setup
- Heatmap customization
- Report interpretation

Contact the Video Production Team or system administrator.

---

## Summary

The Perimeter Studio Capacity Tracking System provides:

🎯 **Automated Scoring** - Grok AI analyzes every task
📊 **Real-Time Tracking** - Updates every 15 minutes
🔮 **Pipeline Visibility** - See future workload 3-6 months out
🎨 **Brand-Styled Reports** - Professional heatmaps and dashboards
📈 **Performance Insights** - Historical accuracy and trends

**Result:** Data-driven capacity management for strategic video production planning.
