'use client';

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDown,
  ChevronUp,
  Plus,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  Filter,
  RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useOptimizationStore } from '@/lib/store/optimization-store';
import { useUIStore } from '@/lib/store/ui-store';
import type { OptimizedSlip } from '@/lib/types/props';
import { formatOdds, formatEV, formatCurrency, formatProbability, cn } from '@/lib/utils';

interface TopSetsDisplayProps {
  onRetry?: () => void;
}

type SortOption = 'ev' | 'probability' | 'legs';

export function TopSetsDisplay({ onRetry }: TopSetsDisplayProps) {
  const { topSets, loadingState, addToManualSlip } = useOptimizationStore();
  const { openDrawer } = useUIStore();

  // Local state
  const [expandedSlips, setExpandedSlips] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<SortOption>('ev');
  const [minLegs, setMinLegs] = useState<number>(0);
  const [maxLegs, setMaxLegs] = useState<number>(10);
  const [minEV, setMinEV] = useState<number>(-100);
  const [showFilters, setShowFilters] = useState(false);
  const [addingSlips, setAddingSlips] = useState<Set<string>>(new Set());

  // Toggle expand/collapse
  const toggleExpand = (slipId: string) => {
    setExpandedSlips((prev) => {
      const next = new Set(prev);
      if (next.has(slipId)) {
        next.delete(slipId);
      } else {
        next.add(slipId);
      }
      return next;
    });
  };

  // Filter and sort slips
  const filteredAndSortedSlips = useMemo(() => {
    let filtered = topSets.filter((slip) => {
      if (slip.num_legs < minLegs || slip.num_legs > maxLegs) return false;
      if (slip.expected_value < minEV) return false;
      return true;
    });

    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'ev':
          return b.expected_value - a.expected_value;
        case 'probability':
          return b.correlation_adjusted_prob - a.correlation_adjusted_prob;
        case 'legs':
          return a.num_legs - b.num_legs;
        default:
          return 0;
      }
    });

    return filtered;
  }, [topSets, sortBy, minLegs, maxLegs, minEV]);

  // Handle add to slip
  const handleAddToSlip = async (slipId: string) => {
    setAddingSlips((prev) => new Set(prev).add(slipId));

    try {
      addToManualSlip(slipId);

      // Show success feedback with a delay
      await new Promise((resolve) => setTimeout(resolve, 300));

      // Open drawer to show added slip
      openDrawer();
    } finally {
      setAddingSlips((prev) => {
        const next = new Set(prev);
        next.delete(slipId);
        return next;
      });
    }
  };

  // Get unique games count
  const getUniqueGames = (slip: OptimizedSlip): number => {
    const gameIds = new Set(slip.legs.map((leg) => leg.game_id));
    return gameIds.size;
  };

  // Get correlation color
  const getCorrelationColor = (notes: string[]): 'default' | 'secondary' | 'destructive' => {
    const hasWarning = notes.some((note) => note.toLowerCase().includes('warning'));
    const hasSameGame = notes.some((note) => note.toLowerCase().includes('same game'));

    if (hasWarning) return 'destructive';
    if (hasSameGame) return 'secondary';
    return 'default';
  };

  // Get max correlation value
  const getMaxCorrelation = (slip: OptimizedSlip): number => {
    // Parse correlation from notes if available
    const corrNote = slip.correlation_notes.find((note) =>
      note.toLowerCase().includes('correlation')
    );
    if (corrNote) {
      const match = corrNote.match(/(\d+\.\d+)/);
      if (match) return parseFloat(match[1]);
    }
    return 0;
  };

  // Render loading state
  if (loadingState.isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="space-y-2 flex-1">
                  <div className="h-6 bg-muted rounded w-32" />
                  <div className="h-4 bg-muted rounded w-24" />
                </div>
                <div className="h-10 bg-muted rounded w-28" />
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                {[...Array(4)].map((_, j) => (
                  <div key={j} className="space-y-1">
                    <div className="h-3 bg-muted rounded w-20" />
                    <div className="h-5 bg-muted rounded w-16" />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  // Render error state
  if (loadingState.error) {
    return (
      <Card className="border-destructive/50">
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
          <h3 className="text-lg font-semibold mb-2">Failed to Load Optimized Slips</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-md">
            {loadingState.error}
          </p>
          {onRetry && (
            <Button onClick={onRetry} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  // Render empty state
  if (topSets.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <Sparkles className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Optimized Slips Yet</h3>
          <p className="text-sm text-muted-foreground max-w-md">
            Click "Generate Optimized Slips" to see AI-powered parlay recommendations based on your
            selected props and risk profile.
          </p>
        </CardContent>
      </Card>
    );
  }

  // Render empty filtered state
  if (filteredAndSortedSlips.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <Filter className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Slips Match Filters</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-md">
            Try adjusting your filter settings to see more results.
          </p>
          <Button
            onClick={() => {
              setMinLegs(0);
              setMaxLegs(10);
              setMinEV(-100);
            }}
            variant="outline"
          >
            Reset Filters
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Top Optimized Slips</h2>
          <p className="text-sm text-muted-foreground">
            {filteredAndSortedSlips.length} of {topSets.length} slips shown
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Sort dropdown */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="h-10 px-3 rounded-md border bg-background text-sm"
          >
            <option value="ev">Sort by EV</option>
            <option value="probability">Sort by Win Probability</option>
            <option value="legs">Sort by Legs</option>
          </select>

          {/* Filter toggle */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
          </Button>
        </div>
      </div>

      {/* Filter panel */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <Card>
              <CardContent className="pt-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Min Legs</label>
                    <input
                      type="number"
                      value={minLegs}
                      onChange={(e) => setMinLegs(parseInt(e.target.value) || 0)}
                      className="w-full h-10 px-3 rounded-md border bg-background"
                      min="0"
                      max="10"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Max Legs</label>
                    <input
                      type="number"
                      value={maxLegs}
                      onChange={(e) => setMaxLegs(parseInt(e.target.value) || 10)}
                      className="w-full h-10 px-3 rounded-md border bg-background"
                      min="0"
                      max="10"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Min EV (%)</label>
                    <input
                      type="number"
                      value={minEV}
                      onChange={(e) => setMinEV(parseFloat(e.target.value) || -100)}
                      className="w-full h-10 px-3 rounded-md border bg-background"
                      step="0.5"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Slips grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <AnimatePresence mode="popLayout">
          {filteredAndSortedSlips.map((slip, index) => {
            const isExpanded = expandedSlips.has(slip.slip_id);
            const isAdding = addingSlips.has(slip.slip_id);
            const uniqueGames = getUniqueGames(slip);
            const maxCorr = getMaxCorrelation(slip);
            const corrColor = getCorrelationColor(slip.correlation_notes);
            const evFormatted = formatEV(slip.expected_value);

            return (
              <motion.div
                key={slip.slip_id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
                layout
              >
                <Card
                  className={cn(
                    'group relative overflow-hidden transition-all',
                    'hover:shadow-lg hover:border-primary/50',
                    index === 0 && 'border-2 border-profit/50 shadow-ev-positive'
                  )}
                >
                  {/* Top rank badge */}
                  {index < 3 && (
                    <div className="absolute right-0 top-0">
                      <Badge
                        variant={index === 0 ? 'profit' : 'secondary'}
                        className="rounded-tl-none rounded-br-none font-bold"
                      >
                        #{index + 1}
                      </Badge>
                    </div>
                  )}

                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          {index >= 3 && (
                            <span className="text-sm font-semibold text-muted-foreground">
                              #{index + 1}
                            </span>
                          )}
                          <h3 className="font-semibold text-lg">
                            {slip.num_legs}-Leg Parlay
                          </h3>
                          <Badge variant="outline" className="text-xs">
                            {slip.risk_level}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatOdds(slip.total_odds)} • {uniqueGames}{' '}
                          {uniqueGames === 1 ? 'game' : 'games'}
                        </p>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className="space-y-4">
                    {/* Key metrics grid */}
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Expected Value</p>
                        <p className={cn('text-2xl font-bold', evFormatted.className)}>
                          {evFormatted.text}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Win Probability</p>
                        <p className="text-2xl font-bold">
                          {formatProbability(slip.correlation_adjusted_prob)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Recommended Stake</p>
                        <p className="text-lg font-semibold">
                          {formatCurrency(slip.suggested_bet)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Diversity Score</p>
                        <div className="flex items-center gap-2">
                          <p className="text-lg font-semibold">
                            {Math.round(slip.diversity_score * 100)}
                          </p>
                          <Badge
                            variant={slip.diversity_score > 0.7 ? 'profit' : 'secondary'}
                            className="text-xs"
                          >
                            {slip.diversity_score > 0.7 ? 'High' : 'Medium'}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    {/* Probability bar */}
                    <div>
                      <div className="h-2 bg-muted rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${slip.correlation_adjusted_prob * 100}%` }}
                          transition={{ duration: 0.6, delay: index * 0.05 }}
                          className="h-full bg-gradient-to-r from-profit/60 to-profit rounded-full"
                        />
                      </div>
                    </div>

                    {/* Correlation info */}
                    {slip.correlation_notes.length > 0 && (
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <p className="text-xs font-medium">Max Correlation:</p>
                          <Badge variant={corrColor} className="text-xs">
                            {maxCorr > 0 ? maxCorr.toFixed(2) : 'Low'}
                          </Badge>
                        </div>
                        {slip.correlation_notes.slice(0, 2).map((note, i) => (
                          <div key={i} className="flex items-start gap-2">
                            <AlertTriangle className="h-3 w-3 text-yellow-500 mt-0.5 flex-shrink-0" />
                            <p className="text-xs text-muted-foreground">{note}</p>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Expand/collapse button */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleExpand(slip.slip_id)}
                      className="w-full"
                    >
                      {isExpanded ? (
                        <>
                          <ChevronUp className="h-4 w-4 mr-2" />
                          Hide Legs
                        </>
                      ) : (
                        <>
                          <ChevronDown className="h-4 w-4 mr-2" />
                          View {slip.num_legs} legs from {uniqueGames}{' '}
                          {uniqueGames === 1 ? 'game' : 'games'}
                        </>
                      )}
                    </Button>

                    {/* Expanded legs */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="space-y-3 border-t pt-3"
                        >
                          {slip.legs.map((leg, legIndex) => (
                            <motion.div
                              key={`${slip.slip_id}-leg-${legIndex}`}
                              initial={{ x: -10, opacity: 0 }}
                              animate={{ x: 0, opacity: 1 }}
                              transition={{ delay: legIndex * 0.05 }}
                              className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                            >
                              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center">
                                <span className="text-xs font-bold">{legIndex + 1}</span>
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-start justify-between gap-2">
                                  <div>
                                    <p className="font-semibold">
                                      {leg.player_name}
                                      <span className="text-xs text-muted-foreground ml-2">
                                        ({leg.position})
                                      </span>
                                    </p>
                                    <p className="text-sm text-muted-foreground">
                                      {leg.prop_type} {leg.direction} {leg.line}
                                    </p>
                                    <p className="text-xs text-muted-foreground mt-1">
                                      {leg.team} • {formatOdds(leg.odds)}
                                    </p>
                                  </div>
                                  <Badge variant="outline" className="text-xs flex-shrink-0">
                                    {formatProbability(leg.prob)}
                                  </Badge>
                                </div>
                              </div>
                            </motion.div>
                          ))}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </CardContent>

                  <CardFooter className="pt-0">
                    <Button
                      onClick={() => handleAddToSlip(slip.slip_id)}
                      disabled={isAdding}
                      className="w-full relative overflow-hidden"
                      variant={index === 0 ? 'profit' : 'default'}
                    >
                      <AnimatePresence mode="wait">
                        {isAdding ? (
                          <motion.div
                            key="adding"
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            className="flex items-center"
                          >
                            <CheckCircle2 className="h-4 w-4 mr-2" />
                            Added!
                          </motion.div>
                        ) : (
                          <motion.div
                            key="add"
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                            className="flex items-center"
                          >
                            <Plus className="h-4 w-4 mr-2" />
                            Add to Slip
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </Button>
                  </CardFooter>
                </Card>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
