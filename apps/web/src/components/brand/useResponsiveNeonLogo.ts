import { useMemo } from 'react';
import type { NeonLogoSize, GlowIntensity, AnimationType } from './NeonLogo';

/**
 * Custom hook for responsive neon logo configuration
 *
 * Automatically adjusts logo size, intensity, and animation based on:
 * - Screen size (mobile, tablet, desktop)
 * - User preferences (reduced motion)
 * - Performance mode
 * - Context (header, hero, etc.)
 *
 * @example
 * ```tsx
 * function Header() {
 *   const logoProps = useResponsiveNeonLogo({ context: 'header' });
 *   return <NeonLogo {...logoProps} />;
 * }
 * ```
 */

export interface ResponsiveNeonLogoOptions {
  /**
   * Context determines default settings
   * - header: Subtle, smaller size, hover animation
   * - hero: Strong, larger size, entrance animation
   * - loading: Medium, medium size, pulse animation
   * - footer: Subtle, small size, no animation
   */
  context?: 'header' | 'hero' | 'loading' | 'footer';

  /**
   * Force specific settings (overrides responsive defaults)
   */
  forceSize?: NeonLogoSize;
  forceIntensity?: GlowIntensity;
  forceAnimation?: AnimationType;

  /**
   * Enable performance mode (reduces effects)
   */
  performanceMode?: boolean;

  /**
   * Custom breakpoints (optional)
   */
  breakpoints?: {
    mobile?: number;
    tablet?: number;
    desktop?: number;
  };
}

export interface ResponsiveNeonLogoResult {
  size: NeonLogoSize;
  intensity: GlowIntensity;
  animation: AnimationType;
  className?: string;
}

/**
 * Default configurations for each context
 */
const CONTEXT_DEFAULTS = {
  header: {
    mobile: { size: 'sm' as NeonLogoSize, intensity: 'subtle' as GlowIntensity, animation: 'none' as AnimationType },
    tablet: { size: 'md' as NeonLogoSize, intensity: 'subtle' as GlowIntensity, animation: 'hover' as AnimationType },
    desktop: { size: 'md' as NeonLogoSize, intensity: 'subtle' as GlowIntensity, animation: 'hover' as AnimationType },
  },
  hero: {
    mobile: { size: 'lg' as NeonLogoSize, intensity: 'medium' as GlowIntensity, animation: 'entrance' as AnimationType },
    tablet: { size: 'xl' as NeonLogoSize, intensity: 'strong' as GlowIntensity, animation: 'entrance' as AnimationType },
    desktop: { size: 'xl' as NeonLogoSize, intensity: 'strong' as GlowIntensity, animation: 'entrance' as AnimationType },
  },
  loading: {
    mobile: { size: 'md' as NeonLogoSize, intensity: 'subtle' as GlowIntensity, animation: 'pulse' as AnimationType },
    tablet: { size: 'lg' as NeonLogoSize, intensity: 'medium' as GlowIntensity, animation: 'pulse' as AnimationType },
    desktop: { size: 'lg' as NeonLogoSize, intensity: 'medium' as GlowIntensity, animation: 'pulse' as AnimationType },
  },
  footer: {
    mobile: { size: 'sm' as NeonLogoSize, intensity: 'subtle' as GlowIntensity, animation: 'none' as AnimationType },
    tablet: { size: 'sm' as NeonLogoSize, intensity: 'subtle' as GlowIntensity, animation: 'none' as AnimationType },
    desktop: { size: 'sm' as NeonLogoSize, intensity: 'subtle' as GlowIntensity, animation: 'none' as AnimationType },
  },
};

/**
 * Detect user preferences
 */
function getUserPreferences() {
  if (typeof window === 'undefined') {
    return {
      prefersReducedMotion: false,
      prefersDarkMode: true,
    };
  }

  return {
    prefersReducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    prefersDarkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
  };
}

/**
 * Detect screen size
 */
function getScreenSize(breakpoints?: { mobile?: number; tablet?: number; desktop?: number }) {
  if (typeof window === 'undefined') {
    return 'desktop';
  }

  const width = window.innerWidth;
  const bp = {
    mobile: breakpoints?.mobile ?? 640,
    tablet: breakpoints?.tablet ?? 1024,
  };

  if (width < bp.mobile) return 'mobile';
  if (width < bp.tablet) return 'tablet';
  return 'desktop';
}

/**
 * Hook implementation
 */
export function useResponsiveNeonLogo(
  options: ResponsiveNeonLogoOptions = {}
): ResponsiveNeonLogoResult {
  const {
    context = 'header',
    forceSize,
    forceIntensity,
    forceAnimation,
    performanceMode = false,
    breakpoints,
  } = options;

  const config = useMemo(() => {
    // Get user preferences
    const { prefersReducedMotion, prefersDarkMode } = getUserPreferences();

    // Get screen size
    const screenSize = getScreenSize(breakpoints);

    // Get base config for context and screen size
    const baseConfig = CONTEXT_DEFAULTS[context][screenSize as keyof typeof CONTEXT_DEFAULTS[typeof context]];

    // Apply forced values
    let size = forceSize ?? baseConfig.size;
    let intensity = forceIntensity ?? baseConfig.intensity;
    let animation = forceAnimation ?? baseConfig.animation;

    // Performance mode: reduce intensity and disable animations
    if (performanceMode) {
      if (intensity === 'ultra') intensity = 'strong';
      if (intensity === 'strong') intensity = 'medium';
      animation = 'none';
    }

    // Respect reduced motion preference
    if (prefersReducedMotion && !forceAnimation) {
      animation = 'none';
    }

    // Mobile optimizations (unless forced)
    if (screenSize === 'mobile' && !forceIntensity) {
      if (intensity === 'ultra') intensity = 'strong';
      if (intensity === 'strong' && context !== 'hero') intensity = 'medium';
    }

    // Light mode adjustments (reduce glow)
    let className = '';
    if (!prefersDarkMode) {
      className = 'neon-light-mode';
    }

    // Add drop-shadow method for better mobile performance
    if (screenSize === 'mobile' && !performanceMode) {
      className += ' drop-shadow-method';
    }

    return {
      size,
      intensity,
      animation,
      className: className.trim() || undefined,
    };
  }, [context, forceSize, forceIntensity, forceAnimation, performanceMode, breakpoints]);

  return config;
}

/**
 * Hook variant for context-specific defaults
 */
export function useHeaderNeonLogo(overrides?: Partial<ResponsiveNeonLogoOptions>) {
  return useResponsiveNeonLogo({ context: 'header', ...overrides });
}

export function useHeroNeonLogo(overrides?: Partial<ResponsiveNeonLogoOptions>) {
  return useResponsiveNeonLogo({ context: 'hero', ...overrides });
}

export function useLoadingNeonLogo(overrides?: Partial<ResponsiveNeonLogoOptions>) {
  return useResponsiveNeonLogo({ context: 'loading', ...overrides });
}

export function useFooterNeonLogo(overrides?: Partial<ResponsiveNeonLogoOptions>) {
  return useResponsiveNeonLogo({ context: 'footer', ...overrides });
}

/**
 * Usage Examples:
 *
 * 1. Basic usage with auto-detection:
 * ```tsx
 * function Header() {
 *   const logoProps = useHeaderNeonLogo();
 *   return <NeonLogo {...logoProps} />;
 * }
 * ```
 *
 * 2. With forced settings:
 * ```tsx
 * function Hero() {
 *   const logoProps = useHeroNeonLogo({
 *     forceIntensity: 'ultra',
 *   });
 *   return <NeonLogo {...logoProps} />;
 * }
 * ```
 *
 * 3. Performance mode:
 * ```tsx
 * function LowEndDeviceHeader() {
 *   const logoProps = useHeaderNeonLogo({
 *     performanceMode: true,
 *   });
 *   return <NeonLogo {...logoProps} />;
 * }
 * ```
 *
 * 4. Custom breakpoints:
 * ```tsx
 * function CustomResponsiveLogo() {
 *   const logoProps = useResponsiveNeonLogo({
 *     context: 'hero',
 *     breakpoints: {
 *       mobile: 480,
 *       tablet: 768,
 *     },
 *   });
 *   return <NeonLogo {...logoProps} />;
 * }
 * ```
 */
