'use client';

import { motion } from 'framer-motion';
import { Plus, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatOdds, formatEV } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface PropCardProps {
  player: string;
  market: string;
  line: number;
  selection: string;
  odds: number;
  expectedValue: number;
  probability: number;
  sportsbook: string;
  teams: string[];
  sport: string;
  isLive?: boolean;
  onAddToSlip?: () => void;
}

export function PropCard({
  player,
  market,
  line,
  selection,
  odds,
  expectedValue,
  probability,
  sportsbook,
  teams,
  sport,
  isLive,
  onAddToSlip,
}: PropCardProps) {
  const ev = formatEV(expectedValue);

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="group relative overflow-hidden border-2 hover:border-primary/50 hover:shadow-lg transition-all">
        {isLive && (
          <div className="absolute right-0 top-0">
            <Badge variant="live" className="rounded-tl-none rounded-br-none">
              LIVE
            </Badge>
          </div>
        )}

        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-lg">{player}</h3>
              <p className="text-sm text-muted-foreground">
                {market} · {selection} {line}
              </p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Odds and EV */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground">Odds</p>
              <p className="odds-american text-xl">{formatOdds(odds)}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Expected Value</p>
              <p className={cn('text-xl font-bold', ev.className)}>{ev.text}</p>
            </div>
          </div>

          {/* Probability Bar */}
          <div>
            <div className="flex justify-between text-xs text-muted-foreground mb-1">
              <span>Win Probability</span>
              <span>{(probability * 100).toFixed(1)}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${probability * 100}%` }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="h-full bg-profit rounded-full"
              />
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between pt-2 border-t">
            <div className="text-xs text-muted-foreground">
              <div>{teams.join(' @ ')}</div>
              <div>{sportsbook} · {sport}</div>
            </div>
            <Button
              size="sm"
              onClick={onAddToSlip}
              className="opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <Plus className="h-4 w-4 mr-1" />
              Add
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
