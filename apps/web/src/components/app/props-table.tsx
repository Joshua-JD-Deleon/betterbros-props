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

// Mock data for demonstration
const mockProps = [
  {
    id: '1',
    propId: 'prop-1',
    player: 'LeBron James',
    market: 'Points',
    line: 27.5,
    selection: 'Over',
    odds: -110,
    sportsbook: 'DraftKings',
    probability: 0.52,
    expectedValue: 4.2,
    sport: 'NBA',
    league: 'NBA',
    teams: ['Lakers', 'Warriors'],
    startTime: '2025-10-14T19:00:00Z',
    isLive: false,
  },
  {
    id: '2',
    propId: 'prop-2',
    player: 'Patrick Mahomes',
    market: 'Passing Yards',
    line: 285.5,
    selection: 'Over',
    odds: 105,
    sportsbook: 'FanDuel',
    probability: 0.58,
    expectedValue: 6.8,
    sport: 'NFL',
    league: 'NFL',
    teams: ['Chiefs', 'Bills'],
    startTime: '2025-10-14T20:15:00Z',
    isLive: true,
  },
  {
    id: '3',
    propId: 'prop-3',
    player: 'Connor McDavid',
    market: 'Points',
    line: 1.5,
    selection: 'Over',
    odds: -115,
    sportsbook: 'BetMGM',
    probability: 0.51,
    expectedValue: 2.1,
    sport: 'NHL',
    league: 'NHL',
    teams: ['Oilers', 'Avalanche'],
    startTime: '2025-10-14T21:00:00Z',
    isLive: false,
  },
];

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
      propId: prop.propId,
      market: prop.market,
      selection: `${prop.player} ${prop.selection} ${prop.line}`,
      odds: prop.odds,
      stake: 0,
      expectedValue: prop.expectedValue,
      probability: prop.probability,
      sportsbook: prop.sportsbook,
      gameInfo: {
        sport: prop.sport,
        league: prop.league,
        teams: prop.teams,
        startTime: prop.startTime,
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
            const ev = formatEV(prop.expectedValue);

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
                    {prop.isLive && (
                      <Badge variant="live" className="text-xs">
                        LIVE
                      </Badge>
                    )}
                    {prop.player}
                  </div>
                </TableCell>
                <TableCell>
                  <span className="text-muted-foreground">{prop.market}</span>
                </TableCell>
                <TableCell>
                  <span className="font-semibold">
                    {prop.selection} {prop.line}
                  </span>
                </TableCell>
                <TableCell>
                  <span className="odds-american">{formatOdds(prop.odds)}</span>
                </TableCell>
                <TableCell>
                  <span className="text-sm">
                    {(prop.probability * 100).toFixed(1)}%
                  </span>
                </TableCell>
                <TableCell>
                  <span className={ev.className}>{ev.text}</span>
                </TableCell>
                <TableCell>
                  <span className="text-xs text-muted-foreground">
                    {prop.sportsbook}
                  </span>
                </TableCell>
                <TableCell>
                  <div className="text-xs text-muted-foreground">
                    <div>{prop.teams.join(' @ ')}</div>
                    <div className="text-xs opacity-70">{prop.sport}</div>
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
