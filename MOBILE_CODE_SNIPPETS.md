# Mobile Optimization Code Snippets

Quick reference for mobile-responsive patterns used in the dashboard.

---

## Chart.js Mobile Configuration

```javascript
// Responsive Chart Options
options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
        y: {
            ticks: {
                font: {
                    size: window.innerWidth < 768 ? 10 : 12
                },
                maxTicksLimit: window.innerWidth < 768 ? 6 : 10
            },
            grid: {
                display: window.innerWidth >= 480
            }
        },
        x: {
            ticks: {
                font: {
                    size: window.innerWidth < 768 ? 9 : 11
                },
                maxRotation: window.innerWidth < 768 ? 90 : 45,
                minRotation: window.innerWidth < 768 ? 90 : 45,
                autoSkip: true,
                autoSkipPadding: window.innerWidth < 768 ? 20 : 10,
                maxTicksLimit: window.innerWidth < 480 ? 10 : 15
            },
            grid: {
                display: false
            }
        }
    },
    plugins: {
        legend: {
            position: window.innerWidth < 768 ? 'bottom' : 'top',
            labels: {
                font: {
                    size: window.innerWidth < 768 ? 10 : 12
                },
                padding: window.innerWidth < 768 ? 8 : 10,
                boxWidth: window.innerWidth < 768 ? 12 : 15
            }
        },
        tooltip: {
            titleFont: {
                size: window.innerWidth < 768 ? 11 : 13
            },
            bodyFont: {
                size: window.innerWidth < 768 ? 10 : 12
            },
            padding: window.innerWidth < 768 ? 8 : 12
        }
    }
}
```

---

## Responsive SVG Containers

```css
/* Radar Chart */
.radar-container {
    position: relative;
    width: 100%;
    max-width: 600px;
    height: 600px;
    margin: 20px auto;
}

@media (max-width: 768px) {
    .radar-container {
        height: 400px;
        max-width: 100%;
    }
    
    .radar-container svg {
        max-width: 100%;
        height: auto;
    }
}

@media (max-width: 480px) {
    .radar-container {
        height: 300px;
    }
    
    .radar-label {
        font-size: 10px !important;
    }
}

/* Sunburst Chart */
.sunburst-container {
    position: relative;
    width: 100%;
    max-width: 400px;
    height: 400px;
    margin: 20px auto;
}

@media (max-width: 768px) {
    .sunburst-container {
        height: 300px;
        max-width: 100%;
    }
    
    .sunburst-container svg {
        max-width: 100%;
        height: auto;
    }
}

@media (max-width: 480px) {
    .sunburst-container {
        height: 250px;
    }
    
    .sunburst-text {
        font-size: 9px !important;
    }
}
```

---

## Touch-Friendly Buttons

```css
/* Base button styles */
.export-btn {
    background: var(--brand-primary);
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
}

/* Mobile touch target optimization */
@media (max-width: 768px) {
    .export-btn {
        font-size: 12px;
        padding: 10px 14px;
        min-height: 44px;
        min-width: 44px;
    }
    
    .theme-toggle {
        padding: 10px 16px;
        font-size: 13px;
        min-height: 44px;
    }
}
```

---

## Responsive Grid Layouts

```css
/* Auto-fit grid that stacks on mobile */
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    margin-bottom: 16px;
}

@media (max-width: 1024px) {
    .grid {
        grid-template-columns: 1fr;
        gap: 15px;
    }
}

/* Force single column on small mobile */
@media (max-width: 480px) {
    .team-capacity-grid {
        grid-template-columns: 1fr !important;
    }
}
```

---

## Responsive Tables

```css
/* Mobile table with horizontal scroll */
@media (max-width: 768px) {
    table {
        width: 100% !important;
        display: block;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        box-shadow: inset 0 -1px 0 var(--border-color);
    }
    
    .card table {
        min-width: 300px;
    }
    
    th, td {
        padding: 8px 6px;
        white-space: nowrap;
    }
    
    /* Sticky headers */
    @supports (position: sticky) {
        table thead {
            position: sticky;
            top: 0;
            background: var(--bg-secondary);
            z-index: 10;
        }
    }
    
    /* Visual scroll indicator */
    .card:has(table)::after {
        content: '← Scroll →';
        position: absolute;
        bottom: 10px;
        right: 10px;
        font-size: 11px;
        color: var(--text-muted);
        opacity: 0.6;
        pointer-events: none;
    }
}
```

---

## Progressive Typography

```css
/* Desktop */
.header h1 {
    font-size: 28px;
}

.card h2 {
    font-size: 16px;
}

.metric-value {
    font-size: 22px;
}

/* Tablet */
@media (max-width: 1024px) {
    .header h1 {
        font-size: 28px;
    }
    
    .card h2 {
        font-size: 20px;
    }
}

/* Mobile */
@media (max-width: 768px) {
    .header h1 {
        font-size: 24px;
    }
    
    .card h2 {
        font-size: 18px;
    }
    
    .metric-value {
        font-size: 24px;
    }
}

/* Small mobile */
@media (max-width: 480px) {
    .header h1 {
        font-size: 20px;
    }
    
    .card h2 {
        font-size: 16px;
    }
    
    .metric-value {
        font-size: 20px;
    }
}
```

---

## Responsive Heatmap

```css
.heatmap-calendar {
    display: grid;
    grid-template-columns: auto repeat(10, 1fr);
    gap: 4px;
    margin: 20px 0;
    overflow-x: auto;
}

@media (max-width: 1024px) {
    .heatmap-calendar {
        grid-template-columns: auto repeat(7, 1fr);
    }
}

@media (max-width: 768px) {
    .heatmap-calendar {
        grid-template-columns: auto repeat(5, 1fr);
        gap: 3px;
        font-size: 12px;
    }
    
    .heatmap-day-label {
        font-size: 10px;
        padding: 6px 8px;
    }
}

@media (max-width: 480px) {
    .heatmap-calendar {
        grid-template-columns: auto repeat(3, 1fr);
        gap: 2px;
    }
    
    .heatmap-cell {
        font-size: 8px;
    }
}
```

---

## Project Cards Mobile Layout

```css
.project-card {
    border: 2px solid var(--border-color);
    border-radius: 12px;
    padding: 18px;
    background: var(--bg-secondary);
    margin-bottom: 16px;
}

.project-card-header {
    display: flex;
    justify-content: space-between;
    align-items: start;
    margin-bottom: 12px;
}

@media (max-width: 768px) {
    .project-card {
        padding: 14px;
        margin-bottom: 14px;
    }
    
    .project-card-header {
        flex-direction: column;
        gap: 8px;
    }
    
    .project-card-title {
        font-size: 15px;
        line-height: 1.5;
        min-height: 44px;
        display: flex;
        align-items: center;
    }
}

@media (max-width: 480px) {
    .project-card {
        padding: 12px;
        margin-bottom: 12px;
    }
    
    .project-card-title {
        font-size: 14px;
    }
}
```

---

## Timeline Horizontal Scroll

```css
.timeline-container {
    margin: 15px 0;
    overflow: hidden;
}

@media (max-width: 768px) {
    .timeline-container {
        overflow-x: auto;
        padding-bottom: 10px;
        -webkit-overflow-scrolling: touch;
    }
    
    .timeline-row {
        min-width: 600px;
    }
    
    .timeline-project-col,
    .timeline-project-name {
        min-width: 120px;
        width: 120px;
    }
}
```

---

## JavaScript: Resize Handler

```javascript
// Handle window resize for responsive charts
let resizeTimeout;
window.addEventListener('resize', function() {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(function() {
        // Regenerate charts on orientation change
        if (window.capacityHistoryChart) {
            window.capacityHistoryChart.destroy();
        }
        
        // Trigger chart regeneration
        const event = new Event('DOMContentLoaded');
        document.dispatchEvent(event);
    }, 250);
});
```

---

## JavaScript: Touch Device Detection

```javascript
// Optimize touch interactions for mobile
if ('ontouchstart' in window) {
    document.body.classList.add('touch-device');
    
    // Improve chart tooltips for touch devices
    const style = document.createElement('style');
    style.textContent = `
        .touch-device .chart-container {
            -webkit-tap-highlight-color: transparent;
        }
        .touch-device canvas {
            touch-action: pan-y;
        }
    `;
    document.head.appendChild(style);
}
```

---

## Chart Container Sizing

```css
/* Desktop */
.chart-container {
    height: 300px;
    margin: 20px 0;
}

/* Mobile */
@media (max-width: 768px) {
    .chart-container {
        height: 250px;
        margin: 10px 0;
        width: 100% !important;
        max-width: 100% !important;
    }
    
    .chart-container canvas {
        max-width: 100% !important;
        height: auto !important;
    }
}

/* Small mobile */
@media (max-width: 480px) {
    .chart-container {
        height: 200px;
    }
}
```

---

## Progress Rings Mobile

```css
.progress-rings-container {
    display: flex;
    justify-content: space-around;
    flex-wrap: wrap;
    gap: 20px;
}

@media (max-width: 768px) {
    .progress-rings-container {
        flex-direction: column;
        align-items: center;
        gap: 20px;
    }
    
    .progress-ring {
        margin-bottom: 15px;
    }
}

@media (max-width: 480px) {
    .progress-ring {
        width: 100px;
        height: 100px;
    }
    
    .progress-ring-value {
        font-size: 16px;
    }
    
    .progress-ring-label {
        font-size: 9px;
    }
}
```

---

## Viewport Meta Tag

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

---

## Common Breakpoints Pattern

```css
/* Base/Desktop styles */
.element {
    /* Default desktop styles */
}

/* Tablet landscape */
@media (max-width: 1024px) {
    .element {
        /* Tablet landscape adjustments */
    }
}

/* Tablet portrait / Large mobile */
@media (max-width: 768px) {
    .element {
        /* Major mobile optimizations */
    }
}

/* Small mobile */
@media (max-width: 480px) {
    .element {
        /* Compact mobile styles */
    }
}
```

---

## Touch Target Best Practices

```css
/* Minimum 44x44px touch targets */
.interactive-element {
    min-height: 44px;
    min-width: 44px;
    padding: 10px 14px;
}

/* Spacing between adjacent targets (8px minimum) */
.button-group {
    gap: 8px;
}

/* Tap highlight removal (custom feedback instead) */
.touch-device * {
    -webkit-tap-highlight-color: transparent;
}
```

---

## Performance: Hardware Acceleration

```css
/* Trigger GPU acceleration for animations */
.animated-element {
    transform: translateZ(0);
    will-change: transform;
}

/* Remove will-change after animation */
.animated-element:not(:hover):not(:active) {
    will-change: auto;
}
```

---

Generated: January 29, 2026
