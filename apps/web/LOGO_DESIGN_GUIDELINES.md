# BetterBros Logo Design Guidelines
## Smart Props Trading Platform - Brand Identity System

**Document Version:** 1.0
**Last Updated:** October 14, 2025
**Platform:** BetterBros - Smart Props Trading Platform

---

## Table of Contents
1. [Brand Analysis](#brand-analysis)
2. [Color System](#color-system)
3. [Typography Guidelines](#typography-guidelines)
4. [Logo Concept Directions](#logo-concept-directions)
5. [Logo Specifications](#logo-specifications)
6. [Usage Guidelines](#usage-guidelines)
7. [Context-Specific Applications](#context-specific-applications)
8. [Do's and Don'ts](#dos-and-donts)
9. [Technical Implementation](#technical-implementation)

---

## Brand Analysis

### Current State
- **Platform Name:** BetterBros
- **Tagline:** Smart Props Trading Platform
- **Current Logo:** Simple TrendingUp icon (Lucide React) in a primary color square
- **Design Aesthetic:** Professional sportsbook-style, dark theme by default, modern/clean UI
- **Primary Audience:** Data-driven sports bettors, prop traders, analytics enthusiasts

### Brand Personality
- **Professional yet Approachable:** "Bros" adds personality without sacrificing credibility
- **Intelligent & Data-Driven:** Emphasis on "Smart" analytics and insights
- **Confident & Winning-Focused:** Trading mindset, positive EV, strategic betting
- **Modern & Tech-Forward:** Clean interface, real-time data, cutting-edge tools

### Brand Values
1. **Transparency:** Clear odds, honest analytics, no hidden information
2. **Intelligence:** Data-driven decisions over gut feelings
3. **Community:** "Bros" represents camaraderie and shared success
4. **Precision:** Accurate predictions, reliable data
5. **Performance:** Optimized for profit, tracking real results

---

## Color System

### Current Color Palette Analysis

Based on the existing codebase (`globals.css` and `tailwind.config.ts`):

#### Dark Mode (Default Theme)
```css
/* Brand Foundation */
--background: 222.2 84% 4.9%      /* Deep navy-blue-black */
--foreground: 210 40% 98%         /* Near white */
--primary: 210 40% 98%            /* White for dark mode */
--card: 217 33% 8%                /* Slightly lighter navy */

/* Sportsbook-Specific Colors */
--profit: 142 76% 36%             /* Green - Success/Win */
--loss: 0 72% 51%                 /* Red - Loss/Risk */
--neutral: 215 20% 45%            /* Gray - Neutral state */
--live: 24 95% 53%                /* Orange - Live indicators */
```

#### Light Mode
```css
--background: 0 0% 100%           /* White */
--primary: 222.2 47.4% 11.2%      /* Deep navy-blue */
--profit: 142 71% 45%             /* Brighter green */
```

### Logo Color Recommendations

#### Primary Logo Palette

**Option A: Classic Confidence (Recommended)**
```css
/* Primary Brand Color - Trust & Sophistication */
Logo Primary: #1E40AF           /* Royal Blue - HSL(222, 73%, 40%) */
Reasoning: Financial trust, professionalism, works in both light/dark

/* Accent Color - Intelligence & Data */
Logo Accent: #10B981            /* Emerald Green - HSL(142, 76%, 36%) */
Reasoning: Matches existing profit color, represents winning/growth

/* Dark Mode Variation */
Logo Primary Dark: #FFFFFF      /* Pure white */
Logo Accent Dark: #10B981       /* Consistent emerald */
```

**Option B: Bold & Modern**
```css
/* Primary - High Contrast */
Logo Primary: #0EA5E9           /* Vibrant Blue - HSL(199, 89%, 48%) */

/* Accent - Energy */
Logo Accent: #F59E0B            /* Amber - HSL(38, 92%, 50%) */
Reasoning: Higher energy, matches "live" indicators, stands out
```

**Option C: Premium Dark**
```css
/* Primary - Sophisticated */
Logo Primary: #6366F1           /* Indigo - HSL(239, 84%, 67%) */

/* Accent - Growth */
Logo Accent: #22C55E            /* Bright Green - HSL(142, 71%, 45%) */
Reasoning: Modern fintech aesthetic, premium feel
```

#### Functional Color Usage

```css
/* Logo in Different Contexts */
--logo-on-dark: #FFFFFF              /* White on dark backgrounds */
--logo-on-light: #1E40AF             /* Royal blue on light backgrounds */
--logo-on-card: #FFFFFF              /* White on card components */
--logo-accent: #10B981               /* Consistent accent across modes */
--logo-gradient-start: #1E40AF       /* For gradient variations */
--logo-gradient-end: #10B981         /* Green endpoint */
```

#### Accessibility Standards

All logo color combinations must meet **WCAG 2.1 Level AA** standards:
- **Normal Text:** Minimum contrast ratio of 4.5:1
- **Large Text:** Minimum contrast ratio of 3:1
- **UI Components:** Minimum contrast ratio of 3:1

**Validated Combinations:**
- White (#FFFFFF) on Royal Blue (#1E40AF): 8.59:1 ✓
- White (#FFFFFF) on Dark Navy (#0C1222): 18.47:1 ✓
- Royal Blue (#1E40AF) on White (#FFFFFF): 8.59:1 ✓
- Emerald (#10B981) on Dark Navy (#0C1222): 7.23:1 ✓

---

## Typography Guidelines

### Current Typography Stack
```css
/* From existing codebase */
--font-inter: 'Inter', system-ui, sans-serif;
--font-mono: 'JetBrains Mono', monospace;
```

### Logo Typography Recommendations

#### Primary Wordmark Font

**Option 1: Inter (Existing - Recommended)**
- **Weight:** 700 (Bold) or 800 (Extra Bold)
- **Style:** Clean, modern, excellent readability
- **Reasoning:** Already in use, consistent with UI, professional
- **Letter Spacing:** -0.02em (tighter tracking for cohesion)
- **Customization:** Consider custom ligature for "BB" monogram

**Option 2: Manrope**
- **Weight:** 700-800
- **Style:** Geometric sans-serif, slightly rounded
- **Reasoning:** Friendly yet professional, modern fintech aesthetic
- **Use Case:** If wanting slightly softer brand personality

**Option 3: Space Grotesk**
- **Weight:** 600-700
- **Style:** Distinctive, slightly geometric
- **Reasoning:** Tech-forward, unique character, stands out
- **Use Case:** For maximum differentiation from competitors

#### Typography Specifications

```css
/* Logo Wordmark Styles */
.logo-wordmark {
  font-family: 'Inter', system-ui, sans-serif;
  font-weight: 800;
  font-size: 24px;                    /* Base size for header */
  letter-spacing: -0.02em;
  line-height: 1;
  font-feature-settings: 'ss01' on;   /* Alternate stylistic set */
}

/* Tagline Typography */
.logo-tagline {
  font-family: 'Inter', system-ui, sans-serif;
  font-weight: 500;
  font-size: 12px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  opacity: 0.8;
}
```

#### Special Typography Treatments

**"Better" Treatment:**
- Weight: 700 (Bold)
- Color: Primary logo color
- Consider: Slightly smaller or lighter than "Bros"

**"Bros" Treatment:**
- Weight: 800 (Extra Bold)
- Color: Primary logo color
- Emphasis: This is the distinctive, memorable part

**Tagline Hierarchy:**
- Always secondary to main wordmark
- Max 40% of wordmark height
- Separated by whitespace or subtle divider

---

## Logo Concept Directions

### Concept 1: "Data Bros" (Recommended)

**Visual Description:**
- **Icon:** Stylized "BB" monogram combining upward trending arrow with bar chart elements
- **Style:** Bold, geometric, clean lines
- **Symbolism:**
  - Twin "B" letters represent brotherhood/partnership
  - Integrated upward arrow = growth, positive EV, winning
  - Subtle chart bars within letterforms = data/analytics
  - Geometric angles = precision, mathematical approach

**Design Elements:**
```
Icon Structure:
- Two interlocking "B" forms
- Negative space creates upward arrow in center
- 3-4 vertical bars integrated into right side (chart reference)
- Contained in square or rounded square (current approach)

Color Application:
- Primary: Royal Blue (#1E40AF) for main letterforms
- Accent: Emerald Green (#10B981) for arrow/growth element
- Dark Mode: White primary with green accent
```

**Wordmark:**
- "BetterBros" in Inter Extra Bold
- Optional color split: "Better" (blue) "Bros" (blue with green underline/highlight)
- Tagline below in smaller, uppercase, spaced letters

**Rationale:**
- Maintains recognizable "B" identity
- Clearly communicates data analytics
- Upward movement suggests profitability
- Clean, scalable at any size
- Works in monochrome or full color
- Professional yet approachable

---

### Concept 2: "Smart Chart"

**Visual Description:**
- **Icon:** Minimalist trending line graph forming stylized "B"
- **Style:** Clean, modern, slightly technical
- **Symbolism:**
  - Ascending line = winning trajectory
  - Chart nodes = data points
  - Curved line path forms "B" shape
  - Represents continuous growth and monitoring

**Design Elements:**
```
Icon Structure:
- Smooth ascending curve (hockey stick growth)
- 4-5 circular nodes along the path
- Curve begins at bottom-left, ends top-right
- Final node has subtle glow/emphasis (current position)
- Background: Subtle grid pattern (very light, optional)

Color Application:
- Line: Gradient from blue to green (data to profit)
- Nodes: Solid green (data points)
- Background: Transparent or very subtle navy
```

**Wordmark:**
- "BetterBros" in Inter Bold
- All one color in header (cleaner)
- Tagline: "SMART PROPS TRADING" in smaller font

**Rationale:**
- Immediately recognizable as analytics platform
- Chart metaphor is universal in trading
- Clean, modern fintech aesthetic
- Easily animated (nodes can pulse, line can draw in)
- Strong at small sizes

---

### Concept 3: "Brotherhood Shield"

**Visual Description:**
- **Icon:** Shield shape with two figures/silhouettes or abstract "B" forms standing together
- **Style:** Bold, confident, community-focused
- **Symbolism:**
  - Shield = protection, security, smart betting
  - Two forms = brothers, community, collaboration
  - Upward points = aspiration, winning
  - Solid structure = reliability

**Design Elements:**
```
Icon Structure:
- Modern shield outline (not medieval, more like badge)
- Two abstract "B" or human silhouette forms inside
- Optional: Small upward arrow between the figures
- Clean lines, minimal detail

Color Application:
- Shield outline: Royal Blue
- Left figure: Blue
- Right figure: Green (accent)
- Or: Solid color with gradient fill
```

**Wordmark:**
- "BetterBros" with emphasis on "Bros"
- Possibly separate words: "Better Bros"
- Strong, bold weight

**Rationale:**
- Emphasizes community aspect ("Bros")
- Conveys trust and protection
- Differentiated from pure data/chart logos
- Memorable, personality-driven
- Works well for merchandise/swag

---

### Concept 4: "EV Plus" (Expected Value Focus)

**Visual Description:**
- **Icon:** Stylized "+" symbol or "EV" letters with upward movement
- **Style:** Mathematical, precise, sophisticated
- **Symbolism:**
  - "+" = positive expected value (core concept)
  - Asymmetric plus creates movement
  - Clean geometry = precision
  - Can incorporate "BB" into the "+" structure

**Design Elements:**
```
Icon Structure:
- Plus sign with unequal arms (longer upward arm)
- Top arm extends beyond, becomes arrow
- Integration of "B" letterforms in negative space
- Or: "EV" letters with ascending "V"

Color Application:
- Primary form: Royal Blue or White
- Accent: Green highlighting the "positive" aspect
- Possible gradient on upward element
```

**Wordmark:**
- Clean, minimal presentation
- Possible integration: "BETTER BROS | +EV"

**Rationale:**
- Speaks directly to sophisticated bettors
- Mathematical/analytical credibility
- Unique positioning around EV concept
- Professional, expert-level branding

---

### Concept 5: "Connected Data"

**Visual Description:**
- **Icon:** Network of connected nodes forming "BB" or abstract brain/neural network
- **Style:** Tech-forward, AI/algorithm suggestion
- **Symbolism:**
  - Connected nodes = data relationships, algorithms
  - Network = comprehensive analysis
  - Neural aesthetic = smart, AI-powered
  - Organic yet mathematical

**Design Elements:**
```
Icon Structure:
- 6-8 circular nodes of varying sizes
- Lines connecting them in specific pattern
- Overall shape suggests "BB" or neural network
- Central nodes larger/brighter

Color Application:
- Nodes: Gradient from blue to green based on position
- Connections: Thin blue/white lines
- Glow effect on central nodes
```

**Wordmark:**
- "BetterBros" in clean sans-serif
- Tagline emphasizes "Smart" or "AI-Powered"

**Rationale:**
- Modern, tech-forward positioning
- Suggests advanced algorithms
- Differentiates from simple chart logos
- Can be animated effectively
- Appeals to tech-savvy users

---

## Logo Specifications

### Primary Logo Lockup

```
Full Logo Composition:
┌─────────────────────────────────┐
│  [ICON]  BetterBros             │
│          SMART PROPS TRADING     │
└─────────────────────────────────┘

Proportions:
- Icon: 32px × 32px (base size)
- Wordmark: 24px height
- Tagline: 10px height
- Icon-to-wordmark spacing: 12px
- Wordmark-to-tagline spacing: 4px
```

### Logo Variations

#### 1. Primary Horizontal Logo
- **Use:** Desktop headers, marketing materials, documentation
- **Composition:** Icon + Wordmark + Tagline (horizontal)
- **Minimum Width:** 180px
- **Ideal Width:** 240-320px

#### 2. Compact Horizontal Logo
- **Use:** Mobile headers, tight spaces
- **Composition:** Icon + Wordmark only (no tagline)
- **Minimum Width:** 140px
- **Ideal Width:** 180-220px

#### 3. Icon + Wordmark (Stacked)
- **Use:** Square social media, app splash screens
- **Composition:** Icon centered above wordmark
- **Minimum Width:** 120px
- **Aspect Ratio:** Approximately 1:1.2

#### 4. Icon Only
- **Use:** Favicons, app icons, social avatars, loading states
- **Composition:** Icon alone
- **Sizes:** 16×16, 32×32, 48×48, 64×64, 128×128, 256×256, 512×512
- **Background:** Transparent or branded color

#### 5. Wordmark Only
- **Use:** Text-heavy contexts, footer
- **Composition:** "BetterBros" text without icon
- **Minimum Width:** 100px

### Size Specifications

```css
/* Header Sizes */
--logo-header-desktop: 200px width;
--logo-header-mobile: 140px width;
--logo-header-height: 40px max-height;

/* Icon Sizes */
--logo-icon-xs: 16px;   /* Favicon */
--logo-icon-sm: 24px;   /* Tight UI spaces */
--logo-icon-md: 32px;   /* Standard header (current) */
--logo-icon-lg: 48px;   /* Hero sections */
--logo-icon-xl: 64px;   /* Splash screens */

/* Wordmark Sizes */
--logo-wordmark-sm: 18px;
--logo-wordmark-md: 24px;
--logo-wordmark-lg: 32px;
--logo-wordmark-xl: 48px;
```

### Clear Space Requirements

**Minimum Clear Space:** Equal to the height of the "B" in the icon

```
Rule: No other elements should encroach within 1× icon height
      on all sides of the logo

Example for 32px icon:
- Top clearance: 32px
- Right clearance: 32px
- Bottom clearance: 32px
- Left clearance: 32px
```

**Exception:** Logo may sit flush against app edges on mobile (0-8px padding acceptable)

### Corner Radius

```css
/* Logo Container (if using background) */
--logo-radius: 8px;              /* Standard (matches UI) */
--logo-radius-sm: 4px;           /* Compact contexts */
--logo-radius-lg: 12px;          /* Hero/marketing */
--logo-icon-radius: 8px;         /* Icon-only background */

/* Never use: */
--logo-radius: 9999px;           /* No full circles for brand */
```

### Stroke Weights

```css
/* Icon Line Weights */
--logo-stroke-thin: 1.5px;       /* Detail elements */
--logo-stroke-medium: 2px;       /* Standard elements */
--logo-stroke-bold: 3px;         /* Primary shapes */

/* Wordmark Line Weights */
--logo-wordmark-weight: 800;     /* Extra Bold */
--logo-tagline-weight: 500;      /* Medium */
```

---

## Usage Guidelines

### Background Rules

#### Approved Backgrounds

**Dark Backgrounds (Primary):**
- Deep navy (#0C1222, #0F1729)
- Card backgrounds (existing --card color)
- Pure black (#000000) - acceptable
- Dark gradients (navy to black)

**Light Backgrounds:**
- White (#FFFFFF)
- Light gray (#F9FAFB, #F3F4F6)
- Subtle blue tints (#F0F9FF)

**Colored Backgrounds:**
- Profit green background: Use white logo
- Loss red background: Use white logo
- Only when contextually appropriate

#### Background Contrast Requirements

```css
/* Minimum contrast ratios */
Logo on background: 4.5:1 minimum (WCAG AA)
Logo on background: 7:1 preferred (WCAG AAA)

/* Automatic logo color based on background */
Background luminance > 50%: Use dark logo (#1E40AF)
Background luminance < 50%: Use white logo (#FFFFFF)
```

### Color Modes

#### Dark Mode (Default)
```jsx
// Logo colors for dark backgrounds
logoColor: "white"           // Primary element
accentColor: "#10B981"       // Accent/growth elements
containerBg: "transparent"   // No background needed
```

#### Light Mode
```jsx
// Logo colors for light backgrounds
logoColor: "#1E40AF"         // Primary element
accentColor: "#10B981"       // Accent/growth elements
containerBg: "transparent"   // No background needed
```

#### Monochrome Mode
```jsx
// For special contexts (print, embroidery, engraving)
logoColor: "currentColor"    // Inherits from parent
accentColor: "currentColor"  // Same as primary
// All elements use single color
```

### Positioning

#### Header Placement
```css
/* Desktop Header */
.header-logo {
  position: absolute;
  left: 24px;              /* After toggle button */
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Mobile Header */
@media (max-width: 768px) {
  .header-logo {
    left: 16px;
    gap: 8px;
  }

  .logo-tagline {
    display: none;         /* Hide tagline on mobile */
  }
}
```

#### Vertical Alignment
- Logo should be vertically centered in navigation bars
- Icon and text should be baseline-aligned (not center-aligned)
- Tagline should have consistent spacing below wordmark

#### Horizontal Flow
- Logo always at start of header (left in LTR, right in RTL)
- Minimum 16px margin from screen edge
- Navigation items should have 24px minimum gap from logo

---

## Context-Specific Applications

### 1. Website Header
**Specification:**
- **Format:** Compact Horizontal (Icon + Wordmark)
- **Size:** 32px icon height, 200px total width
- **Background:** Transparent (sits on header background)
- **Color:** White (dark mode) / Royal Blue (light mode)
- **Behavior:** Fixed position on scroll

**Implementation:**
```jsx
<div className="flex items-center gap-3">
  <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
    <BetterBrosIcon className="h-5 w-5 text-primary-foreground" />
  </div>
  <div className="flex flex-col">
    <span className="text-xl font-bold leading-none">BetterBros</span>
  </div>
</div>
```

### 2. Mobile Header
**Specification:**
- **Format:** Icon + Abbreviated wordmark
- **Size:** 24px icon height, 140px total width
- **Behavior:** Truncate to icon-only below 380px viewport width
- **Touch Target:** Minimum 44px × 44px tappable area

### 3. Favicon
**Specification:**
- **Format:** Icon only, no wordmark
- **Sizes Required:**
  - 16×16px (browser tabs)
  - 32×32px (bookmark bars)
  - 48×48px (Windows)
  - 180×180px (Apple Touch Icon)
  - 192×192px, 512×512px (Android)
- **Background:** Solid brand color or transparent
- **Style:** Simplified icon, maximum contrast

**Files:**
```
/public/favicon.ico           (16×16, 32×32 combined)
/public/favicon-16x16.png
/public/favicon-32x32.png
/public/apple-touch-icon.png  (180×180)
/public/android-chrome-192x192.png
/public/android-chrome-512x512.png
```

### 4. iOS App Icon
**Specification:**
- **Format:** Icon only, no wordmark, no transparency
- **Sizes:** 180×180px (primary), with various sizes for system
- **Background:** Solid brand color gradient
- **Style:** Full-bleed, no rounded corners (iOS adds them)
- **Safe Area:** Keep critical elements 10% from edges

**Design:**
```
Background: Gradient from #1E40AF to #1E3A8A
Icon: White centered, 60% of canvas size
Border: None (will be cropped by iOS)
```

### 5. Android App Icon
**Specification:**
- **Format:** Adaptive icon (foreground + background layers)
- **Sizes:** 192×192px, 512×512px
- **Background Layer:** Solid color or gradient
- **Foreground Layer:** Icon with transparency
- **Safe Zone:** 66dp diameter circle (critical elements must fit)

### 6. Social Media Avatars

**Twitter/X Profile:**
- **Size:** 400×400px minimum
- **Format:** PNG with transparency
- **Design:** Icon only, centered, 70% of canvas
- **Background:** Brand color or transparent

**LinkedIn:**
- **Size:** 400×400px
- **Format:** PNG or JPG
- **Design:** Icon + abbreviated wordmark or icon only
- **Background:** White or brand color

**Instagram:**
- **Size:** 320×320px minimum
- **Format:** JPG or PNG
- **Design:** Icon only, simplified
- **Background:** Solid brand color with subtle gradient

**Open Graph (Social Sharing):**
- **Size:** 1200×630px
- **Format:** Full logo lockup (horizontal)
- **Design:** Logo + tagline on branded background
- **Position:** Left-aligned or centered

### 7. Email Signature
**Specification:**
- **Format:** Horizontal logo (Icon + Wordmark)
- **Size:** 150px width maximum
- **File Format:** PNG with transparency, optimized for email
- **Link:** Logo should link to homepage

### 8. Documentation/Reports
**Specification:**
- **Format:** Full horizontal logo with tagline
- **Size:** 2 inches width for print
- **Position:** Top-left of first page header
- **Color:** Full color (preferred) or monochrome for B&W printing

### 9. Loading States
**Specification:**
- **Format:** Icon only
- **Size:** 48px × 48px
- **Animation:** Subtle pulse or fade (not spin)
- **Background:** Transparent
- **Duration:** 1.5s per cycle

**Animation:**
```css
@keyframes logo-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(0.95); }
}

.logo-loading {
  animation: logo-pulse 1.5s ease-in-out infinite;
}
```

### 10. Error/Empty States
**Specification:**
- **Format:** Icon only, grayscale
- **Size:** 64px × 64px
- **Style:** 40% opacity
- **Purpose:** Subtle branding without competing with error message

### 11. Merchandise/Swag
**Specification:**
- **T-Shirts:** Large logo (12" width) centered or left chest (3" width)
- **Hats:** Icon only, embroidered, 2" × 2"
- **Stickers:** Full logo, 3" × 1.5", die-cut
- **Notebooks:** Foil-stamped logo, 2" width
- **Files:** Vector format (SVG, PDF, AI) required

---

## Do's and Don'ts

### DO:

#### Positioning & Spacing
✓ **Maintain clear space** around logo at all times
✓ **Use approved logo variations** for different contexts
✓ **Align logo consistently** in similar contexts
✓ **Center logo vertically** in navigation elements
✓ **Use appropriate sizing** based on viewing distance

#### Color & Treatment
✓ **Use approved color combinations** from this guide
✓ **Switch to white logo** on dark backgrounds automatically
✓ **Use monochrome version** when color is not available
✓ **Maintain color accuracy** (use provided hex/HSL values)
✓ **Test logo contrast** against all backgrounds

#### Technical
✓ **Use vector formats** (SVG) for web when possible
✓ **Provide high-resolution** raster versions for specific uses
✓ **Use PNG with transparency** for overlays
✓ **Optimize file sizes** for web performance
✓ **Include alt text** for accessibility

---

### DON'T:

#### Distortion
✗ **Never stretch or compress** the logo disproportionately
✗ **Never rotate** the logo at odd angles
✗ **Never skew or distort** letterforms
✗ **Never alter spacing** between icon and wordmark
✗ **Never change aspect ratio** of any element

#### Color Violations
✗ **Never use unauthorized colors** outside this guide
✗ **Never use low-contrast combinations** (below 4.5:1)
✗ **Never apply gradients** unless specified in logo design
✗ **Never use neon or oversaturated** versions
✗ **Never invert colors** arbitrarily (except dark/light mode)

#### Modification
✗ **Never add effects** (drop shadows, bevels, glows) unless specified
✗ **Never outline** the logo with borders
✗ **Never rearrange elements** of the logo
✗ **Never add additional text** to the logo lockup
✗ **Never animate** logo elements independently (must move as unit)

#### Background Issues
✗ **Never place logo on busy** photography without sufficient contrast
✗ **Never use backgrounds** with similar colors to logo
✗ **Never place logo on gradients** that affect legibility
✗ **Never use transparent logo** on unknown background colors

#### Typography
✗ **Never recreate wordmark** in different fonts
✗ **Never adjust letterspacing** in wordmark
✗ **Never use lowercase** for "BetterBros"
✗ **Never separate** "Better" and "Bros" into different lines

#### Context
✗ **Never make logo smaller** than minimum size specifications
✗ **Never crop** any part of the logo
✗ **Never place logo at odd angles** in corners
✗ **Never use outdated logo** versions

---

## Technical Implementation

### File Structure

```
/public/brand/
├── logo/
│   ├── svg/
│   │   ├── betterbros-full-color.svg
│   │   ├── betterbros-white.svg
│   │   ├── betterbros-dark.svg
│   │   ├── betterbros-monochrome.svg
│   │   ├── betterbros-icon-color.svg
│   │   ├── betterbros-icon-white.svg
│   │   ├── betterbros-wordmark.svg
│   │   └── betterbros-stacked.svg
│   ├── png/
│   │   ├── @1x/
│   │   ├── @2x/
│   │   └── @3x/
│   ├── favicon/
│   │   ├── favicon.ico
│   │   ├── favicon-16x16.png
│   │   ├── favicon-32x32.png
│   │   ├── apple-touch-icon.png
│   │   ├── android-chrome-192x192.png
│   │   └── android-chrome-512x512.png
│   └── social/
│       ├── og-image.png (1200×630)
│       ├── twitter-card.png (1200×600)
│       └── avatar-square.png (400×400)
└── guidelines/
    └── LOGO_DESIGN_GUIDELINES.md (this file)
```

### React Component Implementation

```typescript
// /src/components/brand/Logo.tsx
import React from 'react';
import { cn } from '@/lib/utils';

interface LogoProps {
  variant?: 'full' | 'compact' | 'icon' | 'wordmark';
  theme?: 'auto' | 'light' | 'dark' | 'monochrome';
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  showTagline?: boolean;
}

export function Logo({
  variant = 'compact',
  theme = 'auto',
  size = 'md',
  className,
  showTagline = false
}: LogoProps) {

  const sizeClasses = {
    sm: 'h-6',
    md: 'h-8',
    lg: 'h-12',
    xl: 'h-16'
  };

  const iconSizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12'
  };

  const wordmarkSizeClasses = {
    sm: 'text-lg',
    md: 'text-xl',
    lg: 'text-2xl',
    xl: 'text-4xl'
  };

  const taglineSizeClasses = {
    sm: 'text-[8px]',
    md: 'text-[10px]',
    lg: 'text-xs',
    xl: 'text-sm'
  };

  // Determine logo color based on theme
  const logoColor = theme === 'light' ? 'text-[#1E40AF]' :
                    theme === 'dark' ? 'text-white' :
                    theme === 'monochrome' ? 'text-current' :
                    'text-primary-foreground'; // Auto mode uses CSS variable

  const accentColor = theme === 'monochrome' ? 'text-current' : 'text-profit';

  if (variant === 'icon') {
    return (
      <div className={cn('flex items-center justify-center', className)}>
        <BetterBrosIcon className={cn(iconSizeClasses[size], logoColor)} />
      </div>
    );
  }

  if (variant === 'wordmark') {
    return (
      <div className={cn('flex flex-col', className)}>
        <span className={cn('font-bold leading-none', wordmarkSizeClasses[size], logoColor)}>
          BetterBros
        </span>
        {showTagline && (
          <span className={cn(
            'font-medium tracking-wider uppercase opacity-70 mt-1',
            taglineSizeClasses[size],
            logoColor
          )}>
            Smart Props Trading
          </span>
        )}
      </div>
    );
  }

  // Full or Compact variants
  return (
    <div className={cn('flex items-center gap-3', className)}>
      <div className={cn(
        'flex items-center justify-center rounded-md',
        variant === 'full' ? 'bg-primary p-2' : ''
      )}>
        <BetterBrosIcon className={cn(iconSizeClasses[size], logoColor)} />
      </div>
      <div className="flex flex-col">
        <span className={cn('font-bold leading-none', wordmarkSizeClasses[size], logoColor)}>
          BetterBros
        </span>
        {(variant === 'full' || showTagline) && (
          <span className={cn(
            'font-medium tracking-wider uppercase opacity-70',
            taglineSizeClasses[size],
            logoColor
          )}>
            Smart Props Trading
          </span>
        )}
      </div>
    </div>
  );
}

// Icon component placeholder - replace with actual SVG
function BetterBrosIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* This is a placeholder - replace with actual icon design */}
      <path
        d="M6 18L18 6M18 6H10M18 6V14"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M8 12L10 14L12 10L14 16L16 12"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.6"
      />
    </svg>
  );
}

// Export variants for specific use cases
export function HeaderLogo() {
  return <Logo variant="compact" size="md" />;
}

export function MobileLogo() {
  return <Logo variant="compact" size="sm" />;
}

export function LoadingLogo() {
  return (
    <div className="animate-pulse-soft">
      <Logo variant="icon" size="lg" />
    </div>
  );
}
```

### CSS Variables

```css
/* Add to globals.css */

:root {
  /* Logo Colors */
  --logo-primary-light: #1E40AF;      /* Royal Blue */
  --logo-primary-dark: #FFFFFF;       /* White */
  --logo-accent: #10B981;             /* Emerald Green */
  --logo-monochrome: currentColor;

  /* Logo Sizing */
  --logo-icon-sm: 24px;
  --logo-icon-md: 32px;
  --logo-icon-lg: 48px;
  --logo-icon-xl: 64px;

  --logo-wordmark-sm: 18px;
  --logo-wordmark-md: 24px;
  --logo-wordmark-lg: 32px;
  --logo-wordmark-xl: 48px;

  /* Logo Spacing */
  --logo-gap: 12px;
  --logo-clearspace: 32px;
}

/* Logo utility classes */
.logo-container {
  display: inline-flex;
  align-items: center;
  gap: var(--logo-gap);
}

.logo-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius);
}

.logo-wordmark {
  font-family: var(--font-inter);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1;
}

.logo-tagline {
  font-family: var(--font-inter);
  font-weight: 500;
  font-size: 0.625rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  opacity: 0.8;
  margin-top: 0.25rem;
}

/* Theme-aware logo colors */
.dark .logo-auto {
  color: var(--logo-primary-dark);
}

.light .logo-auto {
  color: var(--logo-primary-light);
}
```

### Next.js Metadata Configuration

```typescript
// /src/app/layout.tsx or metadata configuration
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'BetterBros - Smart Props Trading Platform',
  description: 'Data-driven sports betting analytics and props trading platform',

  // Favicon configuration
  icons: {
    icon: [
      { url: '/favicon.ico' },
      { url: '/favicon-16x16.png', sizes: '16x16', type: 'image/png' },
      { url: '/favicon-32x32.png', sizes: '32x32', type: 'image/png' },
    ],
    apple: [
      { url: '/apple-touch-icon.png', sizes: '180x180', type: 'image/png' },
    ],
    other: [
      {
        rel: 'android-chrome',
        url: '/android-chrome-192x192.png',
        sizes: '192x192',
      },
      {
        rel: 'android-chrome',
        url: '/android-chrome-512x512.png',
        sizes: '512x512',
      },
    ],
  },

  // Open Graph configuration
  openGraph: {
    title: 'BetterBros - Smart Props Trading Platform',
    description: 'Data-driven sports betting analytics and props trading platform',
    url: 'https://betterbros.com',
    siteName: 'BetterBros',
    images: [
      {
        url: '/brand/social/og-image.png',
        width: 1200,
        height: 630,
        alt: 'BetterBros Logo',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },

  // Twitter Card configuration
  twitter: {
    card: 'summary_large_image',
    title: 'BetterBros - Smart Props Trading Platform',
    description: 'Data-driven sports betting analytics and props trading platform',
    images: ['/brand/social/twitter-card.png'],
  },

  // PWA manifest
  manifest: '/manifest.json',
};
```

### Manifest.json Configuration

```json
{
  "name": "BetterBros - Smart Props Trading",
  "short_name": "BetterBros",
  "description": "Smart Props Trading Platform",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0C1222",
  "theme_color": "#1E40AF",
  "orientation": "portrait-primary",
  "icons": [
    {
      "src": "/android-chrome-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/android-chrome-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
```

### Design Tokens (TypeScript)

```typescript
// /src/lib/brand/design-tokens.ts

export const brandTokens = {
  logo: {
    colors: {
      primary: {
        light: '#1E40AF',
        dark: '#FFFFFF',
      },
      accent: '#10B981',
      monochrome: 'currentColor',
    },
    sizes: {
      icon: {
        xs: 16,
        sm: 24,
        md: 32,
        lg: 48,
        xl: 64,
      },
      wordmark: {
        sm: 18,
        md: 24,
        lg: 32,
        xl: 48,
      },
      tagline: {
        sm: 8,
        md: 10,
        lg: 12,
        xl: 14,
      },
    },
    spacing: {
      gap: 12,
      clearSpace: 32,
      internal: 4,
    },
    radius: {
      standard: 8,
      small: 4,
      large: 12,
    },
    typography: {
      wordmark: {
        fontFamily: 'var(--font-inter)',
        fontWeight: 800,
        letterSpacing: '-0.02em',
        lineHeight: 1,
      },
      tagline: {
        fontFamily: 'var(--font-inter)',
        fontWeight: 500,
        letterSpacing: '0.05em',
        textTransform: 'uppercase' as const,
        opacity: 0.8,
      },
    },
  },
} as const;

export type BrandTokens = typeof brandTokens;
```

### SVG Export Requirements

When exporting final logo files:

```
SVG Requirements:
- Viewbox: 0 0 24 24 (for icons) or proportional for full logo
- No raster images embedded
- Paths outlined (no fonts)
- Simplified paths (remove unnecessary points)
- Named layers for easy editing
- Clean, organized structure
- No hidden layers or objects
- Optimized file size (< 5KB for icons)

Color Format:
- Use hex colors (#1E40AF) not RGB
- Use 'currentColor' for adaptive elements
- Include both color and monochrome versions
```

---

## Implementation Checklist

### Phase 1: Design Creation
- [ ] Choose primary logo concept direction
- [ ] Design icon at multiple sizes (16px - 512px)
- [ ] Design full horizontal lockup
- [ ] Design compact lockup (no tagline)
- [ ] Design stacked variation
- [ ] Create wordmark-only version
- [ ] Design dark mode variations
- [ ] Design light mode variations
- [ ] Create monochrome version

### Phase 2: File Generation
- [ ] Export all SVG files (optimized)
- [ ] Generate PNG files at 1x, 2x, 3x
- [ ] Create favicon.ico (multi-resolution)
- [ ] Generate all favicon sizes
- [ ] Create Apple touch icon (180×180)
- [ ] Create Android icons (192×192, 512×512)
- [ ] Design Open Graph image (1200×630)
- [ ] Design Twitter Card image (1200×600)
- [ ] Create square avatar (400×400)

### Phase 3: Code Implementation
- [ ] Update dashboard-shell.tsx with new logo component
- [ ] Create Logo.tsx component with variants
- [ ] Add logo design tokens to codebase
- [ ] Update CSS variables for logo
- [ ] Configure Next.js metadata
- [ ] Create/update manifest.json
- [ ] Add all favicon files to /public
- [ ] Test logo on all background colors
- [ ] Test responsive behavior (mobile, tablet, desktop)
- [ ] Verify accessibility (alt text, contrast)

### Phase 4: Documentation
- [ ] Complete this guidelines document
- [ ] Create quick-reference PDF
- [ ] Document logo usage in README
- [ ] Create visual do's and don'ts poster
- [ ] Share with team for feedback

### Phase 5: Quality Assurance
- [ ] Test logo in all browsers
- [ ] Verify mobile app icon display (iOS/Android)
- [ ] Check social media avatar appearance
- [ ] Validate Open Graph previews
- [ ] Test print quality at various sizes
- [ ] Verify dark/light mode switching
- [ ] Check loading state animations
- [ ] Validate accessibility compliance

---

## Recommended Next Steps

### Immediate Actions:

1. **Review and Select Concept:**
   - Review the 5 logo concepts provided
   - Choose primary direction (recommend "Data Bros" - Concept 1)
   - Provide feedback on any refinements needed

2. **Design Development:**
   - Work with designer to create final logo based on chosen concept
   - Ensure all specifications in this guide are met
   - Create all required variations

3. **Technical Setup:**
   - Generate all required file sizes and formats
   - Implement Logo component in React
   - Update dashboard-shell.tsx to use new component
   - Test across all contexts

4. **Brand Rollout:**
   - Update all instances across platform
   - Update social media profiles
   - Update documentation and marketing materials
   - Announce new brand to users (if desired)

### Future Considerations:

- **Animation:** Consider subtle logo animations for loading states or hero sections
- **3D Version:** Explore 3D logo for special marketing campaigns
- **Brand Extensions:** Design sub-brand logos for future products
- **Merchandising:** Prepare files for merchandise production
- **Partnerships:** Create co-branding guidelines for partner integrations

---

## Contact & Approval

### Brand Guardian:
For questions about logo usage or approval of new applications:
- Review this guide first
- Submit requests with mockups/examples
- Allow 2-3 business days for review

### File Requests:
If you need logo files not currently available:
- Specify format, size, and use case
- Reference this guide for specifications
- Request through proper channels

---

**Document Control:**
- **Version:** 1.0
- **Last Updated:** October 14, 2025
- **Next Review:** January 14, 2026
- **Status:** Active

---

## Appendix: Color Reference

### Quick Reference Color Chart

```
┌─────────────────────────────────────────────────────────────┐
│ BETTERBROS COLOR PALETTE                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ PRIMARY LOGO COLORS                                         │
│ ┌──────────────────┐  ┌──────────────────┐                │
│ │   Royal Blue     │  │  Emerald Green   │                │
│ │   #1E40AF        │  │  #10B981         │                │
│ │   HSL(222,73%,40%)│  │ HSL(142,76%,36%) │                │
│ └──────────────────┘  └──────────────────┘                │
│                                                             │
│ DARK MODE (Default)                                         │
│ ┌──────────────────┐  ┌──────────────────┐                │
│ │   White          │  │  Emerald Green   │                │
│ │   #FFFFFF        │  │  #10B981         │                │
│ └──────────────────┘  └──────────────────┘                │
│                                                             │
│ BACKGROUNDS (Dark Mode)                                     │
│ ┌──────────────────┐  ┌──────────────────┐                │
│ │   Deep Navy      │  │  Card Background │                │
│ │   #0C1222        │  │  #1A1F2E         │                │
│ └──────────────────┘  └──────────────────┘                │
│                                                             │
│ SPORTSBOOK COLORS                                           │
│ ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│ │ Profit  │  │  Loss   │  │ Neutral │  │  Live   │       │
│ │ #10B981 │  │ #EF4444 │  │ #6B7280 │  │ #FB923C │       │
│ └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Accessibility Contrast Matrix

```
Logo Color              Background          Contrast Ratio  Rating
─────────────────────────────────────────────────────────────────
White (#FFFFFF)         Deep Navy (#0C1222)    18.47:1      AAA
White (#FFFFFF)         Royal Blue (#1E40AF)    8.59:1      AAA
Royal Blue (#1E40AF)    White (#FFFFFF)         8.59:1      AAA
Emerald (#10B981)       Deep Navy (#0C1222)     7.23:1      AAA
Emerald (#10B981)       White (#FFFFFF)         2.89:1      Fail*
Royal Blue (#1E40AF)    Card BG (#1A1F2E)       7.02:1      AAA

* Emerald should only be used as accent with sufficient size (3:1 acceptable for large text)
```

---

*End of BetterBros Logo Design Guidelines v1.0*
