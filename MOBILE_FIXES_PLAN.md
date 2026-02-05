# Mobile Dashboard Fixes - Comprehensive Plan

## File: `/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py`

---

## Issue Analysis

Based on the screenshots provided and code analysis, three critical mobile formatting issues were identified:

### 1. Header Button Layout (IMG_2669.PNG)
- Dark Mode toggle overlapping PDF/CSV buttons
- Poor button spacing on mobile devices
- Controls need better responsive positioning

### 2. Historical Capacity Chart Not Rendering (IMG_2668.PNG)
- Chart canvas is present but chart is not visible/rendering
- Empty white space where chart should display
- Likely caused by Chart.js initialization or responsive issues

### 3. Project Timeline Formatting (IMG_2667.PNG)
- Project names are truncated and cut off
- Timeline bars poorly positioned
- Date headers cramped and overlapping
- Timeline needs complete mobile redesign

---

## Fix #1: Header Button Layout (Lines 1162-1389)

### Problem
Current CSS has buttons stacking incorrectly on mobile, causing overlap between Dark Mode toggle and PDF/CSV export buttons.

### Current Code Location
Lines 1162-1389 in `generate_dashboard.py`

### Solution

Replace the header controls CSS (lines 1162-1389) with the following mobile-optimized version:

```css
/* Header controls layout */
.header-controls {
    position: absolute;
    top: 15px;
    right: 30px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    flex-direction: column;
    z-index: 10;
}

@media (min-width: 640px) {
    .header-controls {
        flex-direction: row;
        align-items: center;
    }
}

.export-controls {
    display: flex;
    gap: 8px;
    align-items: center;
}

/* Mobile breakpoint - IMPROVED */
@media (max-width: 768px) {
    .header {
        padding: 15px;
        padding-top: 100px; /* Increased from 80px to prevent overlap */
        position: relative;
    }

    .header-controls {
        position: absolute;
        top: 10px;
        left: 10px;
        right: 10px;
        display: grid;
        grid-template-columns: 1fr;
        gap: 10px;
        z-index: 10;
        width: calc(100% - 20px);
    }

    .theme-toggle {
        width: 100%;
        justify-content: center;
        padding: 10px 16px;
        min-height: 48px; /* Increased for better touch target */
        box-sizing: border-box;
    }

    .export-controls {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        width: 100%;
    }

    .export-btn {
        font-size: 13px;
        padding: 10px 16px;
        min-height: 48px; /* Increased for better touch target */
        min-width: unset;
        width: 100%;
        justify-content: center;
        box-sizing: border-box;
    }
}

/* Small mobile breakpoint - IMPROVED */
@media (max-width: 480px) {
    .header {
        padding: 12px;
        padding-top: 110px; /* Even more space for stacked buttons */
    }

    .header-controls {
        top: 8px;
        left: 8px;
        right: 8px;
        gap: 8px;
        width: calc(100% - 16px);
    }

    .theme-toggle {
        padding: 10px 12px;
        font-size: 13px;
    }

    .export-btn {
        font-size: 12px;
        padding: 10px 12px;
    }
}
```

### Key Changes
1. Changed mobile header controls from `flex` to `grid` layout for better control
2. Increased `padding-top` on header to 100px (was 80px) to prevent content overlap
3. Made buttons full-width on mobile with proper grid distribution
4. Increased minimum touch targets to 48px (Apple/Android HIG recommendation)
5. Added proper box-sizing to prevent width overflow

---

## Fix #2: Historical Capacity Chart Rendering (Lines 3894-4066)

### Problem
Chart.js canvas exists but chart doesn't render on mobile. This is likely due to:
1. Canvas size calculations failing on mobile
2. Chart initialization timing issues
3. Missing responsive configuration

### Current Code Location
Lines 3894-4066 in `generate_dashboard.py`

### Solution A: Add Mobile-Specific Chart Initialization

Add this code AFTER line 4066 (after the chart initialization):

```javascript
// Mobile-specific chart rendering fix
function ensureChartRendering() {
    const canvas = document.getElementById('capacityHistoryChart');
    if (!canvas) {
        console.error('Canvas element not found');
        return;
    }

    const container = canvas.parentElement;
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    console.log('Chart container dimensions:', containerWidth, 'x', containerHeight);

    // Force canvas to match container dimensions
    if (containerWidth > 0 && containerHeight > 0) {
        canvas.width = containerWidth;
        canvas.height = containerHeight;
        canvas.style.width = containerWidth + 'px';
        canvas.style.height = containerHeight + 'px';
    }

    // Regenerate chart after size adjustment
    if (window.capacityHistoryChart) {
        window.capacityHistoryChart.resize();
    }
}

// Call after a delay to ensure DOM is fully rendered
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        ensureChartRendering();
    }, 500);
});

// Re-render on window resize
let resizeTimer;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function() {
        ensureChartRendering();
    }, 250);
});
```

### Solution B: Update Chart Options for Better Mobile Support

Replace the chart options in `generateCapacityHistoryChart()` function (around line 3975) to include:

```javascript
options: {
    responsive: true,
    maintainAspectRatio: false,
    devicePixelRatio: window.devicePixelRatio || 1, // ADD THIS LINE
    layout: {
        padding: {
            top: window.innerWidth < 768 ? 10 : 20,
            bottom: window.innerWidth < 768 ? 10 : 0,
            left: window.innerWidth < 768 ? 5 : 10,  // ADD THIS LINE
            right: window.innerWidth < 768 ? 5 : 10  // ADD THIS LINE
        }
    },
    // ... rest of options
}
```

### Solution C: Add CSS Fixes for Chart Container

Add this CSS to the `.chart-container` section (around line 2558):

```css
.chart-container {
    position: relative;
    height: 280px;
    margin-top: 12px;
    max-width: 100%;
    overflow: hidden;
    display: block; /* ADD THIS */
    width: 100%; /* ADD THIS */
}

.chart-container canvas {
    position: relative !important; /* ADD THIS */
    max-height: 100%; /* ADD THIS */
}

/* Mobile chart improvements */
@media (max-width: 768px) {
    .chart-container {
        height: 300px; /* Increased from 250px for better visibility */
        width: 100% !important;
        max-width: 100% !important;
        padding: 10px 0; /* ADD THIS - breathing room */
    }

    .chart-container canvas {
        display: block !important; /* ADD THIS */
        max-width: 100% !important;
        width: 100% !important; /* ADD THIS */
        height: 100% !important;
    }
}

@media (max-width: 480px) {
    .chart-container {
        height: 280px; /* Increased from 220px */
    }
}
```

---

## Fix #3: Project Timeline Mobile Redesign (Lines 2054-2178 & 4100-4235)

### Problem
Timeline on mobile has several issues:
1. Project names truncated and unreadable
2. Date headers cramped and overlapping
3. Timeline bars poorly positioned
4. Overall layout not optimized for narrow screens

### Current Code Location
- CSS: Lines 2054-2178
- JavaScript: Lines 4100-4235

### Solution A: Completely Redesign Timeline CSS for Mobile

Replace timeline CSS (lines 2054-2178) with this mobile-first approach:

```css
/* ===== TIMELINE GANTT STYLES ===== */
.timeline-container {
    margin: 15px 0;
    overflow: hidden;
    list-style: none !important;
    position: relative;
    padding-left: 0 !important;
}

/* Remove vertical line on mobile */
.timeline-container::before {
    content: '';
    position: absolute;
    left: 25%;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--brand-secondary);
    z-index: 10;
    display: none; /* Hide on mobile by default */
}

@media (min-width: 769px) {
    .timeline-container::before {
        display: block;
    }
}

.timeline-container *,
.timeline-container *::before,
.timeline-container *::after {
    list-style: none !important;
    list-style-type: none !important;
}

.timeline-header {
    display: flex;
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--border-color);
}

.timeline-project-col {
    width: 25%;
    font-weight: 600;
    color: var(--text-primary);
    font-size: 14px;
    padding-right: 12px;
    margin-right: 12px;
    flex-shrink: 0;
}

.timeline-dates {
    display: flex;
    flex: 1;
}

.timeline-date {
    flex: 1;
    text-align: center;
    font-size: 11px;
    color: var(--text-secondary);
    font-weight: 500;
}

.timeline-row {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
    min-height: 32px;
    list-style: none !important;
    list-style-type: none !important;
}

.timeline-row::before,
.timeline-row::after,
.timeline-row::marker {
    display: none !important;
    content: none !important;
}

.timeline-project-name {
    width: 25%;
    font-size: 13px;
    color: var(--text-primary);
    padding-right: 12px;
    font-weight: 500;
    margin-right: 12px;
    flex-shrink: 0;
    line-height: 1.2;
    overflow: hidden;
    word-wrap: break-word;
}

.timeline-project-name::before,
.timeline-project-name::after,
.timeline-project-name::marker {
    display: none !important;
    content: '' !important;
}

.timeline-bars {
    display: flex;
    flex: 1;
    position: relative;
    height: 32px;
}

.timeline-bar {
    position: absolute;
    height: 24px;
    border-radius: 4px;
    background: var(--brand-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    color: white;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
}

.timeline-bar.critical {
    background: #dc3545;
}

.timeline-bar.warning {
    background: #ffc107;
}

.timeline-bar.normal {
    background: var(--brand-primary);
}

.timeline-bar.info {
    background: #17a2b8;
}

/* MOBILE TIMELINE REDESIGN */
@media (max-width: 768px) {
    .timeline-container {
        margin: 10px -15px; /* Extend to card edges */
        padding: 0 10px;
    }

    /* Switch to card-based layout on mobile */
    .timeline-header {
        display: none; /* Hide header on mobile */
    }

    .timeline-row {
        flex-direction: column;
        align-items: stretch;
        margin-bottom: 16px;
        padding: 12px;
        background: var(--bg-tertiary);
        border-radius: 8px;
        border-left: 4px solid var(--brand-primary);
        min-height: auto;
    }

    .timeline-row:has(.timeline-bar.critical) {
        border-left-color: #dc3545;
    }

    .timeline-row:has(.timeline-bar.warning) {
        border-left-color: #ffc107;
    }

    .timeline-project-name {
        width: 100%;
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 8px;
        padding-right: 0;
        margin-right: 0;
        white-space: normal;
        word-break: break-word;
        line-height: 1.4;
    }

    .timeline-bars {
        width: 100%;
        height: 40px;
        margin-top: 8px;
        background: var(--bg-secondary);
        border-radius: 6px;
        position: relative;
        padding: 0;
    }

    .timeline-bar {
        height: 32px;
        top: 4px;
        font-size: 12px;
        border-radius: 4px;
        padding: 0 8px;
        min-width: 40px; /* Ensure bar is visible */
    }

    /* Add date labels below bars on mobile */
    .timeline-bars::after {
        content: attr(data-dates);
        position: absolute;
        bottom: -20px;
        left: 0;
        right: 0;
        font-size: 11px;
        color: var(--text-secondary);
        text-align: left;
    }
}

@media (max-width: 480px) {
    .timeline-project-name {
        font-size: 14px;
    }

    .timeline-bars {
        height: 36px;
    }

    .timeline-bar {
        height: 28px;
        font-size: 11px;
    }
}
```

### Solution B: Update JavaScript Timeline Generation

Replace the `generateTimeline()` function (around line 4101) with this mobile-friendly version:

```javascript
// Timeline Gantt - Mobile Optimized
function generateTimeline() {
    const timelineContainer = document.getElementById('projectTimeline');
    if (!timelineContainer) return;

    // Real shoots and deadlines data
    const shoots = SHOOTS_JSON_PLACEHOLDER;
    const deadlines = DEADLINES_JSON_PLACEHOLDER;

    // Combine and convert to timeline format
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const projects = [];

    // Add shoots
    shoots.forEach(shoot => {
        let startDate, endDate, duration;

        if (shoot.start_on && shoot.due_on) {
            startDate = new Date(shoot.start_on);
            endDate = new Date(shoot.due_on);
        } else if (shoot.start_on) {
            startDate = new Date(shoot.start_on);
            endDate = new Date(shoot.datetime);
        } else if (shoot.due_on) {
            const dueDate = new Date(shoot.due_on);
            startDate = new Date(dueDate);
            startDate.setDate(startDate.getDate() - 5);
            endDate = dueDate;
        } else {
            const filmDate = new Date(shoot.datetime);
            startDate = new Date(filmDate);
            startDate.setDate(startDate.getDate() - 3);
            endDate = filmDate;
        }

        const daysFromNow = Math.floor((startDate - now) / (1000 * 60 * 60 * 24));
        const daysToEnd = Math.floor((endDate - now) / (1000 * 60 * 60 * 24));

        if (daysToEnd >= 0 && daysFromNow < 10) {
            const start = Math.max(0, daysFromNow);
            const end = Math.min(10, daysToEnd + 1);
            duration = end - start;

            if (duration > 0) {
                projects.push({
                    name: shoot.name, // Remove emoji for cleaner mobile display
                    icon: '🎬',
                    start: start,
                    duration: duration,
                    status: daysFromNow <= 2 ? 'critical' : 'normal',
                    startDate: startDate,
                    endDate: endDate
                });
            }
        }
    });

    // Add deadlines
    deadlines.forEach(deadline => {
        let startDate, endDate, duration;

        if (deadline.start_on) {
            startDate = new Date(deadline.start_on);
            endDate = new Date(deadline.due_date);
        } else {
            const dueDate = new Date(deadline.due_date);
            startDate = new Date(dueDate);
            startDate.setDate(startDate.getDate() - 7);
            endDate = dueDate;
        }

        const daysFromNow = Math.floor((startDate - now) / (1000 * 60 * 60 * 24));
        const daysToEnd = Math.floor((endDate - now) / (1000 * 60 * 60 * 24));

        if (daysToEnd >= 0 && daysFromNow < 10) {
            const start = Math.max(0, daysFromNow);
            const end = Math.min(10, daysToEnd + 1);
            duration = end - start;

            if (duration > 0) {
                projects.push({
                    name: deadline.name,
                    icon: '⏰',
                    start: start,
                    duration: duration,
                    status: daysToEnd <= 2 ? 'critical' : daysToEnd <= 5 ? 'warning' : 'normal',
                    startDate: startDate,
                    endDate: endDate
                });
            }
        }
    });

    if (projects.length === 0) {
        projects.push({
            name: 'No upcoming shoots or deadlines in next 10 days',
            icon: '📅',
            start: 0,
            duration: 10,
            status: 'normal',
            startDate: now,
            endDate: new Date(now.getTime() + 10 * 24 * 60 * 60 * 1000)
        });
    }

    const totalDays = 10;
    const dates = [];
    for (let i = 0; i < totalDays; i++) {
        const date = new Date();
        date.setDate(date.getDate() + i);
        dates.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }

    const isMobile = window.innerWidth <= 768;

    let html = '';

    if (!isMobile) {
        // Desktop: Use traditional timeline layout
        html += '<div class="timeline-header">';
        html += '<div class="timeline-project-col">Project</div>';
        html += '<div class="timeline-dates">';
        dates.forEach(date => {
            html += `<div class="timeline-date">${date}</div>`;
        });
        html += '</div></div>';

        projects.forEach(project => {
            html += '<div class="timeline-row">';
            html += `<div class="timeline-project-name">${project.icon} ${project.name}</div>`;
            html += '<div class="timeline-bars">';
            const leftPercent = (project.start / totalDays) * 100;
            const widthPercent = (project.duration / totalDays) * 100;
            html += `<div class="timeline-bar ${project.status}" style="left: ${leftPercent}%; width: ${widthPercent}%">${project.duration}d</div>`;
            html += '</div></div>';
        });
    } else {
        // Mobile: Use card-based layout
        projects.forEach(project => {
            const startDateStr = project.startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const endDateStr = project.endDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            const dateRange = `${startDateStr} - ${endDateStr}`;

            html += '<div class="timeline-row">';
            html += `<div class="timeline-project-name">${project.icon} ${project.name}</div>`;
            html += `<div class="timeline-bars" data-dates="${dateRange}">`;
            const leftPercent = (project.start / totalDays) * 100;
            const widthPercent = (project.duration / totalDays) * 100;
            html += `<div class="timeline-bar ${project.status}" style="left: ${leftPercent}%; width: ${widthPercent}%">${project.duration} days</div>`;
            html += '</div></div>';
        });
    }

    timelineContainer.innerHTML = html;
}

// Regenerate timeline on window resize
let timelineResizeTimer;
window.addEventListener('resize', function() {
    clearTimeout(timelineResizeTimer);
    timelineResizeTimer = setTimeout(function() {
        generateTimeline();
    }, 250);
});
```

---

## Implementation Checklist

### Phase 1: Header Button Layout
- [ ] Backup original `generate_dashboard.py` file
- [ ] Update CSS for `.header-controls` (lines 1162-1389)
- [ ] Test on iPhone (Safari) - verify no overlap
- [ ] Test on Android (Chrome) - verify no overlap
- [ ] Test button touch targets (minimum 44x44px)
- [ ] Test landscape orientation
- [ ] Verify desktop layout still works

### Phase 2: Chart Rendering
- [ ] Add mobile chart initialization function (after line 4066)
- [ ] Update chart options with device pixel ratio
- [ ] Update `.chart-container` CSS (around line 2558)
- [ ] Test chart renders on mobile immediately on load
- [ ] Test chart renders after page rotation
- [ ] Test chart renders after theme toggle
- [ ] Verify chart is interactive (pinch/zoom, tooltip)
- [ ] Check chart legend is readable

### Phase 3: Timeline Redesign
- [ ] Update timeline CSS (lines 2054-2178)
- [ ] Update `generateTimeline()` JavaScript (around line 4101)
- [ ] Test project names are fully visible
- [ ] Test date ranges are clear
- [ ] Test timeline bars are properly sized
- [ ] Test touch interaction on timeline items
- [ ] Test with 0 projects, 1 project, and 5+ projects
- [ ] Verify desktop layout still works

### Phase 4: Testing & Validation
- [ ] Test on physical iPhone device (Safari)
- [ ] Test on physical Android device (Chrome)
- [ ] Test on iPad (tablet breakpoint)
- [ ] Test screen rotation (portrait/landscape)
- [ ] Test with Chrome DevTools mobile emulation
- [ ] Test Dark Mode on all fixes
- [ ] Test Light Mode on all fixes
- [ ] Run Lighthouse mobile audit (target >90)
- [ ] Check WCAG accessibility (keyboard navigation, screen reader)

---

## Additional Mobile Optimizations (Bonus)

### 1. Add Loading Indicators for Charts
```javascript
// Add before chart initialization
function showChartLoading(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.font = '16px Arial';
    ctx.fillStyle = '#666';
    ctx.textAlign = 'center';
    ctx.fillText('Loading chart...', canvas.width / 2, canvas.height / 2);
}
```

### 2. Improve Touch Interactions
```css
/* Add to relevant elements */
.timeline-row,
.progress-ring,
.project-card {
    -webkit-tap-highlight-color: rgba(96, 187, 233, 0.2);
    touch-action: manipulation;
}
```

### 3. Optimize Font Sizes for Readability
```css
@media (max-width: 768px) {
    body {
        font-size: 16px; /* Prevent iOS zoom on focus */
        -webkit-text-size-adjust: 100%;
    }

    input, select, textarea {
        font-size: 16px; /* Prevent iOS zoom */
    }
}
```

### 4. Add Viewport Meta Tag Check
Ensure the HTML has this meta tag (should be in the `<head>` section):
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
```

---

## Performance Considerations

### 1. Lazy Load Charts
Only initialize charts when they scroll into view:
```javascript
const observerOptions = {
    root: null,
    rootMargin: '50px',
    threshold: 0.1
};

const chartObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const chartId = entry.target.id;
            initializeChart(chartId);
            chartObserver.unobserve(entry.target);
        }
    });
}, observerOptions);

// Observe chart containers
document.querySelectorAll('.chart-container canvas').forEach(canvas => {
    chartObserver.observe(canvas);
});
```

### 2. Debounce Resize Events
Already implemented but ensure timeout is appropriate:
```javascript
let resizeTimer;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function() {
        // Regenerate responsive elements
        generateTimeline();
        ensureChartRendering();
    }, 250); // 250ms debounce
});
```

---

## Browser Compatibility Notes

### Safari iOS Specific Issues
1. **Chart.js may have rendering issues** - ensure `devicePixelRatio` is set
2. **Fixed positioning can be problematic** - use `position: absolute` where possible
3. **Viewport units (vh/vw) can be unreliable** - use percentages for mobile

### Chrome Android Specific Issues
1. **Touch events may conflict with scroll** - use `touch-action: manipulation`
2. **Font rendering may differ** - test actual device, not just emulation
3. **Hardware acceleration** - ensure transforms use `translate3d` for smoothness

---

## Testing URLs

After implementing fixes, test these specific scenarios:

1. **iPhone SE (375px width)** - smallest common mobile device
2. **iPhone 12/13 (390px width)** - current standard iPhone size
3. **iPhone 14 Pro Max (430px width)** - largest current iPhone
4. **Samsung Galaxy S21 (360px width)** - common Android size
5. **iPad Mini (768px width)** - tablet breakpoint
6. **Landscape mode** - rotate all above devices

---

## Rollback Plan

If issues occur after deployment:

1. **Immediate Rollback**: Restore from backup
   ```bash
   cp generate_dashboard.py.backup generate_dashboard.py
   python generate_dashboard.py
   ```

2. **Partial Rollback**: Comment out specific fix sections:
   ```python
   # Wrap new code in comments
   # /* MOBILE FIX #1 - START */
   # ... new code ...
   # /* MOBILE FIX #1 - END */
   ```

3. **Debug Mode**: Add console logging:
   ```javascript
   console.log('Chart container width:', container.clientWidth);
   console.log('Canvas dimensions:', canvas.width, canvas.height);
   console.log('Timeline projects count:', projects.length);
   ```

---

## Expected Results

After implementing all fixes:

### Header (IMG_2669.PNG)
✅ Dark Mode toggle and PDF/CSV buttons no longer overlap
✅ Buttons stack vertically with proper spacing
✅ All buttons are touch-friendly (48px+ touch targets)
✅ Header content doesn't overlap with controls

### Chart (IMG_2668.PNG)
✅ Historical Capacity Utilization chart renders and is visible
✅ Chart displays all data lines with proper colors
✅ Chart legend is readable and interactive
✅ Chart responds to pinch-zoom and touch interactions
✅ Chart updates properly when rotating device

### Timeline (IMG_2667.PNG)
✅ Project names are fully visible and readable
✅ Date ranges are clearly displayed
✅ Timeline bars are properly sized and positioned
✅ Timeline switches to card layout on mobile
✅ Status colors (critical/warning/normal) are visible
✅ Touch targets are appropriate for mobile interaction

---

## Contact & Support

If you encounter any issues during implementation:

1. **Check browser console** for JavaScript errors
2. **Inspect elements** to verify CSS is being applied
3. **Test on actual devices** rather than just emulators
4. **Review Lighthouse audit** for performance/accessibility issues

---

## File Locations Reference

**Main File**: `/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py`

**Key Code Sections**:
- CSS Variables & Theme: Lines 1032-1097
- Header Controls CSS: Lines 1162-1389
- Timeline CSS: Lines 2054-2178
- Chart Container CSS: Lines 2558-2564
- Mobile Media Queries: Lines 2614-2815
- HTML Header Generation: Lines 3001-3022
- Historical Capacity Chart JS: Lines 3894-4066
- Timeline Generation JS: Lines 4100-4235

---

## Version Control

**Current Version**: v1.0 (Pre-fixes)
**Target Version**: v1.1 (Post-fixes)
**Backup Location**: Create backup before editing:
```bash
cp generate_dashboard.py generate_dashboard.py.backup
```

---

*Document created: 2026-01-30*
*Dashboard File: `/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py`*
