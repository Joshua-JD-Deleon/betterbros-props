'use client';

import { useState } from 'react';
import { Check } from 'lucide-react';
import { useUIStore } from '@/lib/store/ui-store';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

const sports = ['NFL', 'NBA', 'NHL', 'MLB', 'NCAAF', 'NCAAB'];
const markets = [
  'Points',
  'Assists',
  'Rebounds',
  'Passing Yards',
  'Rushing Yards',
  'Receiving Yards',
  'Goals',
  'Shots',
];

export function FilterPanel() {
  const { filters, updateFilters, resetFilters } = useUIStore();

  const toggleSport = (sport: string) => {
    const newSports = filters.sports.includes(sport)
      ? filters.sports.filter((s) => s !== sport)
      : [...filters.sports, sport];
    updateFilters({ sports: newSports });
  };

  const toggleMarket = (market: string) => {
    const newMarkets = filters.markets.includes(market)
      ? filters.markets.filter((m) => m !== market)
      : [...filters.markets, market];
    updateFilters({ markets: newMarkets });
  };

  return (
    <div className="space-y-6">
      {/* Quick Filters */}
      <div>
        <h3 className="mb-3 text-sm font-semibold">Quick Filters</h3>
        <div className="space-y-2">
          <button
            onClick={() =>
              updateFilters({
                showPositiveEvOnly: !filters.showPositiveEvOnly,
              })
            }
            className={cn(
              'flex w-full items-center justify-between rounded-md border p-3 text-sm transition-colors hover:bg-accent',
              filters.showPositiveEvOnly && 'border-profit bg-profit/10'
            )}
          >
            <span>Positive EV Only</span>
            {filters.showPositiveEvOnly && (
              <Check className="h-4 w-4 text-profit" />
            )}
          </button>

          <button
            onClick={() =>
              updateFilters({ showLiveOnly: !filters.showLiveOnly })
            }
            className={cn(
              'flex w-full items-center justify-between rounded-md border p-3 text-sm transition-colors hover:bg-accent',
              filters.showLiveOnly && 'border-live bg-live/10'
            )}
          >
            <span>Live Games Only</span>
            {filters.showLiveOnly && <Check className="h-4 w-4 text-live" />}
          </button>
        </div>
      </div>

      {/* Sports */}
      <div>
        <h3 className="mb-3 text-sm font-semibold">Sports</h3>
        <div className="flex flex-wrap gap-2">
          {sports.map((sport) => (
            <Badge
              key={sport}
              variant={filters.sports.includes(sport) ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => toggleSport(sport)}
            >
              {sport}
            </Badge>
          ))}
        </div>
      </div>

      {/* Markets */}
      <div>
        <h3 className="mb-3 text-sm font-semibold">Markets</h3>
        <div className="space-y-1">
          {markets.map((market) => (
            <button
              key={market}
              onClick={() => toggleMarket(market)}
              className={cn(
                'flex w-full items-center justify-between rounded-md p-2 text-sm transition-colors hover:bg-accent',
                filters.markets.includes(market) && 'bg-accent'
              )}
            >
              <span>{market}</span>
              {filters.markets.includes(market) && (
                <Check className="h-4 w-4" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* EV Range */}
      <div>
        <h3 className="mb-3 text-sm font-semibold">Expected Value Range</h3>
        <div className="space-y-2">
          <input
            type="range"
            min="-10"
            max="20"
            step="0.5"
            value={filters.evRange[0]}
            onChange={(e) =>
              updateFilters({
                evRange: [Number(e.target.value), filters.evRange[1]],
              })
            }
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{filters.evRange[0]}%</span>
            <span>{filters.evRange[1]}%</span>
          </div>
        </div>
      </div>

      {/* Reset Button */}
      <Button
        variant="outline"
        className="w-full"
        onClick={resetFilters}
        size="sm"
      >
        Reset Filters
      </Button>
    </div>
  );
}
