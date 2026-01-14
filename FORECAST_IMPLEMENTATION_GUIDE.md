# Forecast Component - Implementation Guide

## Overview

The Forecast component is **already fully integrated** with Grok AI scoring. It works exactly like your main video scoring system but for pipeline/forecasted projects.

---

## How It Works

### 1. **Automatic Grok Scoring**

When you add a task to the Perimeter Studio Forecast project in Asana, the system automatically:

- ✅ Queries the Forecast project every 15 minutes (via cron)
- ✅ Sends task details to Grok AI for analysis
- ✅ Receives priority, complexity, category, and B-roll requirements
- ✅ Calculates capacity allocation percentage
- ✅ Updates the task's "% Allocation" custom field
- ✅ Includes forecast data in capacity heatmaps

**No manual scoring required** - Grok does it all!

### 2. **What Grok Analyzes**

Grok reads the task's:
- **Name**: Video title
- **Notes**: Full project description and form details
- **Type**: Custom field value (if set)
- **Start Date**: Estimated start date
- **Due Date**: Estimated completion date

### 3. **What Grok Returns**

```json
{
  "priority_score": 8,
  "complexity": 7,
  "mapped_category": "Communications",
  "mapped_type": "Enriching",
  "broll_required": true,
  "manipulation_check": "No issues",
  "reasoning": "3-minute seasonal video, church-wide audience..."
}
```

### 4. **Capacity Calculation**

Based on Grok's scores, the system calculates % allocation:

**Formula:**
- Base = (Complexity × 3.5) × Phase_Multiplier
- Priority_Factor = 0.5 + (Priority / 24)
- Allocation = (Base × Priority_Factor) / Duration_in_Weeks
- If B-roll required: applies 1.5x multiplier

**Example:**
- Complexity: 7, Priority: 8, Duration: 2 weeks
- Base = (7 × 3.5) × 1.0 = 24.5
- Priority_Factor = 0.5 + (8 / 24) = 0.833
- Allocation = (24.5 × 0.833) / 2 = **10.2% per week**

---

## Workflow: Adding Forecast Tasks

### Option A: Manual Entry (Quick)

1. **Create task** in Asana under "Perimeter Studio Forecast" project
2. **Set the name**: "2026 Holy Week Campaign Video"
3. **Add description** in Notes field:
   ```
   Purpose: Enriching - Seasonal invitation to Holy Week services
   Audience: Church-wide
   Scope: Seasonal (3-6 months relevance)
   Duration: 3 minutes
   Requirements: Interview/testimonies, B-roll footage needed
   Additional Context: Need to capture congregation members sharing
   about the meaning of Easter. Will require multiple filming sessions.
   ```
4. **Set Type** custom field: "Enriching" (if available)
5. **Set dates**: Start: March 1, 2026 | Due: April 5, 2026
6. **Save task**
7. **Wait ~15 minutes** - Grok will score it automatically
8. **Check "% Allocation" field** - It will be populated with the AI-calculated value

### Option B: Form Integration (Recommended)

1. **Create intake form** (Google Forms, Typeform, Asana Forms, etc.)
2. **Use questions from** `FORECAST_INTAKE_FORM.md`
3. **Set up Zapier/Make integration** to create Asana tasks automatically
4. **Map form responses** to task notes field (formatted for Grok)
5. **Grok scores automatically** when task is created

**Sample Notes Format for Form Integration:**
```
Content Summary and Form Details:
Video Title: [Form Response]
Purpose: [Form Response]
Audience: [Form Response]
Scope: [Form Response]
Estimated Duration: [Form Response]
Production Requirements: [Form Response]
B-roll Required: [Form Response]
Timeline: Start [Date] | Due [Date]
Ministry: [Form Response]
Key People: [Form Response]
Additional Context: [Form Response]
```

---

## Key Questions for Accurate Scoring

### Critical Questions (Required):

1. **Estimated Video Duration** - PRIMARY complexity driver
   - "How long will the final video be?" (1 min, 2-4 min, 8-15 min, etc.)

2. **Purpose/Type** - Determines category and priority
   - "Is this Equipping, Enriching, Ministry Support, or Partner Support?"

3. **Audience** - Affects priority scoring
   - "Who is this for? Church-wide, Community, People Groups, or Ministry Groups?"

4. **Scope/Longevity** - Affects priority scoring
   - "Is this Evergreen, Seasonal, Event-Driven, or Short-Term?"

5. **B-roll Requirements** - Affects complexity multiplier
   - "Will this require capturing B-roll footage?"

6. **Estimated Timeline** - Affects allocation calculation
   - "When should we start?" and "When is it due?"

### Important Questions (Helpful):

7. **Production Elements** - Informs complexity
   - "Interviews? Graphics? Motion graphics? Multiple locations?"

8. **Key People** - Affects priority (Jeff Norris content = highest)
   - "Who needs to be featured?"

9. **Related Ministry** - Helps categorization
   - "Which ministry is this for?"

### Optional Questions:

10. **Confidence Level** - For planning purposes
    - "How likely is this project to move forward?"

---

## Monitoring Forecast Capacity

### View Forecast Heatmap

Once forecast tasks have dates and allocations, the system generates:

**`Reports/Forecast_heatmap_weighted.png`**
- Shows projected capacity utilization over next 6 months
- Color-coded by workload intensity
- Helps identify future capacity bottlenecks

**`Reports/Combined_heatmap_weighted.png`**
- Shows ALL phases including Forecast
- See complete picture: current + pipeline work
- Make informed decisions about capacity

### Variance Tracking

Forecast tasks are included in:
- `weighted_allocation_report.csv` - Current capacity snapshot
- `variance_tracking_history.csv` - Daily capacity trends

---

## Transitioning from Forecast to Production

When a forecast project is approved and ready to start:

1. **Move the task** from "Forecast" project to "Preproduction" project
2. **Update dates** if needed (now that you have actual schedule)
3. **Grok re-scores** automatically with Preproduction phase multiplier
4. **Task appears in** Preproduction heatmap
5. **Forecast heatmap** no longer shows it

**Capacity seamlessly transitions** from forecast to active work!

---

## Benefits of Forecast Tracking

### 1. **Proactive Capacity Planning**
- See what's coming 3-6 months out
- Identify conflicts before they happen
- Balance current and future workload

### 2. **Informed Decision Making**
- "Can we take on this project in Q2?"
- "Do we have capacity for this campaign?"
- "Should we hire contractors for peak season?"

### 3. **Strategic Resource Allocation**
- Plan hiring/contractor needs in advance
- Schedule major projects during low-capacity periods
- Avoid overcommitting the team

### 4. **Stakeholder Communication**
- Show leadership what's in the pipeline
- Set realistic expectations with ministry partners
- Justify resource requests with data

---

## Troubleshooting

### "My forecast task doesn't have an allocation percentage"

**Possible causes:**
1. Task was just created - wait ~15 minutes for next cron run
2. Task notes don't have enough detail for Grok to analyze
3. Task doesn't have start/due dates
4. Task is marked as completed

**Fix:** Add more detail to notes, set dates, ensure task is incomplete

### "The allocation seems too high/low"

**Possible causes:**
1. Video duration wasn't specified or is inaccurate
2. Complexity factors not clearly described
3. B-roll requirement not mentioned

**Fix:** Update task notes with accurate duration and requirements, wait for next cron run

### "Forecast heatmap isn't generating"

**Possible cause:** No forecast tasks have dates in the 12-month heatmap window

**Fix:** Ensure forecast tasks have start/due dates within next 6 months

---

## Example Forecast Tasks

### Example 1: High Priority, High Complexity

**Name:** "Digging Deeper Series - Discipleship in the Digital Age"
**Notes:**
```
Purpose: Equipping - Teaching series for congregation
Audience: Church-wide
Scope: Evergreen - Long-term website content
Estimated Duration: 8-10 minutes per episode, 4 episodes total
Production Requirements:
- Interviews with Jeff Norris (Senior Pastor)
- B-roll footage of church activities and digital interactions
- Motion graphics for key concepts
- Multiple filming sessions
B-roll Required: Yes
Timeline: Start January 2026, First episode due February 2026
Ministry: Spiritual Formation / Teaching
Additional Context: Strategic priority for 2026 discipleship initiatives
```

**Expected Grok Output:**
- Priority: 10-11 (Jeff Norris, church-wide, evergreen, equipping)
- Complexity: 9-10 (8-10 min duration, multiple episodes, motion graphics, B-roll)
- Category: Spiritual Formation or Pastoral/Strategic
- B-roll: Yes (1.5x multiplier)
- Allocation: ~18-25% per week (per episode)

---

### Example 2: Medium Priority, Medium Complexity

**Name:** "Summer Kids Camp Promotional Video"
**Notes:**
```
Purpose: Ministry Support - Event promotion for Camp All-American
Audience: People Groups (families with children)
Scope: Event-Driven (relevant for 2-3 months)
Estimated Duration: 2-3 minutes
Production Requirements:
- Testimonies from campers/parents
- B-roll of camp activities (if available from previous years)
- Upbeat music and text overlays
B-roll Required: No (using archive footage)
Timeline: Start April 2026, Due May 15, 2026
Ministry: Children's Ministry - Camp All-American
Additional Context: Annual camp promotion, similar to previous years
```

**Expected Grok Output:**
- Priority: 5-6 (people groups, event-driven, ministry support)
- Complexity: 5-6 (2-3 min, testimonies, basic graphics)
- Category: Communications
- B-roll: No
- Allocation: ~6-9% per week

---

### Example 3: Low Priority, Low Complexity

**Name:** "Global Partners Update - Honduras Mission Trip Recap"
**Notes:**
```
Purpose: Partner Support - Sharing global partnership update
Audience: Ministry Groups (missions-focused members)
Scope: Short-Term (one-time update)
Estimated Duration: 90 seconds
Production Requirements:
- Single spokesperson talking head
- Simple text overlays with location/stats
- Background music
B-roll Required: No
Timeline: Start March 2026, Due March 20, 2026
Ministry: Global Partnerships
Additional Context: Quick update for missions-focused congregation
```

**Expected Grok Output:**
- Priority: 3-4 (ministry groups, short-term, partner support)
- Complexity: 3-4 (90 sec, simple talking head, basic graphics)
- Category: Partners
- B-roll: No
- Allocation: ~3-5% per week

---

## Summary

✅ **Forecast component is live and integrated with Grok AI**
✅ **Automatic scoring - no manual calculation needed**
✅ **Use intake form questions to gather right information**
✅ **Add tasks to Asana Forecast project with detailed notes**
✅ **System handles scoring, allocation, and capacity tracking**
✅ **View forecast capacity in heatmaps and reports**

**Next Steps:**
1. Create intake form using `FORECAST_INTAKE_FORM.md` questions
2. Set up form-to-Asana integration (optional but recommended)
3. Start adding forecast tasks to Asana
4. Monitor `Reports/Forecast_heatmap_weighted.png`
5. Use data for proactive capacity planning
