'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

// Mock correlation data
const mockData = [
  { x: 'Points', y: 'Rebounds', correlation: 0.45 },
  { x: 'Points', y: 'Assists', correlation: 0.32 },
  { x: 'Points', y: 'Steals', correlation: 0.15 },
  { x: 'Rebounds', y: 'Assists', correlation: -0.12 },
  { x: 'Rebounds', y: 'Steals', correlation: 0.08 },
  { x: 'Assists', y: 'Steals', correlation: 0.28 },
];

const stats = ['Points', 'Rebounds', 'Assists', 'Steals'];

export function CorrelationHeatmap() {
  const getCorrelation = (x: string, y: string) => {
    if (x === y) return 1;
    const match = mockData.find(
      (d) => (d.x === x && d.y === y) || (d.x === y && d.y === x)
    );
    return match?.correlation || 0;
  };

  const getColor = (value: number) => {
    if (value > 0.3) return 'bg-profit/80';
    if (value > 0.1) return 'bg-profit/40';
    if (value > -0.1) return 'bg-muted';
    if (value > -0.3) return 'bg-loss/40';
    return 'bg-loss/80';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prop Correlations</CardTitle>
        <CardDescription>
          Statistical correlations between different player props
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-5 gap-1">
          {/* Header row */}
          <div></div>
          {stats.map((stat) => (
            <div
              key={stat}
              className="text-xs font-medium text-center text-muted-foreground p-2"
            >
              {stat}
            </div>
          ))}

          {/* Data rows */}
          {stats.map((yAxis) => (
            <div key={yAxis} className="contents">
              <div className="text-xs font-medium text-right text-muted-foreground p-2">
                {yAxis}
              </div>
              {stats.map((xAxis) => {
                const value = getCorrelation(xAxis, yAxis);
                return (
                  <div
                    key={`${xAxis}-${yAxis}`}
                    className={cn(
                      'aspect-square rounded flex items-center justify-center text-xs font-mono font-semibold',
                      getColor(value)
                    )}
                  >
                    {value.toFixed(2)}
                  </div>
                );
              })}
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center justify-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 bg-loss/80 rounded"></div>
            <span>Negative</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 bg-muted rounded"></div>
            <span>Neutral</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-4 w-4 bg-profit/80 rounded"></div>
            <span>Positive</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
