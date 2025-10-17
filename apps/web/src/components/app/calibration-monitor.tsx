'use client';

import { Activity } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { mockCalibration } from '@/lib/mock-data';

export function CalibrationMonitor() {
  const calibrationScore = mockCalibration.overall_accuracy;
  const status = calibrationScore >= 90 ? 'excellent' : calibrationScore >= 80 ? 'good' : 'fair';

  return (
    <button className="flex items-center gap-2 rounded-lg border bg-card px-4 py-2 text-sm transition-colors hover:bg-accent">
      <Activity className="h-4 w-4" />
      <span className="text-muted-foreground">Model Calibration:</span>
      <Badge
        variant={status === 'excellent' ? 'profit' : 'default'}
        className="font-mono"
      >
        {calibrationScore.toFixed(1)}%
      </Badge>
    </button>
  );
}
