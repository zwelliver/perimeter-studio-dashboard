# Perimeter Studio Dashboard - Current Architecture Analysis

## Dashboard Structure Overview

The current dashboard is a single-file HTML application with embedded CSS and JavaScript, generated server-side by Python.

---

## File Composition

```
capacity_dashboard.html (3,008 lines total)
├── HTML Structure (1,800 lines, 60%)
│   ├── Header & Metadata
│   ├── Dashboard Content
│   └── Data Sections
├── CSS Styles (974 lines, 32%)
│   ├── Base Styles
│   ├── Component Styles
│   ├── Chart Styles
│   └── Responsive Media Queries
└── JavaScript (234 lines, 8%)
    ├── Chart Generation Functions
    ├── Animation Functions
    └── Initialization Logic
```

---

## Component Breakdown

### 1. Header Section (Lines 1-982)

```
DOCTYPE & Head
├── Meta tags (charset, viewport)
├── Title
├── Chart.js CDN link
└── Embedded CSS (974 lines)
    ├── Reset & Base (lines 9-22)
    ├── Layout (lines 24-580)
    ├── Components (lines 39-500)
    ├── Charts (lines 39-354)
    └── Responsive (lines 598-973)
```

**Key CSS Sections:**
- Gauge charts (lines 39-84)
- Progress rings (lines 86-145)
- Timeline Gantt (lines 147-274)
- Radar/Spider charts (lines 276-313)
- Heatmaps (lines 355-417)
- Cards & Grids (lines 437-580)
- Media queries (lines 598-973)

---

### 2. Body Content (Lines 976-2774)

```
Dashboard Container
├── Header
│   ├── Title: "Perimeter Studio Dashboard"
│   ├── Subtitle: "Video Production Capacity Tracking..."
│   └── Timestamp
│
├── Main Grid
│   ├── Performance Overview Card
│   ├── Team Capacity Card
│   └── Contracted/Outsourced Card
│
├── At-Risk Tasks Section (Full Width)
│   └── 1 at-risk task displayed
│
├── Upcoming Shoots Section (Full Width)
│   └── 10 upcoming shoots displayed
│
├── Upcoming Deadlines Section (Full Width)
│   └── 7 deadlines displayed
│
├── Progress Rings Section (Full Width)
│   ├── On-Time Delivery Ring (100%)
│   ├── Team Utilization Ring (103%)
│   └── Active Projects Ring (48)
│
├── Timeline Gantt Section (Full Width)
│   └── Next 10 days project timeline
│
├── Radar Chart Section (Full Width)
│   └── Workload Balance visualization
│
├── Velocity Chart Section (Full Width)
│   └── 8-week completion trend
│
├── 6-Month Capacity Timeline (Full Width)
│   └── 26-week capacity bars
│
├── Daily Workload Heatmap (Full Width)
│   └── 30-day capacity distribution
│
└── Historical Capacity Chart
    └── Past 30 days utilization
```

---

### 3. JavaScript Section (Lines 2775-3008)

```javascript
Script Block
├── Progress Ring Animation
│   ├── animateProgressRing()
│   └── Calculates circumference and dashoffset
│
├── Timeline Generation
│   ├── generateTimeline()
│   ├── Processes shoots and deadlines
│   └── Renders Gantt bars dynamically
│
├── Radar Chart Generation
│   ├── generateRadarChart()
│   ├── SVG-based visualization
│   └── Category allocation data
│
├── Velocity Chart Generation
│   ├── generateVelocityChart()
│   ├── Uses Chart.js
│   └── 8-week completion data
│
└── DOMContentLoaded Initialization
    ├── 100ms delay
    ├── Animate progress rings
    └── Generate all charts
```

---

## Data Visualization Inventory

### Chart Types Used

1. **Gauge Charts** (Custom SVG)
   - Location: Progress Rings section
   - Count: 3 (On-Time, Utilization, Projects)
   - Technology: SVG + CSS animations

2. **Progress Bars** (HTML/CSS)
   - Location: Team Capacity cards
   - Count: 4 (one per team member)
   - Technology: CSS width percentage

3. **Timeline Gantt** (Custom)
   - Location: Project Timeline section
   - Count: 1 (dynamic project rows)
   - Technology: JavaScript-generated HTML

4. **Radar/Spider Chart** (Custom SVG)
   - Location: Workload Balance section
   - Count: 1 (5 categories)
   - Technology: SVG polygons

5. **Line Chart** (Chart.js)
   - Location: Velocity Trend section
   - Count: 1 (8-week trend)
   - Technology: Chart.js library

6. **Bar Chart** (Custom HTML/CSS)
   - Location: 6-Month Capacity Timeline
   - Count: 26 weekly bars
   - Technology: Flexbox + dynamic heights

7. **Heatmap** (Custom HTML/CSS)
   - Location: Daily Workload Distribution
   - Count: 30 day cells
   - Technology: CSS Grid + color scales

---

## Styling Approach

### Color Palette

```css
Primary Colors:
- Brand Blue: #60BBE9
- Dark Blue: #09243F
- Muted Gray: #6c757d

Status Colors:
- Success: #28a745
- Warning: #ffc107
- Danger: #dc3545
- Info: #17a2b8

Neutrals:
- White: #ffffff
- Gray 50: #f8f9fa
- Gray 100: #e9ecef
- Gray 200: #dee2e6
- Gray 300: #adb5bd
```

### Typography Scale

```css
Font Sizes:
- xs: 10px
- sm: 12px
- base: 13px
- md: 14px
- lg: 16px
- xl: 22px
- 2xl: 28px
- 3xl: 48px (large screens)

Font Family:
-apple-system, BlinkMacSystemFont, 'Segoe UI',
'Helvetica Neue', Arial, sans-serif
```

### Spacing System

```css
Padding/Margin Values Used:
- 4px (xs)
- 8px (sm)
- 12px (md)
- 15-20px (lg)
- 30px (xl)
- 40-50px (2xl)
```

---

## Responsive Breakpoints

```css
Mobile:
- max-width: 375px (Extra small)
- max-width: 768px (Standard mobile)
- orientation: landscape (Mobile landscape)

Desktop:
- min-width: 1920px (Full HD)
- min-width: 2560px (2K)
- min-width: 3840px (4K)

Print:
- @media print (Optimized for printing)
```

### Responsive Behavior

**Mobile (≤768px):**
- Grid: 1 column
- Charts: Height reduced (250px → 220px)
- Heatmap: 5 columns instead of 10
- Timeline bars: Minimum width reduced
- Font sizes: Slightly smaller

**Tablet (769px-1919px):**
- Grid: Auto-fit minmax(280px, 1fr)
- Default chart heights
- Full heatmap (10 columns)

**Large Screens (≥1920px):**
- Scaled up typography (18px base)
- Larger charts (400px-600px)
- More spacing
- Scaled progress rings

---

## Current Dependencies

### External Libraries
1. **Chart.js v4.4.0**
   - Source: https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js
   - Usage: Velocity trend line chart
   - Size: ~200KB
   - Note: No SRI integrity check

### No Other Dependencies
- No jQuery
- No React/Vue/Angular
- No CSS frameworks (Bootstrap, Tailwind)
- Pure vanilla JavaScript
- Custom CSS (no preprocessor)

---

## Code Organization Issues

### Inline Styles vs Classes

**Inline Styles (Problematic):**
```html
<!-- Found 200+ instances like: -->
<div style="border: 2px solid #dee2e6; border-radius: 12px; padding: 18px;">

<div style="display: flex; justify-content: space-between; margin-bottom: 12px;">

<div style="flex: 1; background: #28a745; height: 5%; cursor: pointer;">
```

**Class-Based Styles (Good):**
```html
<div class="card">
<div class="metric">
<div class="team-member">
```

**Impact:**
- Maintenance difficulty
- CSS specificity conflicts
- Code duplication
- Hard to theme

---

## Performance Characteristics

### Current Load Behavior

```
Page Load Sequence:
1. HTML parsed (3,008 lines)
2. CSS parsed (974 lines embedded)
3. Chart.js fetched from CDN (~200KB)
4. DOM Content Loaded fires
5. 100ms delay
6. All charts render simultaneously
7. Page fully interactive
```

**Estimated Load Time:**
- Fast 3G: 4-5 seconds
- Slow 3G: 8-10 seconds
- Cable/4G: 1-2 seconds

### Bottlenecks

1. **Large HTML file** - 3,008 lines loaded upfront
2. **No code splitting** - Everything loads even if not viewed
3. **Synchronous chart rendering** - Blocks main thread
4. **No lazy loading** - Below-fold charts load immediately
5. **CDN dependency** - Chart.js blocks rendering
6. **No caching strategy** - No service worker

---

## Accessibility Current State

### What's Present
- Semantic HTML (mostly)
- Readable font sizes
- Color coding with labels
- Responsive design

### What's Missing
- ARIA labels on charts
- Keyboard navigation for interactive elements
- Skip links
- Focus indicators
- Screen reader descriptions
- Semantic landmarks (header, main, nav)
- Alt text for visualizations
- Contrast ratio verification

**Estimated WCAG Compliance:** ~30% (many violations)

---

## Data Flow

```
Python Script (Server-Side)
    ↓
Generates HTML with embedded data
    ↓
Browser receives complete HTML
    ↓
JavaScript extracts data from embedded variables
    ↓
Charts render with hardcoded data
    ↓
No subsequent data fetching
```

**Key Characteristic:** Static snapshot, no live data updates

---

## Browser Compatibility

### Current Support
- Modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
- Flexbox and Grid required
- ES6 JavaScript required
- SVG support required

### Potential Issues
- No vendor prefixes for older browsers
- No Grid fallbacks
- Arrow functions not transpiled
- Template literals not polyfilled

---

## Python Integration Points

The HTML is generated by Python with data interpolation:

```python
# Example pattern (inferred):
html = f'''
<div class="metric">
    <span class="metric-label">Active Tasks</span>
    <span class="metric-value">{active_tasks}</span>
</div>
'''
```

**Integration Considerations:**
- All data is Python-generated
- No client-side data fetching
- Structure is template-driven
- Updates require re-generation

---

## Improvement Opportunities Summary

### High Priority
1. Extract CSS to external file
2. Add CSS variables for theming
3. Implement lazy loading for charts
4. Add ARIA labels and landmarks
5. Remove inline styles

### Medium Priority
6. Code splitting (separate JS files)
7. Add interactive features (search, filter)
8. Implement dark mode
9. Add tooltips
10. Export functionality

### Low Priority
11. Service worker for caching
12. Real-time data updates
13. PWA features
14. Advanced chart interactions

---

## Technical Debt Assessment

### Critical Issues
- [ ] No accessibility compliance (WCAG violations)
- [ ] Performance bottlenecks (slow load on 3G)
- [ ] No code organization (monolithic file)
- [ ] Inline styles everywhere

### Major Issues
- [ ] No error handling
- [ ] No loading states
- [ ] No user feedback
- [ ] Limited interactivity

### Minor Issues
- [ ] No comments in code
- [ ] Magic numbers everywhere
- [ ] Inconsistent naming
- [ ] No documentation

---

## Metrics Baseline

### File Size
- **Total:** ~150 KB (uncompressed)
- **HTML:** ~90 KB
- **CSS:** ~35 KB
- **JavaScript:** ~25 KB
- **Chart.js:** ~200 KB (external)

### Performance (Estimated)
- **Load Time (3G):** 4-5 seconds
- **Time to Interactive:** 5-6 seconds
- **First Contentful Paint:** 2-3 seconds
- **Largest Contentful Paint:** 4-5 seconds

### Accessibility
- **Lighthouse Score:** ~60-70
- **axe Violations:** 15-20 estimated
- **WAVE Errors:** 10-15 estimated
- **Keyboard Navigation:** 30% functional

---

## Conclusion

The Perimeter Studio Dashboard is a **functional, data-rich business tool** with solid fundamentals but significant room for improvement in:

1. **Accessibility** (WCAG compliance)
2. **Performance** (load time, code splitting)
3. **Maintainability** (code organization)
4. **User Experience** (interactivity, features)
5. **Modern Standards** (PWA, dark mode, etc.)

**The good news:** All improvements can be made incrementally without breaking the existing Python generation workflow.

---

**Next:** See `DASHBOARD_IMPROVEMENT_PLAN.md` for detailed solutions to these issues.
