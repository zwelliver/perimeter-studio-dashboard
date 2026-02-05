# Screenshot to Fix Mapping Guide

## Quick Reference: Which Fix Addresses Which Screenshot

This document maps each screenshot issue to the specific fix and code location.

---

## IMG_2669.PNG - Header Button Overlap Issue

### What You See in Screenshot
```
┌─────────────────────────────┐
│ [Dark Mode] [PDF] [CSV]     │ ← Buttons overlapping
│                             │
│ Perimeter Studio Dashboard  │
│ Video Production...         │
└─────────────────────────────┘
```

### What It Should Look Like
```
┌─────────────────────────────┐
│ [   Dark Mode Toggle   ]    │ ← Full width
│ [    PDF    ] [   CSV   ]   │ ← Side by side
│                             │
│ Perimeter Studio Dashboard  │
│ Video Production...         │
└─────────────────────────────┘
```

### Fix Location
**File**: `/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py`
**Lines**: 1328-1516 (Mobile breakpoint section)

### Key Changes
```python
# BEFORE (causes overlap)
.header {
    padding-top: 80px;  # Not enough space
}

.header-controls {
    display: flex;  # Causes wrapping issues
    gap: 8px;
}

# AFTER (fixes overlap)
.header {
    padding-top: 100px;  # More space
}

.header-controls {
    display: grid;  # Better control
    grid-template-columns: 1fr;
    gap: 10px;
}

.theme-toggle {
    width: 100%;  # Full width
}

.export-controls {
    display: grid;
    grid-template-columns: 1fr 1fr;  # Two equal columns
}
```

### Testing This Fix
1. Open dashboard on phone (width < 768px)
2. Look at top of page
3. Dark Mode button should be alone on first row
4. PDF and CSV buttons should be side-by-side on second row
5. No overlap or text cutoff

---

## IMG_2668.PNG - Chart Not Rendering

### What You See in Screenshot
```
┌─────────────────────────────┐
│ 📈 Historical Capacity      │
│    Utilization              │
│                             │
│ ┌─────────────────────────┐ │
│ │                         │ │ ← Empty white space
│ │      (no chart)         │ │ ← Should show lines/data
│ │                         │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

### What It Should Look Like
```
┌─────────────────────────────┐
│ 📈 Historical Capacity      │
│    Utilization              │
│                             │
│ ┌─────────────────────────┐ │
│ │   Legend: [Team] [Nick] │ │
│ │        ╱╲                │ │
│ │      ╱    ╲    ╱╲        │ │ ← Colored lines
│ │    ╱        ╲╱    ╲      │ │ ← with data points
│ │  ╱                  ╲    │ │
│ │ Jan 1    Jan 15    Jan 30│ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

### Fix Location
**File**: `/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py`

**Multiple Locations**:
1. **CSS**: Line ~2558 (`.chart-container` definition)
2. **CSS**: Line ~2715 (mobile chart styles)
3. **JavaScript**: Line ~3975 (chart options)
4. **JavaScript**: After line 4066 (new helper function)

### Key Changes

#### Change 1: Chart Container CSS (Line ~2558)
```python
# BEFORE
.chart-container {
    position: relative;
    height: 280px;
    max-width: 100%;
}

# AFTER (adds explicit sizing)
.chart-container {
    position: relative;
    height: 280px;
    max-width: 100%;
    display: block;        # NEW
    width: 100%;          # NEW
}

.chart-container canvas {
    position: relative !important;  # NEW
    max-height: 100%;               # NEW
    display: block !important;      # NEW
}
```

#### Change 2: Mobile Chart CSS (Line ~2715)
```python
# BEFORE
.chart-container {
    height: 250px;
}

# AFTER (forces dimensions)
.chart-container {
    height: 300px;          # Larger
    width: 100% !important;  # Force width
    padding: 10px 0;        # Breathing room
}

.chart-container canvas {
    display: block !important;
    width: 100% !important;
    height: 100% !important;
}
```

#### Change 3: Chart Options (Line ~3975)
```python
# BEFORE
options: {
    responsive: true,
    maintainAspectRatio: false,
    layout: {
        padding: {
            top: window.innerWidth < 768 ? 10 : 20,
            bottom: window.innerWidth < 768 ? 10 : 0
        }
    }
}

# AFTER (adds device pixel ratio and side padding)
options: {
    responsive: true,
    maintainAspectRatio: false,
    devicePixelRatio: window.devicePixelRatio || 1,  # NEW
    layout: {
        padding: {
            top: window.innerWidth < 768 ? 10 : 20,
            bottom: window.innerWidth < 768 ? 10 : 0,
            left: window.innerWidth < 768 ? 5 : 10,   # NEW
            right: window.innerWidth < 768 ? 5 : 10   # NEW
        }
    }
}
```

#### Change 4: New Helper Function (After Line 4066)
```javascript
// NEW FUNCTION - Ensures chart renders properly on mobile
function ensureChartRendering() {
    const canvas = document.getElementById('capacityHistoryChart');
    if (!canvas) return;

    const container = canvas.parentElement;
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight;

    // Force canvas to match container dimensions
    if (containerWidth > 0 && containerHeight > 0) {
        canvas.width = containerWidth;
        canvas.height = containerHeight;
        canvas.style.width = containerWidth + 'px';
        canvas.style.height = containerHeight + 'px';

        // Trigger chart resize
        if (window.capacityHistoryChart) {
            window.capacityHistoryChart.resize();
        }
    }
}

// Call after DOM loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        ensureChartRendering();
    }, 500);
});
```

### Testing This Fix
1. Open dashboard on phone
2. Scroll to "Historical Capacity Utilization" section
3. Should see colored lines (blue, purple, yellow, etc.)
4. Should see legend at top with team member names
5. Should be able to tap legend to hide/show lines
6. Rotate phone - chart should redraw correctly

### Debugging If Chart Still Doesn't Show
```javascript
// Open browser console and run:
console.log('Canvas:', document.getElementById('capacityHistoryChart'));
console.log('Chart instance:', window.capacityHistoryChart);
console.log('Container width:', document.querySelector('.chart-container').clientWidth);

// Should output:
// Canvas: <canvas id="capacityHistoryChart" width="..." height="...">
// Chart instance: Chart {...}
// Container width: (some number > 0)

// If any are null/0, that's the problem
```

---

## IMG_2667.PNG - Timeline Formatting Issues

### What You See in Screenshot
```
┌──────────────────────────────────┐
│ 📅 10-Day Project Timeline       │
│                                  │
│ Project     Jan 28 | Jan 29 | ...│ ← Dates cramped
│ Very Long P... ████████          │ ← Name cut off
│ Another Proj... ███              │ ← Name cut off
│ Short       ████████████████     │
└──────────────────────────────────┘
```

### What It Should Look Like
```
┌──────────────────────────────────┐
│ 📅 10-Day Project Timeline       │
│                                  │
│ ┌──────────────────────────────┐ │
│ │ 🎬 Very Long Project Name    │ │ ← Full name visible
│ │ That Spans Multiple Lines    │ │
│ │ ████████                     │ │ ← Clear bar
│ │ Jan 28 - Feb 4 (7 days)      │ │ ← Date range
│ └──────────────────────────────┘ │
│                                  │
│ ┌──────────────────────────────┐ │
│ │ ⏰ Another Project Name       │ │
│ │ ███                          │ │
│ │ Jan 29 - Jan 31 (3 days)     │ │
│ └──────────────────────────────┘ │
└──────────────────────────────────┘
```

### Fix Location
**File**: `/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py`

**Two Locations**:
1. **CSS**: Lines 2054-2178 (Timeline styles)
2. **JavaScript**: Lines 4101-4235 (Timeline generation function)

### Key Changes

#### Change 1: Timeline CSS - Mobile Card Layout
```python
# BEFORE (horizontal timeline)
@media (max-width: 768px) {
    .timeline-container {
        overflow-x: auto;  # Horizontal scroll
    }

    .timeline-project-name {
        min-width: 120px;   # Fixed width = truncation
        width: 120px;
    }
}

# AFTER (vertical card layout)
@media (max-width: 768px) {
    .timeline-header {
        display: none;  # Hide header on mobile
    }

    .timeline-row {
        flex-direction: column;     # Stack vertically
        padding: 12px;
        background: var(--bg-tertiary);
        border-radius: 8px;
        border-left: 4px solid var(--brand-primary);  # Status indicator
    }

    .timeline-project-name {
        width: 100%;              # Full width
        white-space: normal;      # Allow wrapping
        word-break: break-word;   # Break long words
        line-height: 1.4;
    }

    .timeline-bars {
        width: 100%;
        background: var(--bg-secondary);
    }

    .timeline-bars::after {
        content: attr(data-dates);  # Show date range
    }
}
```

#### Change 2: Timeline JavaScript - Responsive HTML
```javascript
// BEFORE (one layout for all)
projects.forEach(project => {
    html += '<div class="timeline-row">';
    html += `<div class="timeline-project-name">${project.name}</div>`;
    html += '<div class="timeline-bars">';
    // ... timeline bar
    html += '</div></div>';
});

// AFTER (different layouts for mobile/desktop)
const isMobile = window.innerWidth <= 768;

if (!isMobile) {
    // Desktop: Traditional timeline
    html += '<div class="timeline-header">...</div>';
    projects.forEach(project => {
        html += `<div class="timeline-project-name">${project.name}</div>`;
        // ... horizontal bar
    });
} else {
    // Mobile: Card layout
    projects.forEach(project => {
        // Calculate date range
        const startDate = new Date();
        startDate.setDate(startDate.getDate() + project.start);
        const endDate = new Date(startDate);
        endDate.setDate(endDate.getDate() + project.duration);

        const dateRange = `${startDate.toLocaleDateString()} - ${endDate.toLocaleDateString()}`;

        html += '<div class="timeline-row">';
        html += `<div class="timeline-project-name">${project.name}</div>`;
        html += `<div class="timeline-bars" data-dates="${dateRange}">`;
        // ... bar with duration
        html += `${project.duration} days</div>`;
        html += '</div></div>';
    });
}

// Regenerate on resize
window.addEventListener('resize', function() {
    setTimeout(() => generateTimeline(), 250);
});
```

### Visual Comparison

#### Desktop View (> 768px width)
```
Project Name      | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 |
─────────────────────────────────────────────────────────
Project A         [████████████████                     ]
Project B         [     ████████                        ]
Project C         [               ████████████████████  ]
```

#### Mobile View (< 768px width)
```
┌────────────────────────────┐
│ 🎬 Project A               │
│ [████████████████          ]│
│ Jan 28 - Feb 1 (5 days)    │
└────────────────────────────┘

┌────────────────────────────┐
│ ⏰ Project B               │
│ [     ████                ]│
│ Jan 30 - Feb 1 (3 days)    │
└────────────────────────────┘
```

### Testing This Fix
1. Open dashboard on phone (width < 768px)
2. Scroll to "10-Day Project Timeline"
3. Each project should be in its own card
4. Project names should be fully visible (no "...")
5. Timeline bar should show duration in days
6. Date range should be visible below bar
7. Card border color indicates urgency:
   - Red = Critical (< 2 days)
   - Yellow = Warning (2-5 days)
   - Blue = Normal (> 5 days)
8. Rotate phone to landscape - should switch to horizontal timeline
9. Rotate back to portrait - should switch back to cards

---

## Summary Table

| Screenshot | Issue | Fix Location | Key Change |
|------------|-------|--------------|------------|
| IMG_2669.PNG | Button overlap | Lines 1328-1516 | Grid layout, increased padding |
| IMG_2668.PNG | Chart not rendering | Lines 2558, 2715, 3975, 4066+ | Canvas sizing, helper function |
| IMG_2667.PNG | Timeline truncation | Lines 2054-2178, 4101-4235 | Card layout, responsive JS |

---

## Complete Testing Checklist

### Before Making Changes
- [ ] Backup original file: `cp generate_dashboard.py generate_dashboard.py.backup`
- [ ] Note current file size: `wc -l generate_dashboard.py`
- [ ] Test current dashboard on mobile to confirm issues

### After Making Changes
- [ ] Regenerate dashboard: `python generate_dashboard.py`
- [ ] Check for Python errors in terminal
- [ ] Open generated HTML in desktop browser
- [ ] Open generated HTML on mobile Safari (iPhone)
- [ ] Open generated HTML on Chrome Android
- [ ] Test each fix individually:
  - [ ] Header buttons don't overlap
  - [ ] Chart renders and shows data
  - [ ] Timeline shows full project names
- [ ] Test device rotation (portrait/landscape)
- [ ] Test dark mode toggle
- [ ] Test PDF/CSV export buttons
- [ ] Test chart interactivity (legend toggle, tooltips)
- [ ] Test timeline touch interactions

### Performance Checks
- [ ] Page loads in < 3 seconds on mobile
- [ ] No console errors in browser
- [ ] Charts render in < 1 second
- [ ] Smooth scrolling (no jank)
- [ ] Animations don't stutter

---

## Quick Fix Priority

If you need to fix issues one at a time, do them in this order:

1. **Fix #1: Header Buttons** (Easiest, most visible)
   - Impact: High (first thing users see)
   - Difficulty: Easy (just CSS changes)
   - Time: 5 minutes

2. **Fix #2: Chart Rendering** (Most critical)
   - Impact: High (chart completely broken)
   - Difficulty: Medium (CSS + JS changes)
   - Time: 15 minutes

3. **Fix #3: Timeline Redesign** (Most complex)
   - Impact: Medium (usability issue)
   - Difficulty: Hard (CSS + JS rewrite)
   - Time: 30 minutes

---

## Code Block Reference

### For Quick Copy-Paste

#### Header Fix (Goes around line 1328)
```python
@media (max-width: 768px) {{
    .header {{
        padding: 15px;
        padding-top: 100px;
    }}
    .header-controls {{
        position: absolute;
        top: 10px;
        left: 10px;
        right: 10px;
        display: grid;
        grid-template-columns: 1fr;
        gap: 10px;
        width: calc(100% - 20px);
    }}
    .theme-toggle {{
        width: 100%;
        min-height: 48px;
    }}
    .export-controls {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
        width: 100%;
    }}
    .export-btn {{
        width: 100%;
        min-height: 48px;
    }}
}}
```

#### Chart CSS Fix (Goes around line 2558)
```python
.chart-container {{
    position: relative;
    height: 280px;
    max-width: 100%;
    display: block;
    width: 100%;
}}

.chart-container canvas {{
    position: relative !important;
    max-height: 100%;
    display: block !important;
}}
```

#### Chart JS Fix (Goes after line 4066)
```javascript
function ensureChartRendering() {{
    const canvas = document.getElementById('capacityHistoryChart');
    if (!canvas) return;
    const container = canvas.parentElement;
    const w = container.clientWidth;
    const h = container.clientHeight;
    if (w > 0 && h > 0) {{
        canvas.width = w;
        canvas.height = h;
        if (window.capacityHistoryChart) {{
            window.capacityHistoryChart.resize();
        }}
    }}
}}
document.addEventListener('DOMContentLoaded', function() {{
    setTimeout(ensureChartRendering, 500);
}});
```

---

*Screenshot Mapping Guide created: 2026-01-30*
*For dashboard file: `/Users/comstudio/Scripts/StudioProcesses/generate_dashboard.py`*
