'use client';

import { TrendingUp, Zap, Target, Activity } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { mockTrendingProps } from '@/lib/mock-data';

const iconMap: Record<string, any> = {
  profit: TrendingUp,
  live: Zap,
  primary: Target,
  secondary: Activity,
};

const trends = mockTrendingProps.map((trend, index) => ({
  id: `trend-${index}`,
  label: trend.label,
  icon: iconMap[trend.color] || Target,
  count: trend.count,
  variant: trend.color as 'profit' | 'loss' | 'live' | 'default',
}));

export function TrendChips() {
  return (
    <div className="flex flex-wrap gap-2">
      {trends.map((trend) => {
        const Icon = trend.icon;
        return (
          <button
            key={trend.id}
            className={cn(
              'flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition-all hover:scale-105 hover:shadow-md',
              trend.variant === 'profit' &&
                'border-profit/30 bg-profit/10 text-profit hover:bg-profit/20',
              trend.variant === 'loss' &&
                'border-loss/30 bg-loss/10 text-loss hover:bg-loss/20',
              trend.variant === 'live' &&
                'border-live/30 bg-live/10 text-live hover:bg-live/20',
              trend.variant === 'default' &&
                'border-primary/30 bg-primary/10 text-primary hover:bg-primary/20'
            )}
          >
            <Icon className="h-4 w-4" />
            <span>{trend.label}</span>
            <Badge
              variant="secondary"
              className="ml-1 h-5 min-w-[20px] rounded-full px-1.5 text-xs"
            >
              {trend.count}
            </Badge>
          </button>
        );
      })}
    </div>
  );
}
