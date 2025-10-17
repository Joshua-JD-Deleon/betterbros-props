'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowUpDown, Plus } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useSlipStore } from '@/lib/store/slip-store';
import { formatOdds, formatEV } from '@/lib/utils';
import { mockProps } from '@/lib/mock-data';

export function PropsTable() {
  const [sortField, setSortField] = useState<'ev' | 'odds' | 'probability'>('ev');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const { addEntry } = useSlipStore();

  const handleSort = (field: 'ev' | 'odds' | 'probability') => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const handleAddToSlip = (prop: typeof mockProps[0]) => {
    addEntry({
      id: prop.id,
      propId: prop.id,
      market: prop.stat_type,
      selection: `${prop.player} Over ${prop.line}`,
      odds: prop.over_odds,
      stake: 0,
      expectedValue: prop.ev,
      probability: prop.confidence / 100,
      sportsbook: prop.market,
      gameInfo: {
        sport: 'NFL',
        league: 'NFL',
        teams: [prop.team, prop.opponent.replace('vs ', '').replace('@ ', '')],
        startTime: prop.game_time,
      },
    });
  };

  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Player</TableHead>
            <TableHead>Market</TableHead>
            <TableHead>Line</TableHead>
            <TableHead>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleSort('odds')}
                className="h-8 gap-1"
              >
                Odds
                <ArrowUpDown className="h-3 w-3" />
              </Button>
            </TableHead>
            <TableHead>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleSort('probability')}
                className="h-8 gap-1"
              >
                Probability
                <ArrowUpDown className="h-3 w-3" />
              </Button>
            </TableHead>
            <TableHead>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleSort('ev')}
                className="h-8 gap-1"
              >
                EV
                <ArrowUpDown className="h-3 w-3" />
              </Button>
            </TableHead>
            <TableHead>Book</TableHead>
            <TableHead>Game</TableHead>
            <TableHead className="w-[100px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {mockProps.map((prop, index) => {
            const ev = formatEV(prop.ev);

            return (
              <motion.tr
                key={prop.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="group prop-card-hover"
              >
                <TableCell className="font-medium">
                  <div className="flex items-center gap-2">
                    {prop.is_live && (
                      <Badge variant="live" className="text-xs">
                        LIVE
                      </Badge>
                    )}
                    {prop.player}
                  </div>
                </TableCell>
                <TableCell>
                  <span className="text-muted-foreground">{prop.stat_type}</span>
                </TableCell>
                <TableCell>
                  <span className="font-semibold">
                    Over {prop.line}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="odds-american">{formatOdds(prop.over_odds)}</span>
                </TableCell>
                <TableCell>
                  <span className="text-sm">
                    {prop.confidence.toFixed(1)}%
                  </span>
                </TableCell>
                <TableCell>
                  <span className={ev.className}>{ev.text}</span>
                </TableCell>
                <TableCell>
                  <span className="text-xs text-muted-foreground">
                    {prop.market}
                  </span>
                </TableCell>
                <TableCell>
                  <div className="text-xs text-muted-foreground">
                    <div>{prop.team} {prop.opponent}</div>
                    <div className="text-xs opacity-70">NFL</div>
                  </div>
                </TableCell>
                <TableCell>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleAddToSlip(prop)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add
                  </Button>
                </TableCell>
              </motion.tr>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
