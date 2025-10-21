'use client';

import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Trash2,
  TrendingUp,
  AlertTriangle,
  Sparkles,
  Save,
  Share,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  Calculator,
  BarChart3,
  Target,
  Percent,
  DollarSign,
  Layers,
} from 'lucide-react';
import { useState, useMemo } from 'react';
import { useUIStore } from '@/lib/store/ui-store';
import { useSlipStore } from '@/lib/store/slip-store';
import { useOptimizationStore } from '@/lib/store/optimization-store';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Slider } from '@/components/ui/slider';
import { CorrelationWarnings } from './correlation-warnings';
import { RiskProfileSelector } from './risk-profile-selector';
import { formatOdds, formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';

type SlipMode = 'single' | 'parlay' | 'round-robin';

/**
 * Calculate Kelly stake based on probability, odds, bankroll, and Kelly fraction
 */
function calculateKellyStake(
  probability: number,
  americanOdds: number,
  bankroll: number,
  kellyFraction: number = 0.25
): number {
  const decimalOdds = americanOdds > 0
    ? (americanOdds / 100) + 1
    : (100 / Math.abs(americanOdds)) + 1;

  const kellyPercent = (probability * decimalOdds - 1) / (decimalOdds - 1);
  return Math.max(0, kellyPercent * bankroll * kellyFraction);
}

/**
 * Calculate correlation-adjusted parlay probability
 */
function calculateAdjustedParlayProb(
  entries: ReturnType<typeof useSlipStore.getState>['entries']
): number {
  // Simple multiplication for base probability
  const baseProb = entries.reduce((prob, entry) => prob * entry.probability, 1);

  // Check for same-game correlations and apply adjustment
  const gameMap = new Map<string, number>();
  entries.forEach((entry) => {
    const gameKey = `${entry.gameInfo.teams.sort().join('-')}-${entry.gameInfo.startTime}`;
    gameMap.set(gameKey, (gameMap.get(gameKey) || 0) + 1);
  });

  // Find max correlation (more props from same game = higher correlation)
  let maxCorrelation = 0;
  gameMap.forEach((count) => {
    if (count > 1) {
      const correlation = Math.min(0.3 + (count - 2) * 0.15, 0.75);
      maxCorrelation = Math.max(maxCorrelation, correlation);
    }
  });

  // Adjust probability downward based on correlation
  const adjustedProb = baseProb * (1 - maxCorrelation * 0.4);
  return adjustedProb;
}

/**
 * Get EV quality level and color
 */
function getEVQuality(evPercent: number) {
  if (evPercent >= 10) return { label: 'Excellent', color: 'text-emerald-500', bg: 'bg-emerald-500' };
  if (evPercent >= 5) return { label: 'Great', color: 'text-green-500', bg: 'bg-green-500' };
  if (evPercent >= 2) return { label: 'Good', color: 'text-blue-500', bg: 'bg-blue-500' };
  if (evPercent >= 0) return { label: 'Positive', color: 'text-yellow-500', bg: 'bg-yellow-500' };
  return { label: 'Negative', color: 'text-red-500', bg: 'bg-red-500' };
}

export function SlipDrawer() {
  const { isDrawerOpen, closeDrawer } = useUIStore();
  const {
    entries,
    removeEntry,
    updateStake,
    clearSlip,
    getStats,
    mode,
    setMode,
    bankroll,
    kellyFraction,
    setKellyFraction,
  } = useSlipStore();

  const { riskProfile, getRiskProfileConfig } = useOptimizationStore();

  const [showCorrelations, setShowCorrelations] = useState(true);
  const [showRiskProfile, setShowRiskProfile] = useState(false);
  const [customKellyFraction, setCustomKellyFraction] = useState(kellyFraction);

  const stats = getStats();
  const riskConfig = getRiskProfileConfig();

  // Calculate Kelly recommendations for each entry
  const kellyRecommendations = useMemo(() => {
    return entries.map(entry => ({
      id: entry.id,
      recommended: calculateKellyStake(
        entry.probability,
        entry.odds,
        bankroll,
        customKellyFraction
      )
    }));
  }, [entries, bankroll, customKellyFraction]);

  // Calculate parlay metrics
  const parlayMetrics = useMemo(() => {
    if (mode !== 'parlay' || entries.length === 0) return null;

    const rawProb = entries.reduce((prob, entry) => prob * entry.probability, 1);
    const adjustedProb = calculateAdjustedParlayProb(entries);
    const parlayOdds = entries.reduce((product, entry) => {
      const decimalOdds = entry.odds > 0 ? (entry.odds / 100) + 1 : (100 / Math.abs(entry.odds)) + 1;
      return product * decimalOdds;
    }, 1);

    // Convert parlay decimal odds to American
    const parlayAmericanOdds = parlayOdds >= 2
      ? Math.round((parlayOdds - 1) * 100)
      : Math.round(-100 / (parlayOdds - 1));

    return {
      rawProb,
      adjustedProb,
      parlayOdds,
      parlayAmericanOdds,
      correlationImpact: ((rawProb - adjustedProb) / rawProb) * 100,
    };
  }, [mode, entries]);

  // Apply Kelly stakes to all entries
  const handleUseKellyStakes = () => {
    kellyRecommendations.forEach(({ id, recommended }) => {
      updateStake(id, Math.round(recommended));
    });
  };

  // Calculate total EV percentage
  const totalEVPercent = useMemo(() => {
    if (stats.totalStake === 0) return 0;
    return (stats.totalExpectedValue / stats.totalStake) * 100;
  }, [stats]);

  const evQuality = getEVQuality(totalEVPercent);

  return (
    <AnimatePresence>
      {isDrawerOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeDrawer}
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm"
          />

          {/* Drawer */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed right-0 top-0 z-50 h-full w-full max-w-[480px] border-l bg-card shadow-2xl"
          >
            <div className="flex h-full flex-col">
              {/* Header */}
              <div className="flex items-center justify-between border-b p-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-semibold">Bet Slip</h2>
                  {entries.length > 0 && (
                    <Badge variant="default" className="h-6 px-2">
                      {entries.length}
                    </Badge>
                  )}
                </div>
                <Button variant="ghost" size="icon" onClick={closeDrawer}>
                  <X className="h-5 w-5" />
                </Button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto custom-scrollbar">
                {entries.length === 0 ? (
                  // Empty State
                  <div className="flex h-full flex-col items-center justify-center p-6 text-center">
                    <div className="rounded-full bg-muted p-6">
                      <TrendingUp className="h-12 w-12 text-muted-foreground" />
                    </div>
                    <h3 className="mt-6 text-xl font-semibold">Empty Slip</h3>
                    <p className="mt-2 text-sm text-muted-foreground max-w-xs">
                      Add props from the dashboard to build your optimized betting slip
                    </p>

                    <div className="mt-8 w-full max-w-xs space-y-3">
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={closeDrawer}
                      >
                        Browse Props
                      </Button>
                      <Button
                        variant="default"
                        className="w-full gap-2"
                      >
                        <Sparkles className="h-4 w-4" />
                        Generate Optimized Slips
                      </Button>
                    </div>

                    <div className="mt-8 rounded-lg bg-muted/50 p-4 text-left">
                      <p className="text-xs font-medium text-muted-foreground mb-2">
                        Quick Tips:
                      </p>
                      <ul className="space-y-1 text-xs text-muted-foreground">
                        <li className="flex gap-2">
                          <span className="text-primary">•</span>
                          Add props with positive EV for better returns
                        </li>
                        <li className="flex gap-2">
                          <span className="text-primary">•</span>
                          Watch for correlation warnings
                        </li>
                        <li className="flex gap-2">
                          <span className="text-primary">•</span>
                          Use Kelly sizing for optimal stakes
                        </li>
                      </ul>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 space-y-4">
                    {/* Mode Selector */}
                    <div className="flex gap-2">
                      <Button
                        variant={mode === 'single' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setMode('single')}
                        className="flex-1"
                      >
                        <Layers className="h-3.5 w-3.5 mr-1.5" />
                        Single
                      </Button>
                      <Button
                        variant={mode === 'parlay' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setMode('parlay')}
                        className="flex-1"
                      >
                        <Target className="h-3.5 w-3.5 mr-1.5" />
                        Parlay
                      </Button>
                      <Button
                        variant={mode === 'round-robin' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setMode('round-robin')}
                        className="flex-1"
                        disabled
                      >
                        Round Robin
                      </Button>
                    </div>

                    {/* Risk Profile Quick Selector */}
                    <Card className="p-3 bg-muted/30">
                      <button
                        onClick={() => setShowRiskProfile(!showRiskProfile)}
                        className="flex items-center justify-between w-full text-sm"
                      >
                        <div className="flex items-center gap-2">
                          <BarChart3 className="h-4 w-4 text-muted-foreground" />
                          <span className="font-medium">
                            Risk Profile: <span className="text-primary capitalize">{riskProfile}</span>
                          </span>
                        </div>
                        {showRiskProfile ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </button>

                      <AnimatePresence>
                        {showRiskProfile && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                          >
                            <div className="mt-3 pt-3 border-t">
                              <RiskProfileSelector compact />
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </Card>

                    {/* Correlation Warnings */}
                    {entries.length >= 2 && (
                      <div>
                        <button
                          onClick={() => setShowCorrelations(!showCorrelations)}
                          className="flex items-center justify-between w-full mb-2"
                        >
                          <div className="flex items-center gap-2 text-sm font-medium">
                            <AlertTriangle className="h-4 w-4 text-yellow-500" />
                            Correlation Analysis
                          </div>
                          {showCorrelations ? (
                            <ChevronUp className="h-4 w-4" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </button>

                        <AnimatePresence>
                          {showCorrelations && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              className="overflow-hidden"
                            >
                              <CorrelationWarnings compact showActions />
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    )}

                    <Separator />

                    {/* Entries Header */}
                    <div className="flex items-center justify-between">
                      <h3 className="text-sm font-semibold text-muted-foreground">
                        ENTRIES ({entries.length})
                      </h3>
                      {kellyRecommendations.length > 0 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleUseKellyStakes}
                          className="h-7 text-xs gap-1.5"
                        >
                          <Calculator className="h-3 w-3" />
                          Use Kelly Stakes
                        </Button>
                      )}
                    </div>

                    {/* Entry Cards */}
                    <div className="space-y-3">
                      <AnimatePresence mode="popLayout">
                        {entries.map((entry, index) => {
                          const kellyRec = kellyRecommendations.find(k => k.id === entry.id);
                          const showKellyHint = kellyRec && Math.abs(entry.stake - kellyRec.recommended) > 5;

                          return (
                            <motion.div
                              key={entry.id}
                              layout
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, x: -100 }}
                              transition={{ duration: 0.2 }}
                            >
                              <Card className="p-3 relative overflow-hidden">
                                {/* Entry Number Badge */}
                                <div className="absolute top-2 right-2">
                                  <Badge variant="outline" className="h-5 w-5 p-0 flex items-center justify-center text-xs">
                                    {index + 1}
                                  </Badge>
                                </div>

                                <div className="pr-8">
                                  {/* Player & Prop */}
                                  <div className="font-medium text-sm mb-1">
                                    {entry.selection}
                                  </div>
                                  <div className="text-xs text-muted-foreground mb-2">
                                    {entry.market} • {entry.sportsbook}
                                  </div>

                                  {/* Metrics Row */}
                                  <div className="flex items-center gap-3 mb-3">
                                    <div className="flex items-center gap-1">
                                      <DollarSign className="h-3 w-3 text-muted-foreground" />
                                      <span className="odds-american text-sm font-semibold">
                                        {formatOdds(entry.odds)}
                                      </span>
                                    </div>
                                    <Separator orientation="vertical" className="h-4" />
                                    <div className="flex items-center gap-1">
                                      <Percent className="h-3 w-3 text-muted-foreground" />
                                      <span
                                        className={cn(
                                          'text-xs font-semibold',
                                          entry.expectedValue > 0
                                            ? 'text-profit'
                                            : 'text-loss'
                                        )}
                                      >
                                        {entry.expectedValue > 0 ? '+' : ''}
                                        {entry.expectedValue.toFixed(1)}% EV
                                      </span>
                                    </div>
                                    <Separator orientation="vertical" className="h-4" />
                                    <div className="flex items-center gap-1">
                                      <Target className="h-3 w-3 text-muted-foreground" />
                                      <span className="text-xs text-muted-foreground">
                                        {(entry.probability * 100).toFixed(0)}% prob
                                      </span>
                                    </div>
                                  </div>

                                  {/* Stake Input */}
                                  <div className="space-y-1.5">
                                    <div className="flex items-center justify-between">
                                      <label className="text-xs font-medium text-muted-foreground">
                                        Stake
                                      </label>
                                      {showKellyHint && kellyRec && (
                                        <button
                                          onClick={() => updateStake(entry.id, Math.round(kellyRec.recommended))}
                                          className="flex items-center gap-1 text-xs text-primary hover:underline"
                                        >
                                          <Lightbulb className="h-3 w-3" />
                                          Kelly: ${Math.round(kellyRec.recommended)}
                                        </button>
                                      )}
                                    </div>
                                    <input
                                      type="number"
                                      min="0"
                                      step="1"
                                      value={entry.stake || ''}
                                      onChange={(e) =>
                                        updateStake(entry.id, Number(e.target.value))
                                      }
                                      className="w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                                      placeholder="Enter stake..."
                                    />
                                  </div>
                                </div>

                                {/* Remove Button */}
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => removeEntry(entry.id)}
                                  className="absolute bottom-2 right-2 h-7 w-7 text-muted-foreground hover:text-destructive"
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </Button>
                              </Card>
                            </motion.div>
                          );
                        })}
                      </AnimatePresence>
                    </div>

                    {/* Parlay Metrics */}
                    {mode === 'parlay' && parlayMetrics && (
                      <>
                        <Separator />
                        <Card className="p-4 bg-primary/5 border-primary/20">
                          <div className="flex items-center gap-2 mb-3">
                            <Target className="h-4 w-4 text-primary" />
                            <h4 className="text-sm font-semibold">Parlay Analysis</h4>
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <div className="text-xs text-muted-foreground">Combined Odds</div>
                              <div className="text-lg font-bold text-primary">
                                {formatOdds(parlayMetrics.parlayAmericanOdds)}
                              </div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground">Win Probability</div>
                              <div className="text-lg font-bold">
                                {(parlayMetrics.adjustedProb * 100).toFixed(1)}%
                              </div>
                            </div>
                            {parlayMetrics.correlationImpact > 1 && (
                              <div className="col-span-2">
                                <div className="text-xs text-muted-foreground">Correlation Impact</div>
                                <div className="text-sm text-yellow-600 font-medium">
                                  -{parlayMetrics.correlationImpact.toFixed(1)}% probability reduction
                                </div>
                              </div>
                            )}
                          </div>
                        </Card>
                      </>
                    )}

                    {/* Kelly Fraction Adjuster */}
                    <Card className="p-4 bg-muted/30">
                      <div className="flex items-center justify-between mb-3">
                        <label className="text-sm font-medium">Kelly Fraction</label>
                        <span className="text-sm font-mono text-primary">
                          {customKellyFraction.toFixed(2)}
                        </span>
                      </div>
                      <Slider
                        value={[customKellyFraction]}
                        onValueChange={(values) => {
                          setCustomKellyFraction(values[0]);
                          setKellyFraction(values[0]);
                        }}
                        min={0.1}
                        max={1}
                        step={0.05}
                        className="mb-2"
                      />
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Conservative (0.25)</span>
                        <span>Aggressive (1.0)</span>
                      </div>
                    </Card>
                  </div>
                )}
              </div>

              {/* Footer - Summary & Actions */}
              {entries.length > 0 && (
                <div className="border-t bg-background/95 backdrop-blur">
                  {/* Summary Stats */}
                  <div className="p-4 space-y-3">
                    <Card className="p-4 bg-muted/50">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Legs</div>
                          <div className="text-lg font-bold">{entries.length}</div>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Total Stake</div>
                          <div className="text-lg font-bold">
                            {formatCurrency(stats.totalStake)}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Potential Payout</div>
                          <div className="text-lg font-bold text-primary">
                            {formatCurrency(stats.totalPotentialPayout)}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-muted-foreground mb-1">Win Probability</div>
                          <div className="text-lg font-bold">
                            {mode === 'parlay' && parlayMetrics
                              ? `${(parlayMetrics.adjustedProb * 100).toFixed(0)}%`
                              : `${((stats.totalStake > 0 ? entries.reduce((sum, e) => sum + e.probability * e.stake, 0) / stats.totalStake : 0) * 100).toFixed(0)}%`
                            }
                          </div>
                        </div>
                      </div>
                    </Card>

                    {/* EV Display with Progress Bar */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-muted-foreground">
                          Expected Value
                        </span>
                        <div className="text-right">
                          <div className={cn('text-lg font-bold', evQuality.color)}>
                            {formatCurrency(stats.totalExpectedValue)}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {totalEVPercent > 0 ? '+' : ''}{totalEVPercent.toFixed(1)}%
                          </div>
                        </div>
                      </div>

                      {/* EV Progress Bar */}
                      <div className="relative h-2 bg-muted rounded-full overflow-hidden">
                        <motion.div
                          className={cn('h-full', evQuality.bg)}
                          initial={{ width: 0 }}
                          animate={{
                            width: `${Math.min(Math.abs(totalEVPercent) * 5, 100)}%`
                          }}
                          transition={{ duration: 0.5 }}
                        />
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className={cn('text-xs font-medium', evQuality.color)}>
                          {evQuality.label}
                        </span>
                        {totalEVPercent >= 5 && (
                          <Badge variant="default" className="h-5 text-xs bg-profit">
                            Strong Edge
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Action Buttons */}
                  <div className="p-4 space-y-2">
                    <div className="grid grid-cols-2 gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-2"
                      >
                        <Sparkles className="h-4 w-4" />
                        Optimize
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="gap-2"
                      >
                        <Save className="h-4 w-4" />
                        Save
                      </Button>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        className="flex-1"
                        onClick={clearSlip}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Clear
                      </Button>
                      <Button
                        className="flex-1 bg-profit hover:bg-profit/90"
                        size="default"
                      >
                        Place Bets
                        <TrendingUp className="h-4 w-4 ml-2" />
                      </Button>
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      className="w-full gap-2"
                    >
                      <Share className="h-4 w-4" />
                      Export Slip
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
