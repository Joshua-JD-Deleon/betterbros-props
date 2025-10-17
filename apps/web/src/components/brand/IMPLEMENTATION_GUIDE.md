# Neon Logo Implementation Guide

Complete technical guide for integrating the neon glow logo into your Next.js 15 app.

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Replace Current Logo](#replace-current-logo)
3. [Import Actual SVG](#import-actual-svg)
4. [Configure Styles](#configure-styles)
5. [Performance Optimization](#performance-optimization)
6. [Testing & Validation](#testing--validation)
7. [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Step 1: Verify File Structure

Ensure these files exist:

```
apps/web/src/components/brand/
├── NeonLogo.tsx           # React component
├── neon-logo.css          # Styles
├── index.ts               # Exports
├── USAGE_EXAMPLES.md      # Usage guide
└── IMPLEMENTATION_GUIDE.md # This file
```

### Step 2: Import Styles Globally

Add to your root layout:

```tsx
// app/layout.tsx
import '@/components/brand/neon-logo.css';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

**OR** import in your CSS:

```css
/* app/globals.css */
@import '../components/brand/neon-logo.css';
```

### Step 3: Verify Utility Function

Ensure you have a `cn` utility for class merging:

```tsx
// lib/utils.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

If not, install dependencies:

```bash
npm install clsx tailwind-merge
```

---

## Replace Current Logo

### Find Current Logo Usage

Search your codebase for current logo implementations:

```bash
# Search for logo imports
grep -r "logo" apps/web/src/components/ --include="*.tsx" --include="*.ts"

# Search for image tags with logo
grep -r '<img.*logo' apps/web/src/ --include="*.tsx"
```

### Common Locations

1. **Dashboard Header/Layout**
   - `app/dashboard/layout.tsx`
   - `components/layout/Header.tsx`
   - `components/layout/Sidebar.tsx`

2. **Landing Page**
   - `app/page.tsx`
   - `components/hero/HeroSection.tsx`

3. **Authentication Pages**
   - `app/login/page.tsx`
   - `app/signup/page.tsx`

### Replacement Example

**Before:**
```tsx
// components/layout/Header.tsx
<img src="/logo.svg" alt="BetterBros" className="h-10 w-auto" />
```

**After:**
```tsx
// components/layout/Header.tsx
import { NeonLogo } from '@/components/brand';

<NeonLogo
  size="md"
  intensity="subtle"
  animation="hover"
  clickable
  onClick={() => router.push('/')}
/>
```

---

## Import Actual SVG

The component currently has a placeholder SVG. You need to import your actual logo.

### Option A: Inline SVG (Recommended)

1. **Copy SVG content** from `/Users/joshuadeleon/Downloads/OA Logo - Small Horizontal Lockup - White copy.svg`

2. **Update the `InlineNeonSVG` component** in `NeonLogo.tsx`:

```tsx
// In NeonLogo.tsx, replace the InlineNeonSVG component:

const InlineNeonSVG: React.FC = () => {
  return (
    <svg
      viewBox="0 0 400 100"
      className="w-full h-full neon-svg"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <style>
          {`
            .logo-green-primary { fill: #5abe81; }
            .logo-green-secondary { fill: #4bb67a; }
            .logo-green-accent { fill: #22b575; }
            .logo-cream-primary { fill: #fcfbf9; }
            .logo-cream-secondary { fill: #fff8f0; }
            .logo-cream-accent { fill: #fff9f2; }
            .logo-dark-primary { fill: #090809; }
            .logo-dark-secondary { fill: #0b0b0d; }
          `}
        </style>
      </defs>

      {/* PASTE YOUR ACTUAL SVG PATHS HERE */}
      {/* Copy from line 4 onwards in your SVG file */}
      {/* Remove the opening <svg> and closing </svg> tags */}
      {/* Keep only the <g>, <path>, and other shape elements */}

    </svg>
  );
};
```

3. **How to extract SVG content:**

```bash
# View SVG content (skip first 3 and last 1 lines)
tail -n +4 "/Users/joshuadeleon/Downloads/OA Logo - Small Horizontal Lockup - White copy.svg" | head -n -1
```

### Option B: External SVG File

1. **Copy logo to public folder:**

```bash
cp "/Users/joshuadeleon/Downloads/OA Logo - Small Horizontal Lockup - White copy.svg" apps/web/public/logo.svg
```

2. **Use external file mode:**

```tsx
<NeonLogo
  inline={false}
  svgPath="/logo.svg"
  size="md"
  intensity="medium"
/>
```

**Note:** External SVG mode has some limitations:
- Cannot apply SVG filters as effectively
- Must use drop-shadow method
- Less control over individual elements

### Option C: Optimized Inline Component

For best performance, create a separate optimized logo component:

```tsx
// components/brand/OptimizedLogoSVG.tsx
export function OptimizedLogoSVG() {
  return (
    <svg viewBox="0 0 400 100" className="w-full h-full">
      {/* Paste optimized SVG paths here */}
      {/* Remove unnecessary metadata */}
      {/* Combine paths where possible */}
    </svg>
  );
}
```

Then import in NeonLogo:

```tsx
import { OptimizedLogoSVG } from './OptimizedLogoSVG';

const InlineNeonSVG: React.FC = () => {
  return <OptimizedLogoSVG />;
};
```

---

## Configure Styles

### Customize Glow Colors

Update CSS variables to match your exact brand:

```css
/* In neon-logo.css or your global CSS */
:root {
  /* Match your logo's exact green tones */
  --neon-primary: #5abe81;
  --neon-secondary: #4bb67a;
  --neon-accent: #22b575;
  --neon-highlight: #6fd89a;

  /* Adjust opacity for your design */
  --glow-opacity-subtle: 0.3;
  --glow-opacity-medium: 0.6;
  --glow-opacity-strong: 0.85;
  --glow-opacity-ultra: 1;
}
```

### Adjust Animation Speeds

```css
:root {
  --neon-transition-speed: 300ms; /* Hover transitions */
  --neon-pulse-speed: 2s;         /* Breathing effect */
  --neon-shimmer-speed: 3s;       /* Shimmer travel */
  --neon-entrance-speed: 800ms;   /* Initial fade-in */
}
```

### Theme-Specific Adjustments

```css
/* Light mode - reduce glow intensity */
[data-theme='light'] {
  --glow-opacity-subtle: 0.2;
  --glow-opacity-medium: 0.4;
  --glow-opacity-strong: 0.6;
}

/* Dark mode - enhance glow */
[data-theme='dark'] {
  --glow-opacity-subtle: 0.4;
  --glow-opacity-medium: 0.7;
  --glow-opacity-strong: 0.95;
}
```

### Custom Background Colors

Match the glow to your background:

```tsx
// For dark backgrounds
<div className="bg-gray-900">
  <NeonLogo intensity="medium" />
</div>

// For colored backgrounds
<div className="bg-blue-900">
  <NeonLogo intensity="strong" className="neon-blue-tint" />
</div>
```

Add custom tint:

```css
.neon-blue-tint {
  --neon-primary: #60b8e8;
  --neon-secondary: #4ba8d8;
}
```

---

## Performance Optimization

### 1. Choose the Right Intensity

```tsx
// Dashboard header - subtle
<NeonLogo size="md" intensity="subtle" />

// Hero section - strong
<NeonLogo size="xl" intensity="strong" />

// Mobile - always subtle
const isMobile = useMediaQuery('(max-width: 640px)');
<NeonLogo intensity={isMobile ? 'subtle' : 'medium'} />
```

### 2. Limit Animations

```tsx
// Only animate when needed
<NeonLogo
  animation={isInteractive ? 'hover' : 'none'}
/>

// Use entrance animation once
<NeonLogo
  animation="entrance"
  key={pathname} // Re-trigger on route change
/>
```

### 3. Lazy Load Heavy Effects

```tsx
import dynamic from 'next/dynamic';

const NeonLogo = dynamic(
  () => import('@/components/brand').then(mod => mod.NeonLogo),
  {
    loading: () => <img src="/logo.svg" alt="Logo" className="h-12" />,
    ssr: true, // Server-render for SEO
  }
);
```

### 4. Use Intersection Observer

Only apply glow when logo is visible:

```tsx
import { useInView } from 'framer-motion';
import { useRef } from 'react';

function PerformantLogo() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <div ref={ref}>
      <NeonLogo
        intensity={isInView ? 'strong' : 'subtle'}
        animation={isInView ? 'entrance' : 'none'}
      />
    </div>
  );
}
```

### 5. Optimize SVG

```bash
# Install SVGO
npm install -g svgo

# Optimize your logo
svgo "/Users/joshuadeleon/Downloads/OA Logo - Small Horizontal Lockup - White copy.svg" -o apps/web/public/logo-optimized.svg

# Options for more aggressive optimization
svgo input.svg -o output.svg --multipass --pretty
```

### 6. Preload Critical Assets

```tsx
// app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html>
      <head>
        {/* Preload logo for faster FCP */}
        <link
          rel="preload"
          href="/logo.svg"
          as="image"
          type="image/svg+xml"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
```

### 7. Measure Performance

```tsx
// Add performance monitoring
import { useEffect } from 'react';

function MonitoredLogo() {
  useEffect(() => {
    const startTime = performance.now();

    return () => {
      const endTime = performance.now();
      console.log(`Logo render time: ${endTime - startTime}ms`);
    };
  }, []);

  return <NeonLogo intensity="strong" />;
}
```

---

## Testing & Validation

### Visual Testing Checklist

- [ ] Logo displays correctly at all size variants (sm, md, lg, xl)
- [ ] Glow effect is visible on dark backgrounds
- [ ] Glow intensity levels work as expected
- [ ] Animations play smoothly (pulse, hover, shimmer, entrance)
- [ ] No visual glitches or clipping
- [ ] Colors match brand guidelines
- [ ] Logo is sharp and not blurry

### Responsive Testing

```tsx
// Test at different breakpoints
import { useMediaQuery } from '@/hooks/useMediaQuery';

function ResponsiveTest() {
  const breakpoints = {
    mobile: useMediaQuery('(max-width: 640px)'),
    tablet: useMediaQuery('(min-width: 641px) and (max-width: 1024px)'),
    desktop: useMediaQuery('(min-width: 1025px)'),
  };

  return (
    <div>
      <h2>Current Breakpoint:</h2>
      <p>{Object.entries(breakpoints).find(([_, matches]) => matches)?.[0]}</p>

      <NeonLogo
        size={breakpoints.mobile ? 'sm' : breakpoints.tablet ? 'md' : 'lg'}
        intensity={breakpoints.mobile ? 'subtle' : 'medium'}
      />
    </div>
  );
}
```

### Accessibility Testing

```tsx
// Test keyboard navigation
function AccessibilityTest() {
  return (
    <div>
      <h2>Press Tab to focus, Enter to activate</h2>
      <NeonLogo
        clickable
        onClick={() => alert('Logo clicked!')}
        ariaLabel="Navigate to homepage"
      />
    </div>
  );
}
```

Test with:
- Screen readers (VoiceOver, NVDA, JAWS)
- Keyboard-only navigation
- High contrast mode
- Reduced motion preference

### Performance Testing

```bash
# Lighthouse CI
npm run build
npx lighthouse http://localhost:3000 --view

# Check specific metrics:
# - First Contentful Paint (FCP)
# - Largest Contentful Paint (LCP)
# - Cumulative Layout Shift (CLS)
```

### Browser Testing

Test in:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile Safari (iOS)
- Chrome Mobile (Android)

### Performance Benchmarks

Expected performance targets:

| Metric | Target | Critical |
|--------|--------|----------|
| First Paint | < 100ms | < 200ms |
| Animation FPS | 60 | 30 |
| Memory Usage | < 5MB | < 10MB |
| CPU Usage | < 5% idle | < 20% idle |

---

## Troubleshooting

### Issue: Glow Not Visible

**Symptoms:** Logo appears but without glow effect

**Solutions:**
1. Verify CSS is imported:
   ```tsx
   import '@/components/brand/neon-logo.css';
   ```

2. Check SVG has correct class:
   ```tsx
   <svg className="neon-svg">
   ```

3. Ensure dark background:
   ```tsx
   <div className="bg-gray-900">
     <NeonLogo />
   </div>
   ```

4. Try different intensity:
   ```tsx
   <NeonLogo intensity="ultra" />
   ```

### Issue: Animations Not Working

**Symptoms:** Pulse, shimmer, or hover animations don't play

**Solutions:**
1. Check for `prefers-reduced-motion`:
   ```tsx
   // Disable if user prefers reduced motion
   const prefersReducedMotion = window.matchMedia(
     '(prefers-reduced-motion: reduce)'
   ).matches;
   ```

2. Verify CSS animation is defined:
   ```css
   @keyframes neon-pulse { /* ... */ }
   ```

3. Check for CSS conflicts:
   ```css
   /* Make sure nothing overrides */
   .neon-pulse .neon-svg {
     animation: neon-pulse 2s ease-in-out infinite !important;
   }
   ```

### Issue: Performance Problems

**Symptoms:** Lag, stuttering, high CPU usage

**Solutions:**
1. Reduce glow intensity:
   ```tsx
   <NeonLogo intensity="subtle" />
   ```

2. Disable animations on mobile:
   ```tsx
   <NeonLogo animation={isMobile ? 'none' : 'hover'} />
   ```

3. Use drop-shadow instead of SVG filters:
   ```tsx
   <NeonLogo className="drop-shadow-method" />
   ```

4. Limit number of glowing logos per page

### Issue: SVG Not Displaying

**Symptoms:** Blank space where logo should be

**Solutions:**
1. Check viewBox matches SVG dimensions:
   ```tsx
   <svg viewBox="0 0 400 100">
   ```

2. Verify SVG content is valid:
   ```bash
   # Validate SVG
   xmllint --noout "/path/to/logo.svg"
   ```

3. Ensure container has dimensions:
   ```tsx
   <div className="w-48 h-12">
     <NeonLogo />
   </div>
   ```

### Issue: TypeScript Errors

**Symptoms:** Type errors when importing component

**Solutions:**
1. Ensure proper exports:
   ```tsx
   export { NeonLogo } from './NeonLogo';
   export type { NeonLogoProps } from './NeonLogo';
   ```

2. Check tsconfig.json paths:
   ```json
   {
     "compilerOptions": {
       "paths": {
         "@/*": ["./src/*"]
       }
     }
   }
   ```

3. Restart TypeScript server in VS Code:
   `Cmd+Shift+P` → "TypeScript: Restart TS Server"

### Issue: Glow Clips at Edges

**Symptoms:** Glow is cut off at container boundaries

**Solutions:**
1. Increase filter region:
   ```css
   .neon-glow-strong .neon-svg {
     filter: url(#neon-glow-strong);
   }

   /* In SVG filter definition */
   <filter x="-150%" y="-150%" width="400%" height="400%">
   ```

2. Add padding to container:
   ```tsx
   <div className="p-8">
     <NeonLogo intensity="strong" />
   </div>
   ```

3. Use overflow visible:
   ```css
   .neon-logo-container {
     overflow: visible;
   }
   ```

---

## Next Steps

1. **Import your actual logo SVG** into the component
2. **Test in your dashboard** with different intensities
3. **Measure performance** using Lighthouse
4. **Gather feedback** from team on visual effect
5. **Iterate on colors/intensity** based on brand guidelines
6. **Deploy to staging** for user testing
7. **Monitor performance** in production

---

## Support

For issues or questions:
1. Check this guide and USAGE_EXAMPLES.md
2. Review component source code with detailed comments
3. Test in isolation before integrating
4. Use browser DevTools to inspect CSS/SVG
5. Reach out to design/dev team

Happy glowing!
