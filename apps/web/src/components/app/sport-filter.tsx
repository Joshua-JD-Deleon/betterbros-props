'use client';

import { useState } from 'react';
import { Trophy, Activity, Target, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { Sport, StatCategory } from '@/lib/types/stats';
import { getCategoriesForSport } from '@/lib/types/stats';

interface SportFilterProps {
  onSportChange?: (sport: Sport | null) => void;
  onCategoryChange?: (category: StatCategory | null) => void;
  selectedSport?: Sport | null;
  selectedCategory?: StatCategory | null;
  propCounts?: Partial<Record<Sport, number>>;
}

const SPORT_CONFIG: Record<Sport, { icon: typeof Trophy; label: string; color: string }> = {
  NFL: {
    icon: Trophy,
    label: 'NFL',
    color: 'text-orange-500 border-orange-500/30 bg-orange-500/10 hover:bg-orange-500/20',
  },
  NBA: {
    icon: Activity,
    label: 'NBA',
    color: 'text-blue-500 border-blue-500/30 bg-blue-500/10 hover:bg-blue-500/20',
  },
  MLB: {
    icon: Target,
    label: 'MLB',
    color: 'text-red-500 border-red-500/30 bg-red-500/10 hover:bg-red-500/20',
  },
  NHL: {
    icon: Shield,
    label: 'NHL',
    color: 'text-cyan-500 border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20',
  },
};

const CATEGORY_LABELS: Record<StatCategory, string> = {
  Passing: 'Passing',
  Rushing: 'Rushing',
  Receiving: 'Receiving',
  Defense: 'Defense',
  Kicking: 'Kicking',
  Combined: 'Combined',
  Scoring: 'Scoring',
  Rebounding: 'Rebounding',
  Playmaking: 'Playmaking',
  Pitching: 'Pitching',
  Batting: 'Batting',
  Skater: 'Skater',
  Goalie: 'Goalie',
};

export function SportFilter({
  onSportChange,
  onCategoryChange,
  selectedSport,
  selectedCategory,
  propCounts = {},
}: SportFilterProps) {
  const handleSportClick = (sport: Sport) => {
    const newSport = selectedSport === sport ? null : sport;
    onSportChange?.(newSport);
    // Reset category when changing sport
    if (newSport !== selectedSport) {
      onCategoryChange?.(null);
    }
  };

  const handleCategoryClick = (category: StatCategory) => {
    const newCategory = selectedCategory === category ? null : category;
    onCategoryChange?.(newCategory);
  };

  const availableCategories = selectedSport ? getCategoriesForSport(selectedSport) : [];

  return (
    <div className="space-y-4">
      {/* Sport Selection */}
      <div>
        <h3 className="text-sm font-medium text-muted-foreground mb-3">Sport</h3>
        <div className="flex flex-wrap gap-2">
          {(Object.entries(SPORT_CONFIG) as [Sport, typeof SPORT_CONFIG[Sport]][]).map(
            ([sport, config]) => {
              const Icon = config.icon;
              const count = propCounts[sport] || 0;
              const isSelected = selectedSport === sport;

              return (
                <button
                  key={sport}
                  onClick={() => handleSportClick(sport)}
                  className={cn(
                    'flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium transition-all hover:scale-105',
                    isSelected
                      ? config.color
                      : 'border-border bg-card hover:bg-accent text-foreground'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{config.label}</span>
                  {count > 0 && (
                    <Badge
                      variant="secondary"
                      className="ml-1 h-5 min-w-[20px] rounded-full px-1.5 text-xs"
                    >
                      {count}
                    </Badge>
                  )}
                </button>
              );
            }
          )}
        </div>
      </div>

      {/* Category Selection (only shown when sport is selected) */}
      {selectedSport && availableCategories.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-3">
            Category
            <button
              onClick={() => onCategoryChange?.(null)}
              className="ml-2 text-xs text-primary hover:underline"
            >
              Clear
            </button>
          </h3>
          <div className="flex flex-wrap gap-2">
            {availableCategories.map((category) => {
              const isSelected = selectedCategory === category;

              return (
                <button
                  key={category}
                  onClick={() => handleCategoryClick(category)}
                  className={cn(
                    'rounded-full border px-3 py-1.5 text-sm font-medium transition-all hover:scale-105',
                    isSelected
                      ? 'border-primary/30 bg-primary/10 text-primary hover:bg-primary/20'
                      : 'border-border bg-card hover:bg-accent text-muted-foreground'
                  )}
                >
                  {CATEGORY_LABELS[category]}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Active Filters Summary */}
      {(selectedSport || selectedCategory) && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Showing:</span>
          {selectedSport && (
            <Badge variant="outline" className="font-normal">
              {SPORT_CONFIG[selectedSport].label}
            </Badge>
          )}
          {selectedCategory && (
            <Badge variant="outline" className="font-normal">
              {CATEGORY_LABELS[selectedCategory]}
            </Badge>
          )}
          <button
            onClick={() => {
              onSportChange?.(null);
              onCategoryChange?.(null);
            }}
            className="ml-auto text-xs text-primary hover:underline"
          >
            Clear all filters
          </button>
        </div>
      )}
    </div>
  );
}

// Export sport icon helper for use in other components
export function getSportIcon(sport: Sport) {
  return SPORT_CONFIG[sport].icon;
}

export function getSportColor(sport: Sport) {
  const config = SPORT_CONFIG[sport];
  // Extract just the text color class
  const textColorMatch = config.color.match(/text-\w+-\d+/);
  return textColorMatch ? textColorMatch[0] : 'text-foreground';
}
