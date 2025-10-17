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
import { useUIStore } from '@/lib/store/ui-store';
import { formatOdds, formatEV } from '@/lib/utils';
import { mockProps, type MockProp } from '@/lib/mock-data';
import type { Sport, StatCategory } from '@/lib/types/stats';
import { getStatAbbreviation, getStatsByCategory } from '@/lib/types/stats';
import { getSportIcon, getSportColor, SportFilter } from './sport-filter';

interface PropsTableProps {
  showFilters?: boolean;
}

export function PropsTable({ showFilters = true }: PropsTableProps) {
  const [sortField, setSortField] = useState<'ev' | 'odds' | 'probability'>('ev');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedSport, setSelectedSport] = useState<Sport | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<StatCategory | null>(null);
  const { addEntry } = useSlipStore();

  const handleSort = (field: 'ev' | 'odds' | 'probability') => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  // Filter props based on selected sport and category
  const filteredProps = mockProps.filter((prop) => {
    if (selectedSport && prop.sport !== selectedSport) return false;
    if (selectedCategory) {
      const categoryStats = getStatsByCategory(prop.sport, selectedCategory);
      if (!categoryStats.includes(prop.stat_type)) return false;
    }
    return true;
  });

  // Sort props
  const sortedProps = [...filteredProps].sort((a, b) => {
    let comparison = 0;
    switch (sortField) {
      case 'ev':
        comparison = a.ev - b.ev;
        break;
      case 'odds':
        comparison = a.over_odds - b.over_odds;
        break;
      case 'probability':
        comparison = a.confidence - b.confidence;
        break;
    }
    return sortOrder === 'asc' ? comparison : -comparison;
  });

  // Calculate prop counts by sport
  const propCounts: Partial<Record<Sport, number>> = mockProps.reduce((acc, prop) => {
    acc[prop.sport] = (acc[prop.sport] || 0) + 1;
    return acc;
  }, {} as Partial<Record<Sport, number>>);

  const handleAddToSlip = (prop: MockProp) => {
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
        sport: prop.sport,
        league: prop.sport,
        teams: [prop.team, prop.opponent.replace('vs ', '').replace('@ ', '')],
        startTime: prop.game_time,
      },
    });
    // Open the drawer to show the added prop
    useUIStore.getState().openDrawer();
  };

  return (
    <div className="space-y-4">
      {/* Sport and Category Filters */}
      {showFilters && (
        <SportFilter
          selectedSport={selectedSport}
          selectedCategory={selectedCategory}
          onSportChange={setSelectedSport}
          onCategoryChange={setSelectedCategory}
          propCounts={propCounts}
        />
      )}

      {/* Props Table */}
      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Sport</TableHead>
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
            {sortedProps.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} className="h-24 text-center text-muted-foreground">
                  No props found matching the selected filters.
                </TableCell>
              </TableRow>
            ) : (
              sortedProps.map((prop, index) => {
                const ev = formatEV(prop.ev);
                const SportIcon = getSportIcon(prop.sport);
                const sportColor = getSportColor(prop.sport);

                return (
                  <motion.tr
                    key={prop.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: Math.min(index * 0.05, 1) }}
                    className="group prop-card-hover"
                  >
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <SportIcon className={`h-4 w-4 ${sportColor}`} />
                        <span className="text-xs font-medium">{prop.sport}</span>
                      </div>
                    </TableCell>
                    <TableCell className="font-medium">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          {prop.is_live && (
                            <Badge variant="live" className="text-xs">
                              LIVE
                            </Badge>
                          )}
                          {prop.player}
                        </div>
                        {prop.position && (
                          <Badge variant="outline" className="text-xs w-fit">
                            {prop.position}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-muted-foreground text-sm">
                        {getStatAbbreviation(prop.sport, prop.stat_type)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className="font-semibold">
                        {prop.line % 1 === 0.5 ? prop.line : prop.line.toFixed(1)}
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
                        <div className="text-xs opacity-70">{prop.sport}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <button
                        onClick={() => handleAddToSlip(prop)}
                        className="flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1.5 text-sm font-medium text-primary transition-all hover:scale-105 hover:bg-primary/20 hover:shadow-md"
                      >
                        <Plus className="h-4 w-4" />
                        Add to Slip
                      </button>
                    </TableCell>
                  </motion.tr>
                );
              })
            )}
          </TableBody>
        </Table>

        {/* Results count */}
        {sortedProps.length > 0 && (
          <div className="border-t px-4 py-3 text-sm text-muted-foreground">
            Showing {sortedProps.length} of {mockProps.length} props
          </div>
        )}
      </div>
    </div>
  );
}
