# NFL Props Analyzer - Styling Guide

## Overview

This guide covers the custom styling and theming implementation in the Streamlit app. The app uses a green-based color palette with a light theme, enforced via configuration and custom CSS.

## Theme Configuration

### Streamlit Config (`.streamlit/config.toml`)

```toml
[theme]
base="light"
primaryColor="#008057"
backgroundColor="#d9d8df"
secondaryBackgroundColor="#fafafa"
textColor="#484554"
```

**Key Points:**
- `base="light"` enforces light mode only
- Users cannot switch to dark mode
- Primary green color (#008057) used throughout the app

## Color Palette

### Core Colors

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| Primary Green | `#008057` | Primary actions, highlights |
| Background Grey | `#d9d8df` | Main app background |
| Secondary White | `#fafafa` | Card backgrounds, containers |
| Text Dark Grey | `#484554` | Primary text color |
| Action Primary | `#008057` | Buttons, interactive elements |
| Action Hover | `#006844` | Hover states (darker green) |
| Info Green | `#008057` | Informational elements |
| Border Light | `#e0e0e0` | Subtle borders, dividers |

### CSS Variables

Defined in `main.py` lines 542-558:

```css
:root {
    --color-primary: #008057;
    --color-background: #d9d8df;
    --color-background-secondary: #fafafa;
    --color-text: #484554;
    --color-border: #e0e0e0;
    --color-action-primary: #008057;
    --color-action-primary-hover: #006844;
    --color-info: #008057;
    --color-surface: #ffffff;
    --transition-fast: 0.2s ease;
    --transition-medium: 0.3s ease;
    --border-radius: 8px;
    --box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    --box-shadow-hover: 0 4px 8px rgba(0, 0, 0, 0.1);
}
```

## Custom CSS Components

### 1. Quick Actions Bar

**Location:** Lines 948-1002 in `main.py`

**Features:**
- Transparent buttons with green borders
- Hover effects with subtle background tint
- Smooth transitions
- Green border around entire bar

**CSS:**
```css
.quick-actions-wrapper {
    padding: 12px;
    margin-bottom: 20px;
    background-color: var(--color-background-secondary);
    border-radius: var(--border-radius);
    border: 2px solid var(--color-action-primary);
}

.quick-actions-wrapper button[data-testid="baseButton-primary"] {
    background-color: transparent !important;
    border: 2px solid var(--color-action-primary) !important;
    color: var(--color-action-primary) !important;
}

.quick-actions-wrapper button[data-testid="baseButton-primary"]:hover {
    background-color: rgba(51, 170, 119, 0.1) !important;
    transform: translateY(-1px);
}
```

### 2. Slider Styling

**Location:** Lines 588-633 in `main.py`

**Challenge:** Streamlit's BaseWeb sliders have multiple element states and wrapper levels requiring comprehensive CSS coverage.

**Features:**
- Green thumb (handle)
- Grey track background
- Green track fill (progress)
- Darker green on hover/active
- No red colors anywhere

**CSS Strategy:**
```css
/* Cover all slider instances with and without .stSlider wrapper */
div.stSlider div[data-baseweb="slider"] div[role="slider"],
div[data-baseweb="slider"] div[role="slider"] {
    background-color: var(--color-info) !important;
    border: 2px solid var(--color-info) !important;
}

/* Grey track */
div[data-baseweb="slider"] > div:first-child {
    background-color: #e0e0e0 !important;
}

/* Green fill */
div[data-baseweb="slider"] > div > div {
    background-color: var(--color-info) !important;
}

/* Interaction states */
div[data-baseweb="slider"] div[role="slider"]:hover {
    background-color: #006844 !important;
}
```

**Why `!important` is Necessary:**
Streamlit applies inline styles to BaseWeb components. To override these, `!important` is required. This is not a CSS best practice issue but a technical requirement for working with Streamlit's architecture.

### 3. Button Styling

**Location:** Lines 958-969 in `main.py`

**Features:**
- Consistent green theming
- Smooth hover transitions
- Proper focus states
- Subtle shadows

**CSS:**
```css
button[data-testid="baseButton-primary"] {
    background-color: var(--color-action-primary) !important;
    border: 2px solid var(--color-action-primary) !important;
    color: white !important;
    border-radius: var(--border-radius) !important;
    transition: all var(--transition-fast);
}

button[data-testid="baseButton-primary"]:hover {
    background-color: var(--color-action-primary-hover) !important;
    border-color: var(--color-action-primary-hover) !important;
    box-shadow: var(--box-shadow-hover);
}
```

### 4. Expanders

**Location:** Lines 717-785 in `main.py`

**Features:**
- Transparent backgrounds
- Green borders
- Hover effects
- Consistent spacing

**CSS:**
```css
div[data-testid="stExpander"] {
    background-color: transparent !important;
    border: 1px solid var(--color-border) !important;
    border-radius: var(--border-radius);
}

div[data-testid="stExpander"]:hover {
    border-color: var(--color-action-primary);
}

div[data-testid="stExpander"] > div[role="button"] {
    background-color: transparent !important;
    color: var(--color-text);
}
```

### 5. DataFrames and Tables

**Location:** Lines 882-918 in `main.py`

**Features:**
- Clean borders
- Striped rows for readability
- Hover highlighting
- Consistent spacing

**CSS:**
```css
div[data-testid="stDataFrame"] {
    border: 1px solid var(--color-border);
    border-radius: var(--border-radius);
}

div[data-testid="stDataFrame"] table {
    border-collapse: collapse;
}

div[data-testid="stDataFrame"] tbody tr:nth-child(even) {
    background-color: #f9f9f9;
}

div[data-testid="stDataFrame"] tbody tr:hover {
    background-color: rgba(0, 128, 87, 0.05);
}
```

### 6. Modals and Dialogs

**Location:** Lines 1003-1054 in `main.py`

**Features:**
- Centered layout
- Subtle shadows
- White backgrounds
- Smooth animations

**CSS:**
```css
div[data-testid="stModal"] {
    background-color: rgba(0, 0, 0, 0.5);
}

div[data-testid="stModal"] > div {
    background-color: var(--color-surface);
    border-radius: var(--border-radius);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
    max-width: 900px;
    margin: 40px auto;
}
```

### 7. Tabs

**Location:** Lines 1055-1096 in `main.py`

**Features:**
- Green active indicator
- Clean transitions
- Consistent spacing
- No redundant headers

**CSS:**
```css
div[data-testid="stTabs"] button[aria-selected="true"] {
    border-bottom: 2px solid var(--color-action-primary);
    color: var(--color-action-primary);
}

div[data-testid="stTabs"] button {
    color: var(--color-text);
    transition: all var(--transition-fast);
}

div[data-testid="stTabs"] button:hover {
    color: var(--color-action-primary);
}
```

## Typography

### Headers

**Standard Headers:**
- Use `st.markdown("**text**")` for consistent bold formatting
- Avoid `st.subheader()` which creates large grey backgrounds

**Example:**
```python
# Good - consistent sizing
st.markdown("**Performance Metrics**")

# Avoid - creates large grey background
st.subheader("Performance Metrics")
```

### Text Colors

All text uses the primary text color (#484554) defined in theme configuration. No manual color overrides needed.

## Icon Usage

**Current Policy:** No icons used in the app as of Phase 1 completion.

**Previous Icons Removed:**
- Button prefixes (↗, +)
- Trend chips (📈, 📉, ➡️)
- Badge prefixes (🟢, 🟡, 🔴)
- Slip headers (💎)

**Rationale:** Cleaner, more professional appearance with text-only labels.

## Browser Compatibility

### Hard Refresh Required

CSS changes may require hard refresh in browser:
- **Mac:** `Cmd + Shift + R`
- **Windows/Linux:** `Ctrl + Shift + F5`

### Tested Browsers

- Chrome 120+
- Firefox 120+
- Safari 17+
- Edge 120+

## Common Styling Patterns

### Adding New Buttons

```python
# Use type="primary" for green styling
st.button("Action", type="primary")

# For transparent with green border (in Quick Actions):
# Wrap in div with .quick-actions-wrapper class
```

### Adding New Expanders

```python
# Standard expander inherits theme automatically
with st.expander("Section Title"):
    st.write("Content")
```

### Adding New Sliders

```python
# Slider inherits green theme automatically
value = st.slider("Label", min_value=0, max_value=100)
```

## Troubleshooting

### CSS Not Applying

1. **Check Specificity:** Ensure your selector is specific enough
2. **Use !important:** Required for overriding Streamlit inline styles
3. **Hard Refresh:** Clear browser cache
4. **Check Console:** Look for CSS errors in browser dev tools
5. **Restart Server:** Clear Streamlit cache and restart

### Colors Not Matching

1. **Use CSS Variables:** Reference `var(--color-primary)` instead of hardcoding
2. **Check Theme Config:** Verify `.streamlit/config.toml` colors
3. **Inspect Element:** Use browser dev tools to see computed styles

### Hover States Not Working

1. **Check Transition:** Ensure `transition` property is set
2. **Verify Selector:** Make sure hover selector targets correct element
3. **Z-index Issues:** Check if another element is blocking interaction

## CSS Architecture

### File Organization

All CSS is contained in `main.py` in the `apply_theme_css()` function (lines 532-1147).

**Structure:**
1. CSS Variables (root)
2. Global Resets
3. Layout Components (sidebar, main content)
4. Interactive Elements (buttons, sliders, inputs)
5. Data Display (tables, charts, metrics)
6. Expanders and Containers
7. Modals and Dialogs
8. Tabs
9. Quick Actions Bar
10. Theme Chooser Hide (attempt)

### Naming Conventions

- Use `data-testid` selectors for Streamlit components
- Use class names for custom wrappers
- Prefer semantic variable names (`--color-action-primary` not `--green-1`)

## Performance Considerations

### CSS Optimization

- CSS is injected once per session
- Uses CSS variables for dynamic theming
- Minimal selector nesting for fast rendering
- No external CSS files (reduces HTTP requests)

### Browser Rendering

- Hardware-accelerated transitions via `transform`
- Avoid layout thrashing with `will-change` hints
- Use `contain` property for isolated components

## Future Enhancements

### Potential Additions

1. **Dark Mode Support:** Could add conditional CSS for dark theme
2. **Custom Animations:** Slide-in effects for modals and expanders
3. **Responsive Breakpoints:** Better mobile/tablet layouts
4. **Print Styles:** Optimized CSS for PDF export
5. **High Contrast Mode:** Accessibility enhancement

### Design Tokens

Consider extracting all design decisions to a separate config:
```python
DESIGN_TOKENS = {
    'colors': {...},
    'spacing': {...},
    'typography': {...},
    'shadows': {...},
    'transitions': {...}
}
```

## Related Documentation

- **Main README:** `./README.md` - App overview and features
- **Changelog:** `./CHANGELOG.md` - Phase 1 styling changes
- **Streamlit Docs:** https://docs.streamlit.io/library/api-reference/utilities/st.set_page_config

## Support

For styling issues:
1. Check browser console for CSS errors
2. Use browser dev tools to inspect elements
3. Reference this guide for component-specific patterns
4. Review `apply_theme_css()` function in `main.py`
