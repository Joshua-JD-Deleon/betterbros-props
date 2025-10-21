'use client';

import { Suspense } from 'react';
import { PropsTable } from '@/components/app/props-table';
import { TrendChips } from '@/components/app/trend-chips';
import { CalibrationMonitor } from '@/components/app/calibration-monitor';
import { APIConnectionPanel } from '@/components/app/api-connection-panel';
import { RiskProfileSelector } from '@/components/app/risk-profile-selector';
import { TopSetsDisplay } from '@/components/app/top-sets';
import { Card } from '@/components/ui/card';
import { usePropsStore } from '@/lib/store/props-store';
import { useOptimizationStore } from '@/lib/store/optimization-store';

export default function DashboardPage() {
  const { props } = usePropsStore();
  const { topSets } = useOptimizationStore();

  return (
    <div className="flex flex-col gap-6">
      {/* Header Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Props Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Real-time props with calculated expected value
          </p>
        </div>

        <Suspense fallback={<div className="h-10 w-32 bg-muted animate-pulse rounded" />}>
          <CalibrationMonitor />
        </Suspense>
      </div>

      {/* API Connection Panel */}
      <Suspense fallback={<div className="h-24 bg-muted animate-pulse rounded-lg" />}>
        <APIConnectionPanel />
      </Suspense>

      {/* Trend Chips */}
      <Suspense fallback={<div className="h-12 bg-muted animate-pulse rounded" />}>
        <TrendChips />
      </Suspense>

      {/* Main Content - Two Column Layout */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Optimization Controls & Results */}
        <div className="lg:col-span-1 space-y-6">
          {/* Risk Profile Selector */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">Risk Profile</h2>
            <RiskProfileSelector />
          </Card>

          {/* Top Optimized Sets */}
          {topSets.length > 0 && (
            <div>
              <TopSetsDisplay />
            </div>
          )}
        </div>

        {/* Right Column - Props Table */}
        <div className="lg:col-span-2">
          <Card className="p-0">
            <Suspense
              fallback={
                <div className="p-8">
                  <div className="space-y-4">
                    {[...Array(10)].map((_, i) => (
                      <div key={i} className="h-16 bg-muted animate-pulse rounded" />
                    ))}
                  </div>
                </div>
              }
            >
              <PropsTable />
            </Suspense>
          </Card>
        </div>
      </div>

      {/* Analytics Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Active Props</h3>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold">{props.length}</span>
            <span className="text-sm text-muted-foreground">loaded</span>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Optimized Sets</h3>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold">{topSets.length}</span>
            <span className="text-sm text-muted-foreground">generated</span>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Avg EV</h3>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold ev-positive">
              {topSets.length > 0
                ? `+${(topSets.reduce((sum, set) => sum + set.ev, 0) / topSets.length).toFixed(1)}%`
                : '+0.0%'}
            </span>
          </div>
        </Card>
      </div>
    </div>
  );
}
