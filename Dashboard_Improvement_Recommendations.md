# Perimeter Studio Dashboard — Improvement Recommendations

**Prepared:** February 5, 2026
**Scope:** Full analysis of `index.html`, `generate_dashboard.py`, and the automation ecosystem

---

## Executive Summary

The Studio Dashboard is a genuinely impressive system — it pulls live data from Asana, syncs with Google Calendar, auto-scores video projects, and renders a rich HTML dashboard with capacity tracking, forecasting, and delivery metrics. For a church production team, this is unusually sophisticated.

That said, after a deep review of the HTML output, the 5,400-line generator script, and the ~15 automation scripts, there are clear opportunities to make it more useful day-to-day, easier to maintain, and more reliable. Below are the findings organized by impact.

---

## Priority 1: Quick Wins (High Impact, Low Effort)

### 1. Fix the Capacity Discrepancy for Zach
**Issue:** `generate_dashboard.py` line 97 sets Zach's max capacity to **80%**, but `README.md` says **50%**. This means every capacity calculation, forecast, and alert could be off.
**Fix:** Decide which is correct and update both the code and docs to match.

### 2. Add Log Rotation
**Issue:** Log files are growing unchecked. `scorer.log` is **124 MB**, `timeline.log` is **44 MB**, and `scorer_cron.log` is **28 MB**. These will eventually fill the disk on the Mac Mini.
**Fix:** Add a logrotate config or a simple bash script that truncates logs over a threshold. Something like `truncate -s 5M scorer.log` in a weekly cron job would work.

### 3. Hide Empty Sections
**Issue:** "No tasks currently at risk" and "No upcoming shoots" still take up screen space. On a TV display, empty cards waste valuable real estate.
**Fix:** In the generator, wrap those sections in a conditional so they only render when there's data to show.

### 4. Replace Emoji Section Headers
**Issue:** Headers use emoji (⚠️ 🎬 ⏰ 📅 📆 📊 📈) which look unprofessional on a production dashboard displayed on a studio TV.
**Fix:** Use clean text headers or small SVG icons. This is a cosmetic change in the `generate_html_dashboard()` function.

### 5. Clarify Confusing Metrics
**Issue:** "Avg Days Variance" and "Average Capacity Variance: N/A" don't communicate anything actionable at a glance.
**Fix:** Rename to something like "Avg Delivery Offset (days)" and "Est. vs Actual Allocation Gap". If a metric is always N/A, consider hiding it until Actual Allocation data is populated.

---

## Priority 2: Dashboard UX Improvements (High Impact, Medium Effort)

### 6. Add Navigation / Section Anchors
**Issue:** The dashboard is a single 1,500-line HTML page with no way to jump between sections. On a TV this doesn't matter much, but when someone opens it on a laptop they're just scrolling endlessly.
**Fix:** Add a sticky nav bar at the top with anchor links to each major section (Quick Stats, Capacity, Forecasts, Deadlines, Charts). Consider a tabbed view for the laptop version.

### 7. Make the Capacity Display Less Confusing
**Issue:** Zach's capacity shows "93% / 50% capacity" with a progress bar, then says "186%". This triple-number display is hard to parse — is 93% the current load? The max? The bar width?
**Fix:** Simplify to one clear number per person: "Zach: 93% allocated (50% max → 186% over capacity)" with the bar colored red. The key insight (over capacity) should be the headline, not buried in math.

### 8. Implement a "TV Mode" vs "Detail Mode"
**Issue:** A lot of the dashboard's depth (30-day heatmap, historical trend charts, category breakdowns) is great for analysis but clutters a TV overview.
**Fix:** Add a toggle or URL parameter (`?mode=tv`) that shows only the essentials: team capacity bars, upcoming deadlines, at-risk tasks, and next shoots. Keep the full version for desktop deep-dives.

### 9. Auto-Refresh for the TV Display
**Issue:** The dashboard is a static HTML file that shows when it was last generated ("January 05, 2026 at 02:00 PM"). If the cron job fails, the TV shows stale data with no warning.
**Fix:** Add a small JavaScript snippet that checks the generation timestamp against the current time. If it's more than 2 hours old, show a visible "Data may be stale" warning banner.

### 10. Improve the 6-Month Capacity Timeline
**Issue:** The weekly bars use color-coding (green/yellow/orange/red) but the tiny 8px-wide bars with hover tooltips don't work well on a TV.
**Fix:** Make bars wider with numbers visible inside them. Add a summary line above: "Next 4 weeks: Healthy | Weeks 5-8: Over capacity | Q2 outlook: Needs attention."

---

## Priority 3: Code Architecture (Medium Impact, Higher Effort)

### 11. Extract the Monolithic HTML Generator
**Issue:** `generate_dashboard.py` is **5,413 lines** with the entire HTML dashboard built as one massive f-string inside `generate_html_dashboard()`. Any styling change means touching Python code.
**Fix:** Move to a template system (Jinja2 is already a Python dependency). Separate the HTML/CSS template from the data-processing logic. This would let you iterate on the design without risking the data pipeline.

### 12. Centralize Configuration
**Issue:** Project GIDs, team member names, capacity limits, and custom field IDs are hardcoded in at least **7 different scripts**. Changing a team member means editing multiple files.
**Fix:** Create a single `config.py` or `config.json` that all scripts import. Example:
```python
TEAM = {
    "Zach Welliver": {"max_capacity": 80, "email": "zwelliver@perimeter.org"},
    "Nick Clark": {"max_capacity": 100},
    ...
}
PROJECTS = {
    "preproduction": "1208336083003480",
    "production": "1209597979075357",
    ...
}
```

### 13. DRY Up Date Range Logic
**Issue:** The same "calculate task date range from start_on/due_on with 30-day fallback" logic is duplicated in 4 places: `calculate_workload_forecast()`, `generate_6month_timeline()`, `identify_at_risk_tasks()`, and `generate_capacity_heatmap()`.
**Fix:** Extract into a single `get_task_date_range(task)` helper function.

### 14. Fix Silent Error Swallowing
**Issue:** Multiple `except: pass` blocks throughout the code. When something fails — a bad date format, a missing field, an API timeout — the dashboard silently shows wrong data instead of surfacing the problem.
**Fix:** At minimum, change to `except Exception as e: logger.warning(f"...")`. For API calls, add retry logic with backoff.

### 15. Remove Inline Styles from Generated HTML
**Issue:** 300+ inline `style=` attributes throughout the HTML, particularly on heatmap cells, timeline bars, and deadline cards. This makes the CSS un-overridable on mobile (hence all the `!important` flags in the media queries).
**Fix:** Generate CSS classes dynamically instead. For the heatmap, use classes like `capacity-low`, `capacity-medium`, `capacity-high` rather than inline background colors.

---

## Priority 4: Automation Ecosystem (Medium Impact, Medium Effort)

### 16. Add a Central Health Check
**Issue:** There are ~8 automation scripts running on cron with no central monitoring. If `forecast_status_automation.py` fails silently for a week, no one knows.
**Fix:** Create a simple health-check script that runs daily, verifies each log was updated recently, and sends a summary email or Slack message. Could even be a dashboard card: "Automation Health: 7/8 scripts healthy."

### 17. Fix the Hardcoded Mac Path
**Issue:** `run_film_calendar_sync.sh` uses `/Users/comstudio/Scripts/StudioProcesses` — this will break if the system moves or gets rebuilt.
**Fix:** Use `$(dirname "$0")` or an environment variable to resolve paths relative to the script location.

### 18. Deduplicate the Forecast Matcher
**Issue:** `forecast_to_official_matcher.py` isn't listed in `cron_setup.txt` even though it has a runner script (`run_forecast_matcher.sh`). It may or may not be running — unclear.
**Fix:** Audit the actual crontab (`crontab -l`) against the documented schedule and reconcile.

### 19. Add API Rate Limiting
**Issue:** Multiple scripts poll the Asana API every 15 minutes with no rate-limit awareness. Asana's limit is 150 requests/minute.
**Fix:** Add a shared rate-limiter or at minimum stagger the cron schedules so scripts don't fire simultaneously.

---

## Priority 5: Features to Consider Adding

### 20. "Actual Allocation" Tracking
The field exists in Asana (`ACTUAL_ALLOCATION_FIELD_GID`) but the docs note it's "not yet set up." Once populated, this unlocks the most valuable metric: how accurate your estimates are. Consider adding a post-completion prompt that asks team members to log actual time.

### 21. Predictive Capacity Warnings
Currently the dashboard shows a snapshot. With the historical data already being collected in `capacity_history.csv`, you could add a trend line that says "At current pace, team will be over capacity by [date]."

### 22. Project Completion Velocity
Track how many projects the team completes per month and show a rolling average. This helps answer "are we getting faster?" and supports staffing conversations.

### 23. Client-Facing View
A simplified version of the dashboard (just project status, no internal capacity data) could be shared with ministry leaders who request video work, giving them visibility without exposing the team's internal workload.

---

## Summary Matrix

| # | Recommendation | Impact | Effort | Category |
|---|---------------|--------|--------|----------|
| 1 | Fix Zach's capacity discrepancy | High | 5 min | Data accuracy |
| 2 | Add log rotation | High | 30 min | Operations |
| 3 | Hide empty sections | Medium | 15 min | UX |
| 4 | Replace emoji headers | Low | 15 min | Polish |
| 5 | Clarify metric labels | Medium | 30 min | UX |
| 6 | Add section navigation | Medium | 1-2 hr | UX |
| 7 | Simplify capacity display | High | 1 hr | UX |
| 8 | TV Mode vs Detail Mode | High | 2-3 hr | UX |
| 9 | Auto-refresh / stale data warning | High | 30 min | Reliability |
| 10 | Improve timeline readability | Medium | 1-2 hr | UX |
| 11 | Move to Jinja2 templates | High | 4-6 hr | Architecture |
| 12 | Centralize config | High | 2 hr | Architecture |
| 13 | DRY up date logic | Medium | 1 hr | Code quality |
| 14 | Fix silent error swallowing | High | 2 hr | Reliability |
| 15 | Remove inline styles | Medium | 3-4 hr | Maintainability |
| 16 | Central health check | High | 2-3 hr | Operations |
| 17 | Fix hardcoded paths | Medium | 30 min | Operations |
| 18 | Audit cron vs actual schedule | Medium | 30 min | Operations |
| 19 | Add API rate limiting | Medium | 1-2 hr | Reliability |
| 20 | Actual Allocation tracking | High | Ongoing | Feature |
| 21 | Predictive capacity warnings | Medium | 3-4 hr | Feature |
| 22 | Project completion velocity | Low | 2-3 hr | Feature |
| 23 | Client-facing view | Low | 4-6 hr | Feature |
