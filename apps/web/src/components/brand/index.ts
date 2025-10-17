/**
 * Brand Components
 *
 * Centralized exports for all brand-related components, hooks, and utilities
 */

// Main component
export { NeonLogo } from './NeonLogo';
export type { NeonLogoProps, NeonLogoSize, GlowIntensity, AnimationType } from './NeonLogo';

// Responsive hook
export {
  useResponsiveNeonLogo,
  useHeaderNeonLogo,
  useHeroNeonLogo,
  useLoadingNeonLogo,
  useFooterNeonLogo,
} from './useResponsiveNeonLogo';
export type { ResponsiveNeonLogoOptions, ResponsiveNeonLogoResult } from './useResponsiveNeonLogo';

// Tailwind configuration (optional, available but not exported to avoid build issues)
// export { neonTailwindConfig } from './tailwind-neon-config';
