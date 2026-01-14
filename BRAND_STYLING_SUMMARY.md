# Perimeter Church Brand Styling - Applied to Capacity Heatmaps

## Brand Guidelines Applied

Based on the Perimeter Church Brand Guidelines (06/01/2025), the following brand elements have been incorporated into the capacity tracking heatmaps:

---

## Color Palette

### Primary Colors (From Brand Guide)
- **Navy**: `#09243F` - Used for primary text and titles
- **Blue**: `#60BBE9` - Used for accents and highlights
- **Off-White**: `#f8f9fa` - Background color

### Applied In Heatmaps:
✅ **Main Title** - Navy (#09243F)
  - Phase name (e.g., "Combined - Team Capacity Calendar")
  - Serif font family (fallback for Freight DispPro)

✅ **Subtitle** - Navy (#09243F with 70% opacity)
  - Capacity metrics display
  - Sans-serif font family (fallback for Sweet Sans Pro)

✅ **Month Titles**
  - Current month: Brand Blue (#60BBE9) - Bold
  - Other months: Navy (#09243F) - Semibold

✅ **Day Numbers** - Navy (#09243F)
  - On light backgrounds
  - White on dark/saturated backgrounds

✅ **Weekday Labels** - Navy (#09243F with 60% opacity)
  - M, T, W, T, F, S, S

✅ **Colorbar**
  - Label: Navy (#09243F)
  - Ticks: Navy (#09243F with 70% opacity)
  - Outline: Brand Blue (#60BBE9)

### Heatmap Gradient (Unchanged for Data Readability)
🟢 **Light Green** (#e8f5e9) → **Green** (#81c784) → **Yellow** (#ffd54f) → **Orange** (#ff8a65) → **Red** (#ef5350)

**Rationale**: Green/yellow/red gradient maintained for universal understanding of capacity utilization (low → medium → high → over-capacity)

---

## Typography

### Primary Fonts (From Brand Guide)
- **Freight DispPro Book** - Headers and titles
- **Sweet Sans Pro Regular** - Body text and labels

### Applied In Heatmaps:
✅ **Title Text**
  - Font: Serif (system fallback for Freight DispPro)
  - Size: 24pt
  - Weight: Normal
  - Color: Navy (#09243F)

✅ **Subtitle Text**
  - Font: Sans-serif (system fallback for Sweet Sans Pro)
  - Size: 13pt
  - Color: Navy (#09243F, 70% opacity)

✅ **Month Titles**
  - Font: Sans-serif
  - Size: 13pt
  - Color: Brand Blue (#60BBE9) for current month, Navy (#09243F) for others

✅ **Calendar Labels**
  - Font: Sans-serif
  - Sizes: 9-11pt
  - Color: Navy (#09243F) with appropriate contrast

**Note**: Custom fonts (Freight DispPro, Sweet Sans Pro) require system installation. Current implementation uses serif/sans-serif fallbacks that match the brand aesthetic.

---

## Design Elements

### Background
✅ Off-white (#f8f9fa) - Clean, professional appearance matching brand guidelines

### Current Month Highlighting
✅ Current month title in **Brand Blue** (#60BBE9) - Bold
✅ Other months in **Navy** (#09243F) - Semibold

### Today's Date Highlighting
✅ Today's date shown in bold with slightly larger font
✅ Uses brand Navy color

### Calendar Borders
✅ Subtle borders in light gray
✅ Colorbar outline in Brand Blue (#60BBE9)

### Spacing & Layout
✅ Professional 12-month grid (4 rows × 3 columns)
✅ Optimized spacing between elements
✅ Clear visual hierarchy

---

## Files Updated

**Primary File**: `/Users/comstudio/Scripts/StudioProcesses/video_scorer.py`

**Sections Modified**:
1. **Figure Setup** (lines 787-790)
   - Perimeter brand styling comment added

2. **Title Styling** (lines 797-811)
   - Navy color (#09243F)
   - Serif font family (Freight DispPro fallback)
   - Brand-appropriate positioning

3. **Subtitle Styling** (lines 813-817)
   - Navy color with 70% opacity
   - Sans-serif font family (Sweet Sans Pro fallback)

4. **Day Number Text** (line 872)
   - Navy (#09243F) for day numbers on light backgrounds

5. **Month Title Colors** (lines 884-890)
   - Brand Blue (#60BBE9) for current month
   - Navy (#09243F) for other months

6. **Weekday Labels** (lines 892-895)
   - Navy (#09243F) with 60% opacity

7. **Colorbar Styling** (lines 907-914)
   - Labels and ticks in Navy (#09243F)
   - Outline in Brand Blue (#60BBE9)

---

## Heatmap Outputs

All heatmaps in `Reports/` folder now use Perimeter Church brand styling:

1. **Pre_heatmap_weighted.png** - Preproduction capacity
2. **Production_heatmap_weighted.png** - Production capacity
3. **Post_heatmap_weighted.png** - Post Production capacity
4. **Forecast_heatmap_weighted.png** - Forecast/Pipeline capacity
5. **Combined_heatmap_weighted.png** - All phases combined

---

## Brand Compliance

✅ **Primary Color Usage**: Navy (#09243F) for text hierarchy
✅ **Accent Color Usage**: Brand Blue (#60BBE9) for highlights
✅ **Background**: Off-white (#f8f9fa) for clean presentation
✅ **Typography**: Serif/sans-serif matching brand font families
✅ **Visual Hierarchy**: Clear, professional structure
✅ **Consistency**: Applied uniformly across all heatmap types
✅ **Data Readability**: Green/red gradient maintained for intuitive capacity understanding

---

## Optional Future Enhancements

If desired, the following additional brand elements could be added:

1. **Perimeter Logo**
   - Add logo to top-right or top-left corner
   - Logo file location: Extract from brand guide PDF

2. **Custom Font Installation**
   - Install Freight DispPro and Sweet Sans Pro system-wide
   - Update matplotlib font cache
   - Remove fallback fonts

3. **Brand Watermark**
   - Subtle "Perimeter Church" text at bottom
   - Maintains brand presence

4. **PowerPoint Export**
   - Generate PowerPoint-ready versions
   - Apply Perimeter PowerPoint template styling

---

## Testing & Verification

✅ **Script Execution**: Successfully runs without errors
✅ **Color Accuracy**: Brand colors (#09243F, #60BBE9) correctly applied
✅ **Font Fallbacks**: Serif/sans-serif fonts render appropriately
✅ **Visual Consistency**: All 5 heatmap types use unified styling
✅ **Readability**: Text remains clear and legible
✅ **Professional Appearance**: Clean, branded presentation suitable for leadership

---

## Maintenance

The brand styling is now integrated into the core heatmap generation logic. All future heatmaps will automatically use Perimeter Church brand colors and fonts.

**Cron Schedule**: Every 15 minutes (`*/15 * * * *`)
**Output Location**: `Reports/` folder
**Automatic Updates**: Yes - runs continuously via cron

---

## Contact

For questions about brand guidelines or additional customizations, contact:
- **Perimeter Communications Department**
- Brand Guidelines Version: 06/01/2025
