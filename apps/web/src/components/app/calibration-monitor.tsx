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
    <button className="flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-4 py-2 text-sm font-medium text-primary transition-all hover:scale-105 hover:bg-primary/20 hover:shadow-md">
      <Activity className="h-4 w-4" />
      <span>Model Calibration:</span>
      <Badge
        variant="secondary"
        className="ml-1 h-5 min-w-[20px] rounded-full px-1.5 text-xs font-mono"
      >
        {calibrationScore.toFixed(1)}%
      </Badge>
    </button>
  );
}
