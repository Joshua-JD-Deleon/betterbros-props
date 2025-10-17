'use client';

import React, { useState } from 'react';
import { cn } from '@/lib/utils';

/**
 * Size variants for the neon logo
 */
export type NeonLogoSize = 'sm' | 'md' | 'lg' | 'xl';

/**
 * Glow intensity levels
 */
export type GlowIntensity = 'subtle' | 'medium' | 'strong' | 'ultra';

/**
 * Animation types
 */
export type AnimationType = 'none' | 'pulse' | 'hover' | 'shimmer' | 'entrance';

export interface NeonLogoProps {
  /**
   * Size variant
   * @default 'md'
   */
  size?: NeonLogoSize;

  /**
   * Glow intensity
   * @default 'medium'
   */
  intensity?: GlowIntensity;

  /**
   * Animation type
   * @default 'none'
   */
  animation?: AnimationType;

  /**
   * Additional CSS classes
   */
  className?: string;

  /**
   * Whether to use inline SVG (true) or external file (false)
   * @default true
   */
  inline?: boolean;

  /**
   * Path to external SVG file (if inline is false)
   */
  svgPath?: string;

  /**
   * Callback when logo is clicked
   */
  onClick?: () => void;

  /**
   * Whether the logo is clickable
   * @default false
   */
  clickable?: boolean;

  /**
   * Custom aria-label for accessibility
   * @default 'Company Logo'
   */
  ariaLabel?: string;
}

const sizeClasses: Record<NeonLogoSize, string> = {
  sm: 'w-32 h-8',
  md: 'w-48 h-12',
  lg: 'w-64 h-16',
  xl: 'w-80 h-20',
};

const intensityClasses: Record<GlowIntensity, string> = {
  subtle: 'neon-glow-subtle',
  medium: 'neon-glow-medium',
  strong: 'neon-glow-strong',
  ultra: 'neon-glow-ultra',
};

const animationClasses: Record<AnimationType, string> = {
  none: '',
  pulse: 'neon-pulse',
  hover: 'neon-hover-glow',
  shimmer: 'neon-shimmer',
  entrance: 'neon-entrance',
};

/**
 * NeonLogo Component
 *
 * A React component that wraps the company logo with customizable neon glow effects.
 * Supports multiple size variants, glow intensities, and animation options.
 *
 * @example
 * ```tsx
 * // Basic usage
 * <NeonLogo />
 *
 * // With custom size and intensity
 * <NeonLogo size="lg" intensity="strong" />
 *
 * // With pulse animation
 * <NeonLogo animation="pulse" />
 *
 * // Clickable with hover effect
 * <NeonLogo
 *   clickable
 *   animation="hover"
 *   onClick={() => router.push('/')}
 * />
 * ```
 */
export const NeonLogo: React.FC<NeonLogoProps> = ({
  size = 'md',
  intensity = 'medium',
  animation = 'none',
  className,
  inline = false,
  svgPath = '/logo.svg',
  onClick,
  clickable = false,
  ariaLabel = 'BetterBros Logo',
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const containerClasses = cn(
    'neon-logo-container',
    'relative inline-block',
    sizeClasses[size],
    intensityClasses[intensity],
    animationClasses[animation],
    clickable && 'cursor-pointer',
    isHovered && animation === 'hover' && 'neon-hover-active',
    className
  );

  const handleClick = () => {
    if (clickable && onClick) {
      onClick();
    }
  };

  return (
    <div
      className={containerClasses}
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      role={clickable ? 'button' : undefined}
      tabIndex={clickable ? 0 : undefined}
      aria-label={ariaLabel}
      onKeyDown={(e) => {
        if (clickable && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      {inline ? (
        <InlineNeonSVG />
      ) : (
        <img
          src={svgPath}
          alt={ariaLabel}
          className="w-full h-full object-contain"
        />
      )}

      {/* SVG Filter Definitions for High-Quality Glow */}
      <svg className="absolute w-0 h-0" aria-hidden="true">
        <defs>
          {/* Subtle Glow Filter */}
          <filter id="neon-glow-subtle" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur1" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur2" />
            <feMerge>
              <feMergeNode in="blur2" />
              <feMergeNode in="blur1" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Medium Glow Filter */}
          <filter id="neon-glow-medium" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur1" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="6" result="blur2" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="12" result="blur3" />
            <feMerge>
              <feMergeNode in="blur3" />
              <feMergeNode in="blur2" />
              <feMergeNode in="blur1" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Strong Glow Filter */}
          <filter id="neon-glow-strong" x="-150%" y="-150%" width="400%" height="400%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur1" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="8" result="blur2" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="16" result="blur3" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="24" result="blur4" />
            <feMerge>
              <feMergeNode in="blur4" />
              <feMergeNode in="blur3" />
              <feMergeNode in="blur2" />
              <feMergeNode in="blur1" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          {/* Ultra Glow Filter */}
          <filter id="neon-glow-ultra" x="-200%" y="-200%" width="500%" height="500%">
            <feGaussianBlur in="SourceGraphic" stdDeviation="5" result="blur1" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur2" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="20" result="blur3" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="30" result="blur4" />
            <feGaussianBlur in="SourceGraphic" stdDeviation="40" result="blur5" />
            <feMerge>
              <feMergeNode in="blur5" />
              <feMergeNode in="blur4" />
              <feMergeNode in="blur3" />
              <feMergeNode in="blur2" />
              <feMergeNode in="blur1" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
      </svg>
    </div>
  );
};

/**
 * Inline SVG with optimized logo markup
 * This is a simplified version - replace with your actual logo SVG
 */
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

      {/*
        Replace this placeholder with your actual logo SVG content
        The actual SVG from the file should be inserted here
        For now, this is a placeholder that shows the structure
      */}
      <g className="logo-content">
        {/* Your logo paths go here */}
        <text x="200" y="50" textAnchor="middle" className="logo-cream-primary" fontSize="24">
          Insert Logo SVG
        </text>
      </g>
    </svg>
  );
};

export default NeonLogo;
