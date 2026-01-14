# Delivery Performance Tracking - Implementation Guide

## Overview

The delivery performance tracking system monitors two key metrics:

1. **Completion Metrics**: Did projects finish on time when we planned them?
2. **Allocation Accuracy**: How accurate are our capacity estimates vs. reality?

This system automatically tracks all completed tasks from the last 30 days and generates performance reports.

---

## What Gets Tracked

### 1. Completion Metrics

For every completed task, the system tracks:

- **Due Date** - When the task was supposed to be completed
- **Completed Date** - When the task was actually completed
- **Days Variance** - How many days early (-) or late (+)
- **Delivery Status** - Early, On Time, or Late

**Example:**
- Task due: November 24, 2025
- Task completed: November 23, 2025
- Days Variance: -1 (one day early)
- Delivery Status: Early ✅

### 2. Allocation Accuracy Metrics

For tasks with actual time data, the system tracks:

- **Estimated Allocation %** - What Grok AI calculated the task would require
- **Actual Allocation %** - What the task actually consumed (from "Actual Allocation" custom field)
- **Allocation Variance %** - Difference between actual and estimated (positive = over estimate, negative = under estimate)
- **Allocation Accuracy** - Categorized as:
  - **Accurate** - Within 10% of estimate
  - **Moderate** - Within 25% of estimate
  - **Significant Variance** - Over 25% off estimate

**Example:**
- Estimated Allocation: 10%
- Actual Allocation: 12%
- Allocation Variance: +2% (2% over estimate)
- Allocation Accuracy: Accurate (within 10%)

**Example 2:**
- Estimated Allocation: 10%
- Actual Allocation: 15%
- Allocation Variance: +5% (50% over estimate)
- Allocation Accuracy: Significant Variance (over 25%)

---

## Generated Reports

### 1. Delivery Performance Log
**Location**: `Reports/delivery_performance_log.csv`

Detailed log of all completed tasks with columns:
- Task Name
- Project (Preproduction, Production, Post Production, Forecast)
- Category (Spiritual Formation, Communications, etc.)
- Estimated Allocation %
- Actual Allocation % (N/A until actual data is recorded)
- Allocation Variance %
- Allocation Accuracy
- Due Date
- Completed Date
- Days Variance
- Delivery Status

### 2. Delivery Performance Summary
**Location**: `Reports/delivery_performance_summary.csv`

Summary report with sections:

**Overall Metrics:**
- Total Completed Tasks (30 days)
- On-Time Deliveries
- Late Deliveries
- On-Time Delivery Rate %
- Average Days Variance
- Tasks with Actual Allocation Data
- Accurate Estimates (within 10%)
- Allocation Accuracy Rate %
- Average Allocation Variance %

**Allocation Accuracy Breakdown:** (when data available)
- Count of Accurate estimates
- Count of Moderate variance estimates
- Count of Significant variance estimates

**Performance by Category:**
- Total tasks per category
- On-time count per category
- On-time percentage per category

**Performance by Project Phase:**
- Total tasks per phase
- On-time count per phase
- On-time percentage per phase

---

## How to Enable Allocation Accuracy Tracking

Currently, the system tracks completion metrics automatically. To enable allocation accuracy tracking, you need to:

### Step 1: Create "Actual Allocation" Custom Field in Asana

1. Go to any of your projects (Preproduction, Production, Post Production, or Forecast)
2. Click on **Customize** in the top right
3. Add a new **Number** custom field
4. Name it: **"Actual Allocation"** (or "Time Spent %")
5. Format: Number (decimal)
6. Copy the field's GID

### Step 2: Update video_scorer.py

Open `video_scorer.py` and find line 95:

```python
# Custom field GID for Actual Allocation (optional - for tracking actual time spent)
# This field can be populated manually or via time tracking integration
ACTUAL_ALLOCATION_FIELD_GID = None  # Set to actual GID when field is created in Asana
```

Replace `None` with your new custom field GID:

```python
ACTUAL_ALLOCATION_FIELD_GID = "YOUR_FIELD_GID_HERE"
```

### Step 3: Track Actual Time Spent

There are several ways to populate the "Actual Allocation" field:

#### Option A: Manual Entry (Simple)

When you complete a task:
1. Reflect on how much capacity it actually consumed
2. Update the "Actual Allocation" field with the percentage
3. Next cron run will capture the variance

**Example:**
- Task: "Jin and Joanna Park's Story"
- Estimated Allocation: 13%
- You realize it took more time than expected
- Set Actual Allocation: 18%
- System calculates: +5% variance (38% over estimate)

#### Option B: Time Tracking Integration (Recommended)

Use a time tracking tool that integrates with Asana:
- **Toggl** - Track time and sync to Asana custom fields
- **Harvest** - Time tracking with Asana integration
- **Everhour** - Built for Asana time tracking
- **Clockify** - Free time tracking option

Configure your time tracking tool to:
1. Track hours spent on each task
2. Calculate percentage of weekly capacity (based on 40-hour work week)
3. Write the percentage to the "Actual Allocation" custom field
4. System automatically captures variance every 15 minutes

#### Option C: Retrospective Analysis (Periodic)

At the end of each week:
1. Review completed tasks
2. Estimate actual capacity consumed
3. Update "Actual Allocation" field for completed tasks
4. Next cron captures the data

---

## Interpreting the Reports

### Completion Performance

**Good Indicators:**
- ✅ On-time delivery rate > 80%
- ✅ Average days variance near 0 (not consistently early or late)
- ✅ Consistent performance across categories

**Warning Signs:**
- ⚠️ On-time delivery rate < 60%
- ⚠️ Large positive days variance (consistently late)
- ⚠️ Large negative days variance (rushing, dates may be unrealistic)

### Allocation Accuracy

**Good Indicators:**
- ✅ Allocation accuracy rate > 70% (within 10%)
- ✅ Average allocation variance near 0
- ✅ Improving accuracy over time (learning from past projects)

**Warning Signs:**
- ⚠️ Consistently positive variance (underestimating complexity)
- ⚠️ Consistently negative variance (overestimating or padding)
- ⚠️ High variance in specific categories (need better scoring for that type)

### Example Analysis

**Scenario 1: Consistently Late Deliveries**
```
On-Time Delivery Rate: 18.2%
Average Days Variance: +5.3 days
```

**Possible Causes:**
- Due dates are too aggressive
- Tasks are more complex than estimated
- Unexpected blockers or dependencies
- Team capacity is overallocated

**Actions:**
- Review Grok AI scoring parameters
- Adjust phase multipliers to reflect reality
- Add buffer time to due dates
- Reduce concurrent active tasks

---

**Scenario 2: Overestimating Allocation**
```
Allocation Accuracy Rate: 45%
Average Allocation Variance: -3.2%
```

**Possible Causes:**
- Grok AI is padding estimates too much
- Team has become more efficient
- Tasks are simpler than descriptions suggest

**Actions:**
- Review complexity scoring parameters
- Reduce base multiplier (currently 3.5)
- Check if B-roll multiplier (1.5x) is too high
- Analyze which categories are consistently overestimated

---

**Scenario 3: Underestimating Allocation**
```
Allocation Accuracy Rate: 40%
Average Allocation Variance: +5.8%
```

**Possible Causes:**
- Hidden complexity not captured in task descriptions
- Scope creep during execution
- Underestimating specific task types

**Actions:**
- Improve intake form questions to capture complexity
- Increase base multiplier (currently 3.5)
- Review which categories are consistently underestimated
- Add additional scoring factors for common complexity drivers

---

## Automated Tracking

The system runs automatically every 15 minutes via cron:
- Fetches all tasks completed in last 30 days
- Calculates delivery and allocation metrics
- Updates `Reports/delivery_performance_log.csv`
- Updates `Reports/delivery_performance_summary.csv`

**No manual intervention required** - just ensure:
1. Tasks have due dates set
2. Tasks are marked as completed when finished
3. (Optional) "Actual Allocation" field is populated for accuracy tracking

---

## Monthly Review Process

### Recommended Monthly Review

1. **Open both performance reports** at the end of each month
2. **Review overall metrics** - Are we delivering on time? Are estimates accurate?
3. **Identify patterns** - Which categories/phases are struggling?
4. **Adjust scoring parameters** - Based on variance trends
5. **Document learnings** - What changed? What worked?
6. **Share with team** - Celebrate wins, address challenges

### Example Monthly Review Template

**November 2025 Performance Review**

**Delivery Performance:**
- Total tasks completed: 11
- On-time rate: 18.2%
- Average variance: -1.0 days

**Observations:**
- Only 2 tasks had due dates (others showed N/A)
- Team completed work quickly when due dates were set

**Actions:**
- Ensure all tasks have due dates going forward
- Continue monitoring delivery trends

**Allocation Accuracy:**
- Tasks with actual data: 0 (not yet tracking)

**Actions:**
- Set up "Actual Allocation" custom field
- Begin tracking actual time spent on tasks
- Review accuracy in December

---

## Troubleshooting

### "Most tasks show 'N/A' for Days Variance"

**Cause:** Tasks don't have due dates set in Asana

**Fix:** When creating tasks, always set a due date. Grok AI uses start/due dates for allocation calculations, so these should always be present.

---

### "All Actual Allocation fields show 'N/A'"

**Cause:** Either:
1. `ACTUAL_ALLOCATION_FIELD_GID` is not set in video_scorer.py (still `None`)
2. The custom field exists but hasn't been populated with data

**Fix:**
1. Create "Actual Allocation" custom field in Asana
2. Update `ACTUAL_ALLOCATION_FIELD_GID` in video_scorer.py
3. Populate the field for completed tasks (manually or via time tracking)

---

### "Allocation variance seems wrong"

**Cause:** The "Actual Allocation" field value doesn't represent the same scale as estimated allocation

**Fix:** Ensure "Actual Allocation" is entered as a percentage (e.g., 15.5, not 0.155)

---

### "Reports aren't updating"

**Cause:** The cron job may not be running

**Fix:**
```bash
# Check cron status
crontab -l

# Manually run the script
cd ~/Scripts/StudioProcesses
source venv/bin/activate
python video_scorer.py
```

---

## Benefits of Performance Tracking

### 1. **Improve Estimate Accuracy**
- Learn which types of tasks are consistently over/underestimated
- Refine Grok AI scoring parameters based on actual data
- Reduce surprises and better predict capacity needs

### 2. **Optimize Scheduling**
- Identify realistic project timelines
- Avoid overcommitting the team
- Set achievable due dates

### 3. **Data-Driven Decisions**
- "We consistently underestimate testimonies by 40%" → Adjust scoring
- "Communications category is 85% on-time" → Model for other categories
- "Post Production variance is +3 days average" → Add buffer time

### 4. **Team Communication**
- Show leadership concrete performance data
- Justify resource requests with evidence
- Celebrate improvements in accuracy

### 5. **Continuous Improvement**
- Track improvements month-over-month
- Identify training opportunities
- Refine processes based on patterns

---

## Summary

✅ **Completion tracking is live** - Automatically tracking on-time delivery
✅ **Allocation variance infrastructure ready** - Just needs Actual Allocation field
✅ **Reports generate every 15 minutes** - Always up-to-date
✅ **30-day rolling window** - Focuses on recent performance
✅ **Actionable insights** - Identifies patterns and improvement opportunities

**Next Steps:**
1. ✅ Completion tracking is working (18.2% on-time rate currently)
2. ⏳ Set up "Actual Allocation" custom field in Asana
3. ⏳ Update `ACTUAL_ALLOCATION_FIELD_GID` in video_scorer.py
4. ⏳ Begin tracking actual time spent on tasks
5. ⏳ Review monthly reports and adjust scoring parameters

---

## Contact

For questions about delivery performance tracking or to request additional metrics, contact the Video Production Team.

**System Location**: `/Users/comstudio/Scripts/StudioProcesses/video_scorer.py`
**Reports Location**: `/Users/comstudio/Scripts/StudioProcesses/Reports/`
**Cron Schedule**: Every 15 minutes (`*/15 * * * *`)
