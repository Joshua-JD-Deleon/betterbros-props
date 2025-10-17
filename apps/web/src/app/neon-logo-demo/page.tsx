'use client';

import { NeonLogo } from '@/components/brand';
import type { NeonLogoSize, GlowIntensity, AnimationType } from '@/components/brand';
import { useState } from 'react';

/**
 * Neon Logo Demo & Testing Page
 *
 * Interactive page to preview all logo variants, intensities, and animations.
 * Use this to test and choose the right settings for your implementation.
 *
 * Access at: http://localhost:3000/neon-logo-demo
 */
export default function NeonLogoDemoPage() {
  const [size, setSize] = useState<NeonLogoSize>('md');
  const [intensity, setIntensity] = useState<GlowIntensity>('medium');
  const [animation, setAnimation] = useState<AnimationType>('none');
  const [background, setBackground] = useState('#090809');

  const sizes: NeonLogoSize[] = ['sm', 'md', 'lg', 'xl'];
  const intensities: GlowIntensity[] = ['subtle', 'medium', 'strong', 'ultra'];
  const animations: AnimationType[] = ['none', 'pulse', 'hover', 'shimmer', 'entrance'];
  const backgrounds = [
    { name: 'Black', value: '#000000' },
    { name: 'Dark Gray', value: '#090809' },
    { name: 'Gray', value: '#1f2937' },
    { name: 'Blue Dark', value: '#0f172a' },
    { name: 'Green Dark', value: '#052e16' },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">Neon Logo Demo & Testing</h1>
          <p className="text-sm text-gray-400">
            Interactive preview of all logo variants
          </p>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Left Column: Controls */}
          <div className="space-y-6">
            <div className="rounded-lg border border-gray-800 bg-gray-800/50 p-6">
              <h2 className="mb-4 text-xl font-semibold">Controls</h2>

              {/* Size Control */}
              <div className="mb-6">
                <label className="mb-2 block text-sm font-medium text-gray-300">
                  Size: <span className="text-green-400">{size}</span>
                </label>
                <div className="flex gap-2">
                  {sizes.map((s) => (
                    <button
                      key={s}
                      onClick={() => setSize(s)}
                      className={`rounded px-4 py-2 text-sm font-medium transition-colors ${
                        size === s
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {s.toUpperCase()}
                    </button>
                  ))}
                </div>
                <p className="mt-2 text-xs text-gray-500">
                  sm: 128px | md: 192px | lg: 256px | xl: 320px
                </p>
              </div>

              {/* Intensity Control */}
              <div className="mb-6">
                <label className="mb-2 block text-sm font-medium text-gray-300">
                  Intensity: <span className="text-green-400">{intensity}</span>
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {intensities.map((i) => (
                    <button
                      key={i}
                      onClick={() => setIntensity(i)}
                      className={`rounded px-4 py-2 text-sm font-medium transition-colors ${
                        intensity === i
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {i.charAt(0).toUpperCase() + i.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Animation Control */}
              <div className="mb-6">
                <label className="mb-2 block text-sm font-medium text-gray-300">
                  Animation: <span className="text-green-400">{animation}</span>
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {animations.map((a) => (
                    <button
                      key={a}
                      onClick={() => setAnimation(a)}
                      className={`rounded px-4 py-2 text-sm font-medium transition-colors ${
                        animation === a
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {a.charAt(0).toUpperCase() + a.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Background Control */}
              <div>
                <label className="mb-2 block text-sm font-medium text-gray-300">
                  Background
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {backgrounds.map((bg) => (
                    <button
                      key={bg.value}
                      onClick={() => setBackground(bg.value)}
                      className={`flex items-center gap-2 rounded px-4 py-2 text-sm font-medium transition-colors ${
                        background === bg.value
                          ? 'bg-green-500 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      <div
                        className="h-4 w-4 rounded border border-gray-600"
                        style={{ backgroundColor: bg.value }}
                      />
                      {bg.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Code Preview */}
            <div className="rounded-lg border border-gray-800 bg-gray-800/50 p-6">
              <h2 className="mb-4 text-xl font-semibold">Code</h2>
              <pre className="overflow-x-auto rounded bg-gray-900 p-4 text-xs text-gray-300">
                <code>{`<NeonLogo
  size="${size}"
  intensity="${intensity}"
  animation="${animation}"
/>`}</code>
              </pre>
            </div>

            {/* Performance Info */}
            <div className="rounded-lg border border-gray-800 bg-gray-800/50 p-6">
              <h2 className="mb-4 text-xl font-semibold">Performance Info</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">CPU Impact:</span>
                  <span
                    className={
                      intensity === 'subtle' || intensity === 'medium'
                        ? 'text-green-400'
                        : intensity === 'strong'
                        ? 'text-yellow-400'
                        : 'text-orange-400'
                    }
                  >
                    {intensity === 'subtle'
                      ? 'Very Low'
                      : intensity === 'medium'
                      ? 'Low'
                      : intensity === 'strong'
                      ? 'Medium'
                      : 'High'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Mobile Friendly:</span>
                  <span
                    className={
                      intensity === 'subtle' || intensity === 'medium'
                        ? 'text-green-400'
                        : 'text-yellow-400'
                    }
                  >
                    {intensity === 'subtle' || intensity === 'medium'
                      ? 'Yes'
                      : 'Consider subtle/medium'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Animation FPS:</span>
                  <span className="text-green-400">
                    {animation === 'none' ? 'N/A' : '60 fps'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Preview */}
          <div className="space-y-6">
            {/* Main Preview */}
            <div
              className="flex min-h-[400px] items-center justify-center rounded-lg border border-gray-700 p-8"
              style={{ backgroundColor: background }}
            >
              <NeonLogo
                size={size}
                intensity={intensity}
                animation={animation}
                key={`${size}-${intensity}-${animation}`}
              />
            </div>

            {/* Use Cases */}
            <div className="rounded-lg border border-gray-800 bg-gray-800/50 p-6">
              <h2 className="mb-4 text-xl font-semibold">Recommended Use Cases</h2>
              <div className="space-y-3 text-sm">
                {intensity === 'subtle' && (
                  <div className="rounded bg-green-900/20 p-3 text-green-300">
                    <strong>Perfect for:</strong> Dashboard headers, navigation bars,
                    frequent appearance, mobile devices
                  </div>
                )}
                {intensity === 'medium' && (
                  <div className="rounded bg-green-900/20 p-3 text-green-300">
                    <strong>Perfect for:</strong> Landing pages, section headers,
                    featured content, desktop primary placement
                  </div>
                )}
                {intensity === 'strong' && (
                  <div className="rounded bg-orange-900/20 p-3 text-orange-300">
                    <strong>Perfect for:</strong> Hero sections, splash screens,
                    marketing pages, special events
                  </div>
                )}
                {intensity === 'ultra' && (
                  <div className="rounded bg-orange-900/20 p-3 text-orange-300">
                    <strong>Perfect for:</strong> Promotional pages, loading screens,
                    special announcements, limited-time offers
                  </div>
                )}
              </div>
            </div>

            {/* All Sizes Preview */}
            <div className="rounded-lg border border-gray-800 bg-gray-800/50 p-6">
              <h2 className="mb-4 text-xl font-semibold">All Sizes</h2>
              <div
                className="flex flex-wrap items-end justify-center gap-8 rounded-lg p-6"
                style={{ backgroundColor: background }}
              >
                {sizes.map((s) => (
                  <div key={s} className="text-center">
                    <NeonLogo
                      size={s}
                      intensity={intensity}
                      animation="none"
                    />
                    <p className="mt-2 text-xs text-gray-400">{s.toUpperCase()}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* All Intensities Preview */}
            <div className="rounded-lg border border-gray-800 bg-gray-800/50 p-6">
              <h2 className="mb-4 text-xl font-semibold">All Intensities</h2>
              <div
                className="grid grid-cols-2 gap-4 rounded-lg p-6"
                style={{ backgroundColor: background }}
              >
                {intensities.map((i) => (
                  <div key={i} className="text-center">
                    <NeonLogo
                      size="md"
                      intensity={i}
                      animation="none"
                    />
                    <p className="mt-2 text-xs text-gray-400">
                      {i.charAt(0).toUpperCase() + i.slice(1)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Context Examples */}
        <div className="mt-8 space-y-6">
          <h2 className="text-2xl font-bold">Context Examples</h2>

          {/* Dashboard Header Example */}
          <div className="rounded-lg border border-gray-800 bg-gray-800/50 p-6">
            <h3 className="mb-4 text-lg font-semibold">Dashboard Header</h3>
            <div className="rounded-lg border border-gray-700 bg-gray-900">
              <div className="flex items-center justify-between border-b border-gray-800 px-6 py-4">
                <NeonLogo size="md" intensity="subtle" animation="hover" />
                <nav className="flex gap-6 text-sm text-gray-300">
                  <a href="#" className="hover:text-white">Dashboard</a>
                  <a href="#" className="hover:text-white">Bets</a>
                  <a href="#" className="hover:text-white">Leaderboard</a>
                </nav>
              </div>
              <div className="p-6 text-gray-400">
                Dashboard content goes here...
              </div>
            </div>
          </div>

          {/* Hero Section Example */}
          <div className="rounded-lg border border-gray-800 bg-gray-800/50 p-6">
            <h3 className="mb-4 text-lg font-semibold">Hero Section</h3>
            <div className="rounded-lg bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 py-16 text-center">
              <div className="mb-8 flex justify-center">
                <NeonLogo size="xl" intensity="strong" animation="entrance" />
              </div>
              <h1 className="mb-4 text-4xl font-bold">Welcome to BetterBros</h1>
              <p className="mb-8 text-xl text-gray-300">
                Bet smarter, win together
              </p>
              <button className="rounded-lg bg-green-500 px-8 py-3 font-semibold text-white hover:bg-green-600">
                Get Started
              </button>
            </div>
          </div>

          {/* Loading State Example */}
          <div className="rounded-lg border border-gray-800 bg-gray-800/50 p-6">
            <h3 className="mb-4 text-lg font-semibold">Loading State</h3>
            <div className="flex items-center justify-center rounded-lg bg-gray-900 py-20">
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
          </div>
        </div>
      </div>
    </div>
  );
}
