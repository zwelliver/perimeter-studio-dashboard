# Mobile Dashboard Testing Checklist

Use this checklist to verify all mobile optimizations are working correctly.

---

## Device Testing

### Screen Sizes to Test

- [ ] iPhone SE (375x667) - Small mobile
- [ ] iPhone 12/13 Pro (390x844) - Standard mobile
- [ ] iPhone 14 Pro Max (430x932) - Large mobile
- [ ] iPad Mini (768x1024) - Small tablet
- [ ] iPad Pro (1024x1366) - Large tablet
- [ ] Android phones (various sizes)

### Orientation Testing

- [ ] Portrait mode - All features work
- [ ] Landscape mode - Layout adjusts properly
- [ ] Rotation - Charts regenerate correctly
- [ ] No horizontal overflow in either orientation

---

## Visual & Layout Tests

### Header Section

- [ ] Logo/title visible and properly sized
- [ ] Theme toggle button is at least 44x44px
- [ ] Export buttons are at least 44x44px  
- [ ] Buttons don't overlap with title
- [ ] Controls stack properly on small screens
- [ ] Padding allows comfortable touch targets

### Card Layout

- [ ] Cards stack vertically on mobile (768px)
- [ ] Cards have adequate padding (15px mobile, 12px small)
- [ ] Card titles are readable (18px mobile, 16px small)
- [ ] No card content overflow
- [ ] Margins between cards appropriate

### Typography

- [ ] H1 size: 24px on mobile, 20px on small mobile
- [ ] H2 size: 18px on mobile, 16px on small mobile
- [ ] Body text: minimum 14px
- [ ] All text is legible without zoom
- [ ] Line heights provide comfortable reading

---

## Chart Testing

### Line Charts (Trends & Capacity)

- [ ] Charts resize to container width
- [ ] Chart height appropriate (250px mobile, 200px small)
- [ ] Legend moves to bottom on mobile
- [ ] Legend items readable (10-12px font)
- [ ] X-axis labels rotate 90° on mobile
- [ ] Y-axis shows 6 ticks max on mobile
- [ ] Tooltips appear on touch
- [ ] Tooltips sized appropriately for mobile
- [ ] Grid lines visible but not cluttered
- [ ] No chart distortion or cutoff

### SVG Charts (Radar, Sunburst)

- [ ] Radar chart: 400px on tablet, 300px on mobile
- [ ] Sunburst chart: 300px on tablet, 250px on mobile
- [ ] Labels readable (10px mobile)
- [ ] SVG scales proportionally
- [ ] No overflow outside container
- [ ] Interactive elements respond to touch

### Heatmap Calendar

- [ ] Columns reduce on smaller screens
  - [ ] 10 cols desktop
  - [ ] 7 cols tablet (1024px)
  - [ ] 5 cols mobile (768px)
  - [ ] 3 cols small mobile (480px)
- [ ] Cell text readable
- [ ] Gaps appropriate (4px → 3px → 2px)
- [ ] Horizontal scroll if needed
- [ ] Touch/tap on cells works

---

## Touch Interaction Tests

### Buttons & Controls

- [ ] All buttons minimum 44x44px
- [ ] 8px minimum spacing between buttons
- [ ] Buttons respond to touch immediately
- [ ] No double-tap zoom on buttons
- [ ] Active/pressed state visible
- [ ] Focus indicators work with keyboard

### Links & Navigation

- [ ] Project card links are tappable
- [ ] Links have 44px min-height
- [ ] No accidental taps on adjacent links
- [ ] External links open correctly

### Chart Interactions

- [ ] Chart tooltips work on tap
- [ ] Can pan/scroll charts horizontally if needed
- [ ] Pinch-to-zoom disabled on charts
- [ ] Chart legends respond to touch
- [ ] No touch lag or delay

---

## Scrolling & Overflow

### Vertical Scrolling

- [ ] Smooth scrolling throughout page
- [ ] Sticky headers work (if implemented)
- [ ] No bounce/rubber-band issues
- [ ] Scroll position maintained on rotate

### Horizontal Scrolling

- [ ] Tables scroll horizontally
- [ ] Timeline scrolls horizontally
- [ ] Scroll indicator visible ("← Scroll →")
- [ ] Touch scrolling smooth (-webkit-overflow-scrolling)
- [ ] Can scroll to end of content

### Tables

- [ ] Tables have horizontal scroll
- [ ] Headers sticky on scroll (if supported)
- [ ] All columns accessible
- [ ] Text doesn't wrap mid-word
- [ ] Minimum width enforced (300px)

---

## Team Capacity Section

- [ ] Progress bars full width
- [ ] Progress bars minimum 25px height
- [ ] Percentages visible inside bars
- [ ] Team member names readable (16px mobile)
- [ ] Capacity text clear (14px mobile)
- [ ] Grid stacks to single column on phones
- [ ] Background colors sufficient contrast

---

## Progress Rings

- [ ] Rings stack vertically on mobile
- [ ] Ring size: 140px desktop, 100px small mobile
- [ ] Values readable (24px → 16px)
- [ ] Labels readable (10px → 9px)
- [ ] Centered alignment
- [ ] Gap between rings (20px)
- [ ] Animation smooth

---

## Project Cards (Shoots, Deadlines, Forecast)

- [ ] Cards stack vertically
- [ ] Header switches to column layout on mobile
- [ ] Badges visible and readable
- [ ] Date/time prominent
- [ ] Title is tappable link
- [ ] Min-height 44px for title link
- [ ] Details text readable (14px → 13px)
- [ ] Card padding appropriate
- [ ] Borders visible

---

## Timeline Visualization

- [ ] Horizontal scroll enabled
- [ ] Project names fixed (120px width)
- [ ] Timeline bars visible
- [ ] Dates readable
- [ ] Min-width 600px enforced
- [ ] Smooth touch scrolling
- [ ] Can see full timeline by scrolling

---

## Performance Tests

### Load Time

- [ ] Initial render < 3 seconds
- [ ] Charts appear progressively
- [ ] No layout shift during load
- [ ] Smooth transitions

### Scroll Performance

- [ ] 60fps scrolling
- [ ] No jank or stutter
- [ ] Tables scroll smoothly
- [ ] Timeline scroll smooth

### Interaction Response

- [ ] Touch response < 100ms
- [ ] Button feedback immediate
- [ ] Chart tooltips appear quickly
- [ ] Theme toggle instant

### Resize/Rotate

- [ ] Charts regenerate within 250ms
- [ ] No memory leaks
- [ ] Layout recalculates correctly
- [ ] Content doesn't flash

---

## Browser Compatibility

### iOS Safari

- [ ] All features work
- [ ] Charts render correctly
- [ ] Touch scrolling smooth
- [ ] Buttons respond properly
- [ ] No webkit-specific issues

### Chrome Mobile

- [ ] All features work
- [ ] Charts render correctly
- [ ] Touch interactions smooth
- [ ] Tooltips work

### Firefox Mobile

- [ ] All features work
- [ ] Charts render correctly
- [ ] Layout correct
- [ ] No Firefox-specific issues

### Samsung Internet

- [ ] Basic functionality works
- [ ] Charts visible
- [ ] Touch works
- [ ] Layout acceptable

---

## Accessibility (Mobile)

### Touch Targets

- [ ] All interactive elements ≥ 44x44px
- [ ] Adequate spacing (≥ 8px)
- [ ] No overlapping touch targets

### Color & Contrast

- [ ] Sufficient color contrast (4.5:1 text)
- [ ] Dark mode works on mobile
- [ ] Theme toggle accessible

### Screen Reader

- [ ] ARIA labels present
- [ ] Focus order logical
- [ ] Chart data accessible

### Keyboard (External)

- [ ] Tab navigation works
- [ ] Focus indicators visible
- [ ] Can access all features

---

## Edge Cases

### Small Screens (<375px)

- [ ] Content still accessible
- [ ] No critical features hidden
- [ ] Text still readable
- [ ] Buttons still tappable

### Large Screens (Tablets)

- [ ] Layout uses space efficiently
- [ ] Not overly stretched
- [ ] Readable at arm's length

### Slow Connections

- [ ] Dashboard loads progressively
- [ ] Charts don't block rendering
- [ ] Fallback content shown

### Low Memory Devices

- [ ] Charts load without crash
- [ ] No memory warnings
- [ ] Smooth after prolonged use

---

## Data Validation

### Empty States

- [ ] Proper messaging when no data
- [ ] Charts handle empty data gracefully
- [ ] No errors in console

### Large Datasets

- [ ] Charts handle many data points
- [ ] Tables scroll properly with many rows
- [ ] Performance acceptable

### Edge Values

- [ ] Handles 0% capacity
- [ ] Handles >100% capacity
- [ ] Negative values handled
- [ ] Very large numbers formatted

---

## Dark Mode (Mobile)

- [ ] Dark mode toggle works
- [ ] Charts update colors
- [ ] Text remains readable
- [ ] Sufficient contrast maintained
- [ ] Theme persists on reload
- [ ] Works in both orientations

---

## Network Conditions

### Offline

- [ ] Graceful degradation
- [ ] Cached version loads
- [ ] Error messaging clear

### Slow 3G

- [ ] Progressive enhancement
- [ ] Critical content loads first
- [ ] No timeouts

---

## Issue Tracking

Use this section to note any issues found:

### Critical Issues
- 

### Medium Issues
- 

### Minor Issues
- 

### Enhancement Ideas
- 

---

## Sign-off

Tested by: __________________  
Date: __________________  
Devices tested: __________________  
Overall Status: [ ] Pass [ ] Fail [ ] Conditional Pass

Notes:
_______________________________________
_______________________________________
_______________________________________

---

Generated: January 29, 2026
