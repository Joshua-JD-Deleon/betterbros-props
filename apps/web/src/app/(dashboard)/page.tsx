import { Suspense } from 'react';
import { PropsTable } from '@/components/app/props-table';
import { TrendChips } from '@/components/app/trend-chips';
import { CalibrationMonitor } from '@/components/app/calibration-monitor';
import { Card } from '@/components/ui/card';

export default function DashboardPage() {
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

      {/* Trend Chips */}
      <Suspense fallback={<div className="h-12 bg-muted animate-pulse rounded" />}>
        <TrendChips />
      </Suspense>

      {/* Main Props Table */}
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

      {/* Analytics Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Active Props</h3>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold">1,247</span>
            <span className="text-sm text-profit">+12%</span>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Avg EV</h3>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold ev-positive">+4.2%</span>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Live Games</h3>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold">8</span>
            <span className="live-indicator text-xs px-2 py-0.5 rounded-full">LIVE</span>
          </div>
        </Card>
      </div>
    </div>
  );
}
