# Neon Logo Implementation Checklist

Use this checklist to ensure proper implementation of the neon logo component.

## Pre-Implementation

- [ ] Read `QUICK_SETUP.md` for overview
- [ ] Review `README.md` for API reference
- [ ] Check `USAGE_EXAMPLES.md` for code patterns
- [ ] Have logo SVG file ready at `/Users/joshuadeleon/Downloads/OA Logo - Small Horizontal Lockup - White copy.svg`

## Phase 1: Installation (5 minutes)

### 1.1 Import Styles
- [ ] Open `apps/web/app/layout.tsx`
- [ ] Add: `import '@/components/brand/neon-logo.css';`
- [ ] Save and verify no build errors

### 1.2 Verify Imports Work
- [ ] Create test component with `import { NeonLogo } from '@/components/brand';`
- [ ] Render `<NeonLogo />` on a test page
- [ ] Confirm placeholder logo displays (will show "Insert Logo SVG" text)

### 1.3 Check Path Aliases
- [ ] Verify `tsconfig.json` has `"@/*": ["./src/*"]` path mapping
- [ ] Restart TypeScript server if needed (VS Code: Cmd+Shift+P → "TypeScript: Restart TS Server")
- [ ] Confirm no import errors

## Phase 2: Logo SVG Integration (10-15 minutes)

### 2.1 Choose Import Method

**Option A: Inline SVG (Recommended)**
- [ ] Open `/Users/joshuadeleon/BetterBros Bets/apps/web/src/components/brand/NeonLogo.tsx`
- [ ] Locate `InlineNeonSVG` component (around line 187)
- [ ] Extract logo content from source SVG (lines 4 to second-to-last)
- [ ] Replace placeholder with actual logo paths
- [ ] Test display on demo page

**Option B: External SVG (Simpler)**
- [ ] Copy logo to public folder: `cp "/Users/joshuadeleon/Downloads/OA Logo - Small Horizontal Lockup - White copy.svg" apps/web/public/logo.svg`
- [ ] Use `<NeonLogo inline={false} svgPath="/logo.svg" />`
- [ ] Note: This method has limited glow control

### 2.2 Verify Logo Displays
- [ ] Run dev server: `npm run dev`
- [ ] Visit demo page: `http://localhost:3000/neon-logo-demo`
- [ ] Confirm actual logo (not placeholder) displays
- [ ] Check all sizes render correctly
- [ ] Verify glow effects are visible

## Phase 3: Replace Existing Logos (15-30 minutes)

### 3.1 Find Current Logo Usage
- [ ] Search codebase for logo references: `grep -r "logo" apps/web/src/ --include="*.tsx"`
- [ ] Identify all locations where logo is used
- [ ] Document current implementations

Common locations to check:
- [ ] `app/dashboard/layout.tsx`
- [ ] `components/layout/Header.tsx`
- [ ] `components/layout/Sidebar.tsx`
- [ ] `app/page.tsx` (landing page)
- [ ] `app/login/page.tsx`
- [ ] `app/signup/page.tsx`

### 3.2 Replace Dashboard Header Logo
- [ ] Open dashboard header file
- [ ] Import: `import { NeonLogo, useHeaderNeonLogo } from '@/components/brand';`
- [ ] Replace `<img>` tag with:
  ```tsx
  const logoProps = useHeaderNeonLogo();
  return <NeonLogo {...logoProps} clickable onClick={() => router.push('/')} />;
  ```
- [ ] Test in browser - logo should display with subtle glow
- [ ] Verify hover animation works
- [ ] Check click navigation works

### 3.3 Replace Landing Page Logo
- [ ] Open landing page file
- [ ] Import: `import { NeonLogo, useHeroNeonLogo } from '@/components/brand';`
- [ ] Replace logo with:
  ```tsx
  const logoProps = useHeroNeonLogo();
  return <NeonLogo {...logoProps} />;
  ```
- [ ] Test entrance animation
- [ ] Verify strong glow is visible

### 3.4 Add Loading States
- [ ] Find or create loading component
- [ ] Import: `import { NeonLogo, useLoadingNeonLogo } from '@/components/brand';`
- [ ] Implement:
  ```tsx
  const logoProps = useLoadingNeonLogo();
  return <NeonLogo {...logoProps} />;
  ```
- [ ] Test pulse animation
- [ ] Verify loading state looks good

## Phase 4: Testing (20-30 minutes)

### 4.1 Visual Testing
- [ ] Test all size variants (sm, md, lg, xl)
- [ ] Test all intensities (subtle, medium, strong, ultra)
- [ ] Test all animations (none, pulse, hover, shimmer, entrance)
- [ ] Verify glow is visible on dark backgrounds
- [ ] Check colors match brand guidelines
- [ ] Confirm no clipping or overflow issues

### 4.2 Responsive Testing
- [ ] Test on mobile (< 640px) - should auto-optimize
- [ ] Test on tablet (640px - 1024px)
- [ ] Test on desktop (> 1024px)
- [ ] Verify logo scales appropriately
- [ ] Check performance on mobile devices
- [ ] Confirm touch interactions work

### 4.3 Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Chrome Mobile (Android)

### 4.4 Accessibility Testing
- [ ] Test keyboard navigation (Tab, Enter, Space)
- [ ] Test with screen reader (VoiceOver, NVDA, or JAWS)
- [ ] Verify focus states are visible
- [ ] Check aria-labels are descriptive
- [ ] Test with high contrast mode
- [ ] Enable reduced motion preference - verify animations disabled

### 4.5 Performance Testing
- [ ] Run Lighthouse audit on dashboard
- [ ] Run Lighthouse audit on landing page
- [ ] Check FCP (First Contentful Paint) impact
- [ ] Check LCP (Largest Contentful Paint) impact
- [ ] Monitor CPU usage (should be low at idle)
- [ ] Check mobile performance scores

Performance targets:
- [ ] FCP impact: < 20ms
- [ ] LCP impact: < 40ms
- [ ] Lighthouse score: -5 points or less
- [ ] Mobile performance: 70+ score

## Phase 5: Optimization (15-20 minutes)

### 5.1 Adjust Based on Performance
If performance issues detected:
- [ ] Reduce intensity on mobile: Use `drop-shadow-method` class
- [ ] Disable animations on low-end devices
- [ ] Consider using container glow method for frequently rendered logos
- [ ] Lazy load logos below the fold

### 5.2 Fine-tune Visual Effect
- [ ] Adjust glow colors if needed (edit CSS variables)
- [ ] Tweak animation speeds for brand feel
- [ ] Modify intensities for different contexts
- [ ] Get design team approval on final look

### 5.3 Code Cleanup
- [ ] Remove old logo imports and files
- [ ] Clean up unused logo assets
- [ ] Update any logo-related comments
- [ ] Verify no console errors or warnings

## Phase 6: Documentation & Handoff (10 minutes)

### 6.1 Update Project Documentation
- [ ] Add neon logo usage to project README
- [ ] Document any custom modifications made
- [ ] Note performance benchmarks
- [ ] Record team decisions on default settings

### 6.2 Team Communication
- [ ] Demo to design team
- [ ] Show to development team
- [ ] Get stakeholder approval
- [ ] Document feedback and iterate if needed

### 6.3 Deployment Preparation
- [ ] Verify all changes committed to git
- [ ] Test on staging environment
- [ ] Create deployment checklist
- [ ] Plan rollout strategy

## Phase 7: Deployment (Varies)

### 7.1 Pre-Deployment
- [ ] Final Lighthouse audit
- [ ] Final accessibility check
- [ ] Cross-browser verification
- [ ] Mobile device testing

### 7.2 Staging Deployment
- [ ] Deploy to staging
- [ ] Smoke test all pages with logo
- [ ] Verify no console errors
- [ ] Get QA approval

### 7.3 Production Deployment
- [ ] Deploy to production
- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Verify user experience

### 7.4 Post-Deployment
- [ ] Monitor user feedback
- [ ] Track performance metrics
- [ ] Document any issues
- [ ] Plan iterations if needed

## Optional Enhancements

### Tailwind Integration
- [ ] Add `neonTailwindConfig` to `tailwind.config.js`
- [ ] Test new utility classes
- [ ] Update components to use utilities
- [ ] Document new utilities for team

### Advanced Customizations
- [ ] Create theme-specific logo variants
- [ ] Add seasonal/special event variations
- [ ] Implement dark/light mode toggle
- [ ] Create animated logo sequence

### Analytics & Monitoring
- [ ] Add click tracking to logo
- [ ] Monitor logo interaction rates
- [ ] Track performance metrics
- [ ] Set up error monitoring

## Troubleshooting Reference

If issues arise, check:
- [ ] `IMPLEMENTATION_GUIDE.md` - Troubleshooting section
- [ ] `README.md` - API reference
- [ ] Browser console for errors
- [ ] Network tab for failed asset loads
- [ ] React DevTools for component props

Common issues:
- **Glow not visible**: Import CSS, check background color, increase intensity
- **Logo not displaying**: Check SVG content, verify imports, ensure container has dimensions
- **Performance lag**: Reduce intensity, use drop-shadow method, disable animations
- **TypeScript errors**: Check path aliases, restart TS server, verify exports

## Success Criteria

Implementation is complete when:
- [ ] Logo displays correctly on all key pages
- [ ] Glow effect is visible and visually appealing
- [ ] Performance impact is within acceptable range (< -5 Lighthouse points)
- [ ] Accessibility requirements are met (WCAG AA minimum)
- [ ] All browsers render correctly
- [ ] Mobile experience is optimized
- [ ] Team approves visual design
- [ ] Production deployment is successful
- [ ] No critical errors or issues

## Time Estimates

| Phase | Estimated Time |
|-------|----------------|
| Installation | 5 minutes |
| Logo SVG Integration | 10-15 minutes |
| Replace Existing | 15-30 minutes |
| Testing | 20-30 minutes |
| Optimization | 15-20 minutes |
| Documentation | 10 minutes |
| Deployment | Varies |
| **Total** | **75-120 minutes** |

## Notes

- Keep IMPLEMENTATION_GUIDE.md open for detailed reference
- Use demo page extensively for testing
- Don't skip accessibility testing
- Get design approval before deployment
- Monitor performance in production

---

**Checklist Status**: ☐ Not Started | ☑ Complete

Last Updated: 2025-10-16
