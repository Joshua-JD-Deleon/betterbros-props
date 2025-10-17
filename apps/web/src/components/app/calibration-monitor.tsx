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
    <button className="flex items-center gap-2 rounded-lg border border-border/50 bg-card/50 px-4 py-2 text-sm transition-colors hover:bg-accent/50 hover:border-border">
      <Activity className="h-4 w-4 text-muted-foreground" />
      <span className="text-muted-foreground">Model Calibration:</span>
      <span
        className="font-mono text-sm font-medium text-foreground/90"
      >
        {calibrationScore.toFixed(1)}%
      </span>
    </button>
  );
}
