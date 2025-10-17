# Neon Logo Usage Examples

Complete guide for implementing the neon glow logo across different sections of the BetterBros web app.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Dashboard Header](#dashboard-header)
3. [Hero Sections](#hero-sections)
4. [Loading States](#loading-states)
5. [Navigation Components](#navigation-components)
6. [Performance Optimization](#performance-optimization)
7. [Comparison: Filter Methods](#comparison-filter-methods)

---

## Quick Start

### Installation

1. Import the component and styles:

```tsx
import { NeonLogo } from '@/components/brand';
import '@/components/brand/neon-logo.css';
```

2. Basic usage:

```tsx
<NeonLogo />
```

---

## Dashboard Header

### Example 1: Simple Header Logo

```tsx
// app/dashboard/layout.tsx
import { NeonLogo } from '@/components/brand';

export default function DashboardLayout({ children }) {
  return (
    <div className="min-h-screen bg-gray-900">
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <NeonLogo
            size="md"
            intensity="subtle"
            animation="hover"
            clickable
            onClick={() => router.push('/dashboard')}
          />
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
```

### Example 2: Header with Navigation

```tsx
// components/layout/DashboardHeader.tsx
import { NeonLogo } from '@/components/brand';
import Link from 'next/link';

export function DashboardHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-gray-800 bg-gray-900/80 backdrop-blur-md">
      <div className="container mx-auto flex items-center justify-between px-4 py-3">
        {/* Logo */}
        <Link href="/dashboard">
          <NeonLogo
            size="md"
            intensity="subtle"
            animation="hover"
            ariaLabel="BetterBros - Go to Dashboard"
          />
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-6">
          <Link href="/bets" className="text-gray-300 hover:text-white">
            Bets
          </Link>
          <Link href="/leaderboard" className="text-gray-300 hover:text-white">
            Leaderboard
          </Link>
          <Link href="/profile" className="text-gray-300 hover:text-white">
            Profile
          </Link>
        </nav>
      </div>
    </header>
  );
}
```

---

## Hero Sections

### Example 3: Landing Page Hero

```tsx
// app/page.tsx
import { NeonLogo } from '@/components/brand';

export default function LandingPage() {
  return (
    <div className="relative min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="mb-8 flex justify-center">
          <NeonLogo
            size="xl"
            intensity="strong"
            animation="entrance"
          />
        </div>

        <h1 className="mb-6 text-5xl font-bold text-white">
          Bet Smarter, Win Together
        </h1>

        <p className="mx-auto mb-8 max-w-2xl text-xl text-gray-300">
          Join the ultimate betting community where friends compete,
          track stats, and celebrate wins together.
        </p>

        <button className="rounded-lg bg-green-500 px-8 py-3 text-lg font-semibold text-white hover:bg-green-600">
          Get Started
        </button>
      </section>
    </div>
  );
}
```

### Example 4: Hero with Animated Background

```tsx
// app/promo/page.tsx
import { NeonLogo } from '@/components/brand';

export default function PromoPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-gray-900">
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-green-900/20 via-gray-900 to-blue-900/20 animate-gradient-shift" />

      {/* Content */}
      <div className="relative z-10 container mx-auto px-4 py-32">
        <div className="text-center">
          {/* Ultra glow for maximum impact */}
          <div className="mb-12 flex justify-center">
            <NeonLogo
              size="xl"
              intensity="ultra"
              animation="pulse"
              className="container-glow"
            />
          </div>

          <h1 className="mb-6 text-6xl font-bold text-white">
            Limited Time Offer
          </h1>
          <p className="text-2xl text-green-400">
            50% off premium features
          </p>
        </div>
      </div>
    </div>
  );
}
```

---

## Loading States

### Example 5: Page Loading Overlay

```tsx
// components/ui/LoadingOverlay.tsx
import { NeonLogo } from '@/components/brand';

export function LoadingOverlay() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/95 backdrop-blur-sm">
      <div className="text-center">
        <NeonLogo
          size="lg"
          intensity="medium"
          animation="pulse"
          className="neon-loading"
        />
        <p className="mt-6 text-lg text-gray-400">Loading...</p>
      </div>
    </div>
  );
}
```

### Example 6: Suspense Fallback

```tsx
// app/dashboard/bets/page.tsx
import { Suspense } from 'react';
import { NeonLogo } from '@/components/brand';

function BetsLoadingFallback() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="text-center">
        <NeonLogo
          size="md"
          intensity="medium"
          className="neon-loading"
        />
        <p className="mt-4 text-gray-400">Loading your bets...</p>
      </div>
    </div>
  );
}

export default function BetsPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="mb-6 text-3xl font-bold text-white">Your Bets</h1>

      <Suspense fallback={<BetsLoadingFallback />}>
        <BetsList />
      </Suspense>
    </div>
  );
}
```

### Example 7: Button Loading State

```tsx
// components/ui/SubmitButton.tsx
import { NeonLogo } from '@/components/brand';
import { useState } from 'react';

export function SubmitButton() {
  const [isLoading, setIsLoading] = useState(false);

  return (
    <button
      disabled={isLoading}
      className="relative rounded-lg bg-green-500 px-6 py-3 text-white hover:bg-green-600 disabled:opacity-50"
    >
      {isLoading ? (
        <span className="flex items-center gap-2">
          <NeonLogo
            size="sm"
            intensity="subtle"
            className="neon-loading"
          />
          <span>Submitting...</span>
        </span>
      ) : (
        'Submit Bet'
      )}
    </button>
  );
}
```

---

## Navigation Components

### Example 8: Mobile Menu

```tsx
// components/layout/MobileMenu.tsx
import { NeonLogo } from '@/components/brand';
import { useState } from 'react';

export function MobileMenu() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="lg:hidden p-2 text-white"
      >
        <MenuIcon />
      </button>

      {/* Mobile Menu Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 bg-gray-900">
          <div className="container mx-auto px-4 py-6">
            {/* Logo at top */}
            <div className="mb-8 flex items-center justify-between">
              <NeonLogo
                size="md"
                intensity="medium"
                animation="entrance"
              />
              <button onClick={() => setIsOpen(false)}>
                <CloseIcon />
              </button>
            </div>

            {/* Menu items */}
            <nav className="flex flex-col gap-4">
              <a href="/dashboard" className="text-xl text-white">
                Dashboard
              </a>
              <a href="/bets" className="text-xl text-white">
                Bets
              </a>
              <a href="/leaderboard" className="text-xl text-white">
                Leaderboard
              </a>
            </nav>
          </div>
        </div>
      )}
    </>
  );
}
```

### Example 9: Footer Branding

```tsx
// components/layout/Footer.tsx
import { NeonLogo } from '@/components/brand';

export function Footer() {
  return (
    <footer className="border-t border-gray-800 bg-gray-900 py-12">
      <div className="container mx-auto px-4">
        <div className="grid gap-8 md:grid-cols-4">
          {/* Brand column */}
          <div>
            <NeonLogo
              size="sm"
              intensity="subtle"
            />
            <p className="mt-4 text-sm text-gray-400">
              The ultimate betting platform for friends
            </p>
          </div>

          {/* Other footer columns */}
          <div>
            <h3 className="mb-4 font-semibold text-white">Product</h3>
            <ul className="space-y-2 text-sm text-gray-400">
              <li><a href="/features">Features</a></li>
              <li><a href="/pricing">Pricing</a></li>
            </ul>
          </div>

          {/* ... more columns */}
        </div>
      </div>
    </footer>
  );
}
```

---

## Performance Optimization

### Tips for Optimal Performance

1. **Choose the Right Method**:
   - Use SVG filters for best quality (hero sections)
   - Use drop-shadow for good balance (most cases)
   - Use container-glow for lightweight effect

2. **Reduce Intensity on Mobile**:

```tsx
import { useMediaQuery } from '@/hooks/useMediaQuery';

function ResponsiveLogo() {
  const isMobile = useMediaQuery('(max-width: 640px)');

  return (
    <NeonLogo
      intensity={isMobile ? 'subtle' : 'medium'}
      animation={isMobile ? 'none' : 'hover'}
    />
  );
}
```

3. **Lazy Load on Scroll**:

```tsx
import { useInView } from 'framer-motion';
import { useRef } from 'react';

function LazyGlowLogo() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <div ref={ref}>
      {isInView && (
        <NeonLogo
          intensity="strong"
          animation="entrance"
        />
      )}
    </div>
  );
}
```

4. **Disable Animations for Reduced Motion**:

The CSS automatically respects `prefers-reduced-motion`, but you can also disable programmatically:

```tsx
function AccessibleLogo() {
  const prefersReducedMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
  ).matches;

  return (
    <NeonLogo
      animation={prefersReducedMotion ? 'none' : 'pulse'}
    />
  );
}
```

---

## Comparison: Filter Methods

### SVG Filter Method

**Pros:**
- Highest quality glow
- Multiple blur layers for depth
- Best for hero sections and featured placement
- Smooth gradients

**Cons:**
- Slightly more resource-intensive
- Requires inline SVG filter definitions

**Best for:** Hero sections, landing pages, premium features

**Usage:**
```tsx
<NeonLogo intensity="strong" /> // Uses SVG filters by default
```

---

### Drop-Shadow Method

**Pros:**
- Simpler implementation
- Good performance
- Works with external SVG files
- Easy to customize

**Cons:**
- Slightly lower quality than SVG filters
- Limited control over blur distribution

**Best for:** Headers, navigation, general use

**Usage:**
```tsx
<NeonLogo intensity="medium" className="drop-shadow-method" />
```

**CSS:**
```css
.drop-shadow-method .neon-svg {
  filter:
    drop-shadow(0 0 3px var(--neon-primary))
    drop-shadow(0 0 6px rgba(90, 190, 129, 0.6))
    drop-shadow(0 0 12px rgba(75, 182, 122, 0.4));
}
```

---

### Container Glow Method

**Pros:**
- Lightest weight
- Adds ambient glow around logo
- Works with any image format
- CSS-only (no filters)

**Cons:**
- Doesn't glow the logo itself
- Less dramatic effect
- Requires absolute positioning

**Best for:** Subtle enhancement, mobile, performance-critical sections

**Usage:**
```tsx
<NeonLogo intensity="medium" className="container-glow" />
```

**CSS:**
```css
.container-glow::after {
  content: '';
  position: absolute;
  inset: -10px;
  border-radius: 8px;
  background: radial-gradient(
    ellipse at center,
    rgba(90, 190, 129, 0.15) 0%,
    transparent 70%
  );
  pointer-events: none;
  z-index: -1;
}
```

---

## Performance Benchmark

| Method | Quality | Performance | Mobile-Friendly | Use Case |
|--------|---------|-------------|-----------------|----------|
| SVG Filter | 10/10 | 7/10 | 6/10 | Hero, Featured |
| Drop-Shadow | 8/10 | 9/10 | 9/10 | Headers, General |
| Container Glow | 6/10 | 10/10 | 10/10 | Mobile, Subtle |

---

## Tailwind Integration

Add these utilities to your Tailwind config for quick access:

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        'neon-primary': '#5abe81',
        'neon-secondary': '#4bb67a',
        'neon-accent': '#22b575',
      },
      dropShadow: {
        'neon-sm': [
          '0 0 2px rgb(90 190 129)',
          '0 0 4px rgb(90 190 129 / 0.3)'
        ],
        'neon-md': [
          '0 0 3px rgb(90 190 129)',
          '0 0 6px rgb(90 190 129 / 0.6)',
          '0 0 12px rgb(75 182 122 / 0.4)'
        ],
        'neon-lg': [
          '0 0 5px rgb(111 216 154)',
          '0 0 10px rgb(90 190 129)',
          '0 0 20px rgb(90 190 129 / 0.8)',
          '0 0 30px rgb(75 182 122 / 0.6)'
        ],
      },
    },
  },
};
```

Then use directly in JSX:

```tsx
<img
  src="/logo.svg"
  alt="Logo"
  className="drop-shadow-neon-md"
/>
```

---

## Next Steps

1. Import the actual logo SVG content into `NeonLogo.tsx`
2. Test different intensities in your dashboard
3. Measure performance impact
4. Adjust glow colors to match your exact brand
5. Create variants for different themes (light mode, holidays, etc.)

For questions or custom implementations, see the component source code or reach out to the design team.
