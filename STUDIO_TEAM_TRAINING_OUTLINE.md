# Studio Automation System - Team Training Outline

## Presentation Duration: 45-60 minutes

---

## 1. INTRODUCTION & OVERVIEW (5 minutes)

### What We Built
- **Complete automation system** for studio production workflow
- **AI-powered** task management, capacity planning, and content generation
- **Real-time dashboards** showing what's happening across all projects
- **Zero manual data entry** for most routine tasks

### The Problem We Solved
**Before:**
- Manual tracking of capacity and workload
- No visibility into team allocation
- Guessing at how long tasks take
- Calendar events disconnected from tasks
- Manual backdrop requests and generation

**After:**
- Automatic capacity calculation and tracking
- Real-time visibility into who's working on what
- Data-driven estimates based on historical performance
- Calendar events automatically create tasks
- AI-generated backdrops on demand

---

## 2. THE THREE ASANA PROJECTS (5 minutes)

### Project Structure
```
📋 Preproduction (1208336083003480)
   ↓
🎬 Production (1209597979075357)
   ↓
🎞️ Post Production (1209581743268502)
```

### Key Custom Fields (What You'll See & Use)

**Everyone Uses:**
- **Category** - What type of work (Video, Event, Graphics, etc.)
- **% Allocation** - How much of weekly capacity this takes
- **Film Date** - When filming happens
- **Start Date** - When work begins
- **Task Progress** - Current status (Scheduled, In Progress, etc.)

**Auto-Populated (You'll See These, But Don't Touch):**
- **Actual Allocation** - System calculates after completion
- **Video Duration** - Extracted from task details
- **Approval** - Workflow status

### How Tasks Flow
1. Create task in **Preproduction** → Scout, plan, prepare
2. Move to **Production** → Film, record, capture
3. Move to **Post Production** → Edit, review, publish

---

## 3. AUTOMATIC CAPACITY SCORING (10 minutes)

### What It Does
**Every 15 minutes**, the system automatically:
1. Scans all tasks across all three projects
2. Calculates **% Allocation** (weekly capacity consumed)
3. Updates tasks with estimates
4. Tracks actual time spent on completed tasks

### How It Calculates % Allocation

**Base Formula:**
```
Category Base × Duration Multiplier × Type Modifier = % Allocation
```

**Category Bases (What type of work):**
- Full Video: 11-19% (based on length)
- Testimonial: 11-19% (based on length)
- B-Roll: 3-6%
- Social Media: 1.5-3%
- Event Coverage: 5-11%
- Graphics: 2-4%
- Communications: 1-2%

**Duration Multipliers:**
```
0-2 min:   × 1.0
2-5 min:   × 1.3
5-10 min:  × 1.7
10-20 min: × 2.2
20+ min:   × 3.0
```

**Type Modifiers:**
- Educational: +30%
- Enriching: +15%
- Celebrational: +10%
- Promotional: Base
- Administrative: -20%

### What This Means for You

**When creating a task:**
1. Set the **Category** (Video, Event, etc.)
2. Include duration in title/notes: "5-minute testimonial video"
3. Set the **Type** (Educational, Enriching, etc.)
4. **System automatically calculates % Allocation within 15 minutes**

**Example:**
```
Task: "5-minute educational video on quantum computing"

Calculation:
- Category: Full Video (15% base for 5 min)
- Type: Educational (+30%)
- Result: 15% × 1.30 = 19.5% allocation
```

This means: **One person would spend ~19.5% of their week on this task**

---

## 4. THE DASHBOARD - YOUR MISSION CONTROL (10 minutes)

### Live Dashboard: `index.html`
**Updated automatically every 15 minutes and pushed to GitHub**

### What You'll See

#### A. Weekly Capacity Overview
- **Total tasks** in each project
- **Capacity by category** (Video, Events, Graphics, etc.)
- **Team allocation** percentage
- Color-coded warnings (🟢 Good, 🟡 High, 🔴 Overloaded)

#### B. Production Timeline
**Visual calendar showing:**
- What's filming this week
- What's filming next week
- Film dates for next 30 days
- Conflicts and overlaps

#### C. Performance Metrics
- **Estimated vs. Actual Allocation**
  - Did tasks take more/less time than expected?
  - Tracks variance to improve future estimates
- **Tasks with actual data tracked**
- **Average variance** (Are we over/under estimating?)

#### D. Delivery Performance
- **On-time completion rate**
- **Average delay** for late tasks
- **Category performance** (Which types of work are on time?)

### How to Use the Dashboard

**Daily Check-In:**
- Look at Production Timeline to see what's filming
- Check capacity percentage (Are we overloaded?)

**Weekly Planning:**
- Review upcoming film dates
- Check if total allocation > 100% (too much scheduled)
- Identify categories consuming most capacity

**Monthly Review:**
- Look at delivery performance
- Check estimated vs. actual variance
- Adjust future estimates based on trends

---

## 5. WOV (WEEKLY OPPORTUNITY VIDEO) AUTOMATION (5 minutes)

### What It Does
**Every 30 minutes**, the system:
1. Checks Google Calendar for events with "WOV" in the title
2. Identifies the talent (non-studio attendee)
3. Automatically creates a task in **Production project**

### What Gets Created Automatically

**Task Name:**
```
WOV - [Talent Name]
```

**Task Details:**
- **Film Date**: Set from calendar event
- **Due Date**: Thursday 10am before the Sunday it airs
- **Task Progress**: "Scheduled"
- **Approval**: "Approved"
- **Virtual Location**: "WOV Set"
- **Type**: "Enriching"
- **Category**: "Communications"

### What You Need to Do

**Nothing!** Just schedule the calendar event with "WOV" in the title.

**Example:**
```
Calendar Event: "WOV - Interview with Dr. Sarah Chen"
Date: December 15, 2025 at 2:00 PM

↓ Automatically creates ↓

Asana Task: "WOV - Dr. Sarah Chen"
Film Date: Dec 15, 2025 at 2:00 PM
Due Date: Dec 18, 2025 at 10:00 AM (Thursday before Sunday)
```

---

## 6. CALENDAR SYNCHRONIZATION (5 minutes)

### Two-Way Calendar Integration

**From Asana → Google Calendar:**

**Film Date Sync** (Every 30 minutes)
- Tasks with Film Dates create calendar events
- Format: `🎬 FILM: [Task Name]`
- Shows on your calendar when filming happens

**Due Date Sync** (Every 30 minutes)
- Tasks with Due Dates create calendar events
- Format: `✅ DUE: [Task Name]`
- Shows when deliverables are due

**From Google Calendar → Asana:**

**WOV Sync** (Every 30 minutes)
- Calendar events with "WOV" create Asana tasks
- Automatically populated with all details

### What You'll See

**In Google Calendar:**
- `🎬 FILM:` events (filming schedule)
- `✅ DUE:` events (delivery deadlines)
- Regular `WOV` events (your scheduled recordings)

**In Asana:**
- Tasks automatically created from WOV calendar events
- Film Date and Due Date fields synced

---

## 7. AI-POWERED BACKDROP GENERATION (5 minutes)

### The Old Way
1. Request backdrop from graphics team
2. Wait for mockup
3. Provide feedback
4. Wait for revisions
5. Get final backdrop (days/weeks later)

### The New Way
1. Describe what you want
2. AI generates 4 options in ~60 seconds
3. Pick the best one
4. Done

### How to Generate Backdrops

**Option 1: Via Script** (Currently running)
```bash
python production_backdrops.py
```

**Option 2: Manual Request** (Coming soon - web interface)

### What You Can Request

**Styles:**
- Professional office
- Library/bookshelf
- Modern tech environment
- Seasonal themes (Christmas, Halloween, etc.)
- Custom scenes

**Example Prompts:**
```
"Professional library with warm lighting and vintage books"
"Modern tech studio with blue accent lighting"
"Cozy office with plants and natural light"
"Winter holiday scene with fireplace and decorations"
```

### Automatic Backdrop System

**Currently Running for WOV:**
- Every task in Production project
- Checks if backdrop exists
- Generates 4 variations automatically
- Saves to production backdrops folder

**AI Models Used:**
- **Grok-4-Fast**: Prompt enhancement and creative direction
- **Stable Diffusion Ultra**: High-quality image generation

---

## 8. WEEKLY CAPACITY REPORT (5 minutes)

### Automatic Monday Morning Report

**Every Monday at 8:00 AM**, you receive an email with:

#### This Week's Snapshot
- Total tasks scheduled
- Capacity by category
- Estimated weekly allocation percentage
- Team workload distribution

#### Insights
- **Capacity warnings** (Are we overbooked?)
- **Category breakdown** (What's consuming most time?)
- **Film schedule** (What's being recorded this week?)

#### Recommendations
- Suggested task deferrals (if overloaded)
- Underutilized capacity (if under 80%)
- Scheduling conflicts to resolve

### How to Use It

**Monday Planning Meeting:**
1. Review the report
2. Identify overload weeks
3. Defer or reassign tasks
4. Confirm film schedule

---

## 9. WHAT'S MANUAL VS. AUTOMATIC (5 minutes)

### What YOU Do (Manual)

✏️ **Task Creation**
- Create tasks in appropriate project
- Set Category, Type, Approval status
- Add task description and notes
- Set Film Date (if applicable)

✏️ **Task Management**
- Move tasks between projects (Prep → Prod → Post)
- Mark tasks complete
- Update Task Progress status
- Add notes about challenges/complexity

✏️ **Calendar Management**
- Schedule WOV events in Google Calendar
- Manage film schedule

### What the SYSTEM Does (Automatic)

🤖 **Every 15 Minutes:**
- Calculate % Allocation for all tasks
- Update capacity estimates
- Calculate actual allocation for completed tasks
- Regenerate dashboard
- Commit dashboard to GitHub

🤖 **Every 30 Minutes:**
- Sync Film Dates to Google Calendar
- Sync Due Dates to Google Calendar
- Sync WOV calendar events to Asana tasks
- Generate production backdrops

🤖 **Every Monday at 8 AM:**
- Generate weekly capacity report
- Email report to team

---

## 10. BEST PRACTICES & TIPS (5 minutes)

### For Accurate Capacity Tracking

✅ **DO:**
- Include video duration in task title or notes: "5-minute educational video"
- Set Category accurately (Video, Event, Graphics, etc.)
- Set Type appropriately (Educational, Enriching, etc.)
- Mark tasks complete when done
- Add notes about what took longer/shorter than expected

❌ **DON'T:**
- Leave Category blank
- Use "Other" unless truly necessary
- Delete tasks (mark complete instead, for tracking)
- Manually edit % Allocation (system recalculates every 15 min)

### For WOV Tasks

✅ **DO:**
- Include "WOV" in calendar event title
- Invite the talent to the calendar event
- Exclude studio team from attendee list (or use studio emails in the filter)

❌ **DON'T:**
- Create WOV tasks manually (let automation handle it)
- Edit auto-generated WOV task fields (they'll be overwritten)

### For Dashboard Accuracy

✅ **DO:**
- Set Film Dates for filming tasks
- Set Due Dates for deliverables
- Update Task Progress as work progresses
- Add Start Date when work begins

### For Better Estimates

✅ **DO:**
- Add detailed notes to complex tasks
- Mention if something was "easier than expected" or "took longer"
- Note number of revisions required
- Document challenges encountered

**Why?** The AI uses these notes to calculate actual allocation and improve future estimates.

---

## 11. TROUBLESHOOTING & FAQ (5 minutes)

### Common Questions

**Q: "My task doesn't have a % Allocation yet"**
- Wait up to 15 minutes (system runs every 15 min)
- Check that Category is set (not blank)
- Verify task has video duration in title/notes if it's a video

**Q: "The % Allocation seems wrong"**
- System recalculates every 15 minutes based on latest info
- Check Category, Type, and duration are correct
- See formula in Section 3 for how it's calculated

**Q: "I created a WOV calendar event but no task appeared"**
- Wait 30 minutes (WOV sync runs every 30 min)
- Verify event has "WOV" in the title
- Check that event is not in the past
- Ensure event has at least one non-studio attendee

**Q: "Calendar events are duplicating"**
- This was a bug, now fixed
- Events starting with "✅ DUE:" or "🎬 FILM:" are auto-generated
- Don't manually create events with these prefixes

**Q: "Dashboard isn't updating"**
- Check last update timestamp at top of dashboard
- System updates every 15 minutes
- Auto-commits to GitHub
- Refresh browser (Ctrl+F5 / Cmd+Shift+R)

### Who to Ask for Help

**For Asana/Automation Issues:**
- Check scripts: `~/Scripts/StudioProcesses/`
- Check logs: `scorer_cron.log`, `wov_sync.log`, `timeline.log`

**For Calendar Sync Issues:**
- Check cron: `crontab -l`
- Check logs: `film_calendar_sync.log`, `due_calendar_sync.log`

---

## 12. WHAT'S NEXT - ROADMAP (3 minutes)

### Coming Soon

🔜 **Web Interface for Backdrop Generation**
- Request backdrops via web form
- Real-time generation and preview
- Download high-res versions

🔜 **Task Templates**
- Pre-configured templates for common video types
- Auto-populate fields based on template
- Faster task creation

🔜 **Advanced Analytics**
- Team member workload distribution
- Category trends over time
- Predictive capacity planning

🔜 **Slack Integration**
- Capacity alerts in Slack
- WOV task notifications
- Weekly report in team channel

### Feedback Welcome!

**What would make this system more useful for you?**
- Features you'd like to see
- Reports that would be helpful
- Automation you'd like added

---

## 13. HANDS-ON DEMO (10 minutes)

### Live Walkthrough

**Demo 1: Create a Task and Watch Automation**
1. Create new video task in Production
2. Set Category: "Full Video"
3. Add "8-minute educational video" to title
4. Set Type: "Educational"
5. Wait 15 minutes → Show % Allocation auto-calculated

**Demo 2: WOV Calendar Event → Asana Task**
1. Create Google Calendar event: "WOV - Test Demo"
2. Set date/time
3. Add fake talent as attendee
4. Wait 30 minutes → Show Asana task auto-created

**Demo 3: Dashboard Tour**
1. Open `index.html`
2. Show capacity overview
3. Show production timeline
4. Show delivery performance
5. Explain how to interpret metrics

**Demo 4: Complete a Task and See Actual Allocation**
1. Find a completed task
2. Show original estimated allocation
3. Show calculated actual allocation
4. Explain variance

---

## 14. Q&A (5 minutes)

### Open Floor
- Questions about any feature
- Clarifications on workflow
- Requests for additional training

---

## APPENDIX: QUICK REFERENCE

### Key Files & Locations
```
~/Scripts/StudioProcesses/
├── video_scorer.py          # Main automation (% allocation)
├── production_timeline.py   # Timeline generation
├── generate_dashboard.py    # Dashboard creation
├── wov_calendar_sync.py     # WOV automation
├── film_date_calendar_sync.py   # Film date sync
├── due_date_calendar_sync.py    # Due date sync
├── production_backdrops.py  # AI backdrop generation
└── index.html              # Live dashboard
```

### Cron Schedule (What Runs When)
```
Every 15 min:  video_scorer.py + production_timeline.py + dashboard commit
Every 30 min:  WOV sync + Film sync + Due sync
Every Monday:  Weekly capacity report
```

### Important URLs
- **Dashboard**: [GitHub Pages URL]
- **Asana Projects**:
  - Preproduction: https://app.asana.com/0/1208336083003480
  - Production: https://app.asana.com/0/1209597979075357
  - Post Production: https://app.asana.com/0/1209581743268502

### Custom Field Reference
| Field Name | Type | Purpose | Auto-Populated? |
|------------|------|---------|-----------------|
| Category | Enum | Type of work | ❌ Manual |
| % Allocation | Number | Weekly capacity | ✅ Auto |
| Actual Allocation | Number | Real capacity used | ✅ Auto |
| Film Date | Date/Time | When filming | ❌ Manual |
| Start Date | Date | Work begins | ❌ Manual |
| Due Date | Date | Deadline | ❌ Manual |
| Task Progress | Enum | Status | ❌ Manual |
| Approval | Enum | Workflow state | ❌ Manual |
| Type | Enum | Content type | ❌ Manual |
| Virtual Location | Text | Where filmed | ❌ Manual |

---

## THANK YOU!

**Questions? Feedback? Ideas?**

Let's make this system work for everyone!
