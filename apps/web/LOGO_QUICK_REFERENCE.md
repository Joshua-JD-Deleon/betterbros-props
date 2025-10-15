# BetterBros Logo - Quick Reference Guide

**One-Page Cheat Sheet for Developers & Designers**

---

## Logo Variations

```
FULL LOGO              COMPACT               ICON ONLY           WORDMARK
┌──────────────────┐   ┌──────────────┐      ┌────┐             ┌──────────┐
│ [🔷] BetterBros  │   │ [🔷] BetterBros│      │ 🔷 │             │BetterBros│
│   Smart Props    │   │              │      └────┘             └──────────┘
└──────────────────┘   └──────────────┘
Marketing/Docs         Headers/Nav           Favicons           Footer/Text
Min: 180px            Min: 140px            16-512px           Min: 100px
```

---

## Color Usage

### Dark Mode (Default)
```css
Logo Primary: #FFFFFF (white)
Logo Accent:  #10B981 (emerald green)
Background:   #0C1222 (deep navy) or transparent
```

### Light Mode
```css
Logo Primary: #1E40AF (royal blue)
Logo Accent:  #10B981 (emerald green)
Background:   #FFFFFF (white) or transparent
```

### When to Use Which Color
- **On dark backgrounds (< 50% luminance):** White logo
- **On light backgrounds (> 50% luminance):** Blue logo
- **Accent always stays:** Emerald green (#10B981)

---

## Sizing Scale

```
Component          Icon Size    Wordmark Size    Use Case
────────────────────────────────────────────────────────────
Mobile Header      24px         18px             Small screens
Desktop Header     32px         24px             Standard nav
Hero Section       48px         32px             Landing pages
Loading State      48px         —                Spinners
Favicon           16-32px       —                Browser tabs
App Icon          180-512px     —                Mobile apps
```

---

## Required Clear Space

```
  ← 32px →
  ┌───────────────┐  ↑
  │               │  32px
  │   [LOGO]      │  ↓
  │               │
  └───────────────┘

Clear space = height of the icon
No other elements should be closer than this distance
```

---

## Critical Do's and Don'ts

### DO:
✓ Use white logo on dark backgrounds
✓ Use blue logo on light backgrounds
✓ Maintain minimum sizes (140px+ for full logo)
✓ Keep clear space around logo
✓ Use vector (SVG) format when possible

### DON'T:
✗ Never stretch or distort the logo
✗ Never use logo smaller than minimums
✗ Never place on busy backgrounds without contrast
✗ Never rotate or skew the logo
✗ Never use unauthorized colors
✗ Never add effects (shadows, glows, outlines)

---

## Component Implementation

### Basic Usage
```tsx
import { Logo } from '@/components/brand/Logo';

// Standard header logo
<Logo variant="compact" size="md" />

// Mobile header
<Logo variant="compact" size="sm" />

// Icon only
<Logo variant="icon" size="md" />

// Full logo with tagline
<Logo variant="full" size="lg" showTagline />
```

### Props Reference
```typescript
variant: 'full' | 'compact' | 'icon' | 'wordmark'
theme: 'auto' | 'light' | 'dark' | 'monochrome'
size: 'sm' | 'md' | 'lg' | 'xl'
showTagline: boolean
```

---

## File Locations

```
/public/brand/logo/
  ├── svg/
  │   ├── betterbros-full-color.svg      ← Full logo
  │   ├── betterbros-white.svg           ← Dark mode
  │   ├── betterbros-dark.svg            ← Light mode
  │   └── betterbros-icon-color.svg      ← Icon only
  ├── favicon/
  │   ├── favicon.ico
  │   ├── favicon-16x16.png
  │   ├── favicon-32x32.png
  │   └── apple-touch-icon.png
  └── social/
      ├── og-image.png (1200×630)
      └── avatar-square.png (400×400)
```

---

## Context-Specific Sizes

| Context              | Format          | Size              |
|---------------------|-----------------|-------------------|
| Website Header      | Compact         | 32px icon, 200px  |
| Mobile Header       | Compact         | 24px icon, 140px  |
| Favicon             | Icon Only       | 16×16, 32×32px    |
| Apple Touch Icon    | Icon Only       | 180×180px         |
| Android Icon        | Icon Only       | 192×192, 512×512  |
| Open Graph          | Full Horizontal | 1200×630px        |
| Email Signature     | Compact         | 150px max         |
| Loading Spinner     | Icon Only       | 48×48px           |

---

## Accessibility Requirements

```
Minimum Contrast Ratios (WCAG 2.1 AA):
- Normal text: 4.5:1
- Large text: 3:1
- UI components: 3:1

Validated Combinations:
✓ White on Deep Navy (#FFFFFF / #0C1222): 18.47:1
✓ White on Royal Blue (#FFFFFF / #1E40AF): 8.59:1
✓ Royal Blue on White (#1E40AF / #FFFFFF): 8.59:1
✓ Emerald on Deep Navy (#10B981 / #0C1222): 7.23:1
```

---

## Common Scenarios

### Scenario 1: Adding logo to new page header
```tsx
<header className="flex h-16 items-center border-b bg-card px-6">
  <Logo variant="compact" size="md" />
  {/* Rest of header content */}
</header>
```

### Scenario 2: Creating loading state
```tsx
<div className="flex items-center justify-center h-screen">
  <div className="animate-pulse-soft">
    <Logo variant="icon" size="lg" />
  </div>
</div>
```

### Scenario 3: Responsive logo
```tsx
<Logo
  variant="compact"
  size={{ base: 'sm', md: 'md', lg: 'lg' }}
  className="hidden sm:flex"
/>
<Logo
  variant="icon"
  size="sm"
  className="sm:hidden"
/>
```

---

## Design Token Reference

```typescript
// Import and use design tokens
import { brandTokens } from '@/lib/brand/design-tokens';

const iconSize = brandTokens.logo.sizes.icon.md;  // 32
const primaryColor = brandTokens.logo.colors.primary.dark;  // #FFFFFF
```

---

## Contact for Logo Files

Need additional logo files or have questions?

1. Check `/public/brand/logo/` directory first
2. Review full guidelines in `LOGO_DESIGN_GUIDELINES.md`
3. For custom requests, document:
   - Format needed (SVG, PNG, etc.)
   - Size requirements
   - Use case
   - Background color

---

## Recommended Logo Concepts

**Top 3 Concepts for BetterBros:**

1. **"Data Bros" (Recommended)** - Stylized "BB" monogram with integrated upward arrow and chart elements
2. **"Smart Chart"** - Minimalist trending line graph forming stylized "B"
3. **"EV Plus"** - Mathematical "+" symbol representing positive expected value

See full guidelines document for complete concept descriptions and rationale.

---

## Quick Decision Tree

```
Need logo for...
│
├─ Website header?
│  └─ Use: variant="compact" size="md"
│
├─ Mobile app?
│  └─ Use: Icon only, 180×180 (iOS) or 192×192/512×512 (Android)
│
├─ Social media?
│  └─ Use: Icon only, 400×400 square
│
├─ Email/Marketing?
│  └─ Use: variant="full" with tagline
│
├─ Favicon?
│  └─ Use: Pre-generated favicon files in /public
│
└─ Loading state?
   └─ Use: variant="icon" size="lg" with animation
```

---

**For complete specifications, see:** `LOGO_DESIGN_GUIDELINES.md`

**Current Status:** Design phase - logo concepts pending selection and creation

**Version:** 1.0 | **Last Updated:** October 14, 2025
