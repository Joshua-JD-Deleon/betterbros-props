# Neon Logo Quick Setup Guide

Get up and running with the neon logo in under 5 minutes.

## Step 1: Import Styles (Required)

Add to your root layout:

```tsx
// app/layout.tsx
import '@/components/brand/neon-logo.css';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

## Step 2: Use the Component

### Option A: Simple Usage

```tsx
import { NeonLogo } from '@/components/brand';

export function Header() {
  return (
    <header className="bg-gray-900 px-4 py-3">
      <NeonLogo />
    </header>
  );
}
```

### Option B: With Responsive Hook (Recommended)

```tsx
import { NeonLogo, useHeaderNeonLogo } from '@/components/brand';

export function Header() {
  const logoProps = useHeaderNeonLogo();

  return (
    <header className="bg-gray-900 px-4 py-3">
      <NeonLogo {...logoProps} />
    </header>
  );
}
```

## Step 3: Import Your Logo SVG (Important!)

The component currently has a placeholder. Replace it with your actual logo:

### Method 1: Quick Copy-Paste

1. Read the first 50 lines of your logo to get the style definitions:

```bash
head -n 50 "/Users/joshuadeleon/Downloads/OA Logo - Small Horizontal Lockup - White copy.svg"
```

2. Extract the main SVG content (skip the opening `<svg>` tag and closing `</svg>`):

```bash
tail -n +4 "/Users/joshuadeleon/Downloads/OA Logo - Small Horizontal Lockup - White copy.svg" | head -n -1
```

3. Open `/Users/joshuadeleon/BetterBros Bets/apps/web/src/components/brand/NeonLogo.tsx`

4. Find the `InlineNeonSVG` component (around line 187)

5. Replace the placeholder content with your actual logo paths

### Method 2: Use External SVG (Simpler but Less Control)

1. Copy logo to public folder:

```bash
cp "/Users/joshuadeleon/Downloads/OA Logo - Small Horizontal Lockup - White copy.svg" /Users/joshuadeleon/BetterBros\ Bets/apps/web/public/logo.svg
```

2. Use external mode:

```tsx
<NeonLogo
  inline={false}
  svgPath="/logo.svg"
  intensity="medium"
/>
```

Note: External SVG has limited glow control. Inline is recommended.

## Step 4: Test It Out

Visit the demo page to see all options:

```
http://localhost:3000/neon-logo-demo
```

## Common First Implementations

### Replace Existing Logo in Dashboard Header

**Find your current header** (common locations):
- `app/dashboard/layout.tsx`
- `components/layout/Header.tsx`
- `components/layout/DashboardHeader.tsx`

**Replace this:**
```tsx
<img src="/logo.svg" alt="Logo" className="h-10" />
```

**With this:**
```tsx
import { NeonLogo, useHeaderNeonLogo } from '@/components/brand';

// Inside your component:
const logoProps = useHeaderNeonLogo();

<NeonLogo {...logoProps} clickable onClick={() => router.push('/')} />
```

### Add to Landing Page Hero

**In your landing page** (`app/page.tsx`):

```tsx
import { NeonLogo, useHeroNeonLogo } from '@/components/brand';

export default function LandingPage() {
  const logoProps = useHeroNeonLogo();

  return (
    <section className="bg-gradient-to-b from-gray-900 to-gray-800 py-20 text-center">
      <div className="mb-8 flex justify-center">
        <NeonLogo {...logoProps} />
      </div>
      <h1 className="text-5xl font-bold">Welcome to BetterBros</h1>
    </section>
  );
}
```

### Add Loading State

```tsx
import { NeonLogo, useLoadingNeonLogo } from '@/components/brand';

export function LoadingSpinner() {
  const logoProps = useLoadingNeonLogo();

  return (
    <div className="flex items-center justify-center py-20">
      <div className="text-center">
        <NeonLogo {...logoProps} />
        <p className="mt-4 text-gray-400">Loading...</p>
      </div>
    </div>
  );
}
```

## Troubleshooting

### "Cannot find module '@/components/brand'"

Make sure you have TypeScript path aliases set up in `tsconfig.json`:

```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Glow not visible

1. Make sure you imported the CSS: `import '@/components/brand/neon-logo.css';`
2. Check that you're using a dark background
3. Try increasing intensity: `<NeonLogo intensity="strong" />`

### Logo doesn't display

1. Check browser console for errors
2. Verify the component is imported correctly
3. Ensure the container has dimensions (add `className="w-48 h-12"` for testing)

## Next Steps

1. **Read the full documentation**: `/Users/joshuadeleon/BetterBros Bets/apps/web/src/components/brand/README.md`
2. **Review usage examples**: `/Users/joshuadeleon/BetterBros Bets/apps/web/src/components/brand/USAGE_EXAMPLES.md`
3. **Check visual comparison**: `/Users/joshuadeleon/BetterBros Bets/apps/web/src/components/brand/VISUAL_COMPARISON.md`
4. **Test on demo page**: `http://localhost:3000/neon-logo-demo`

## File Structure

```
apps/web/src/components/brand/
├── NeonLogo.tsx                    # Main component
├── neon-logo.css                   # Styles (MUST import!)
├── useResponsiveNeonLogo.ts        # Responsive hook
├── index.ts                        # Exports
├── README.md                       # Full documentation
├── QUICK_SETUP.md                  # This file
├── USAGE_EXAMPLES.md               # Detailed examples
├── IMPLEMENTATION_GUIDE.md         # Technical guide
├── VISUAL_COMPARISON.md            # Visual guide
└── tailwind-neon-config.ts        # Tailwind utilities

apps/web/src/app/neon-logo-demo/
└── page.tsx                        # Interactive demo
```

## Quick Reference

### Props

```tsx
<NeonLogo
  size="md"              // sm | md | lg | xl
  intensity="medium"     // subtle | medium | strong | ultra
  animation="hover"      // none | pulse | hover | shimmer | entrance
  clickable              // Makes logo clickable
  onClick={() => {}}     // Click handler
  className=""           // Additional classes
/>
```

### Hooks

```tsx
// Automatically optimized for context
const logoProps = useHeaderNeonLogo();   // Headers
const logoProps = useHeroNeonLogo();     // Hero sections
const logoProps = useLoadingNeonLogo();  // Loading states
const logoProps = useFooterNeonLogo();   // Footers
```

That's it! You're ready to use the neon logo component.
