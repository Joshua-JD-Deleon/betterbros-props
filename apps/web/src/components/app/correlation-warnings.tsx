'use client';

import { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  Users,
  TrendingUp,
  Calendar,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  X,
  AlertCircle,
  Info,
} from 'lucide-react';
import { useSlipStore } from '@/lib/store/slip-store';
import { useOptimizationStore } from '@/lib/store/optimization-store';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

/**
 * Enhanced correlation warning interface
 */
export interface CorrelationWarning {
  id: string;
  severity: 'low' | 'medium' | 'high';
  correlation: number;
  type: 'same_game' | 'same_player' | 'dependent_stats' | 'lineup';
  description: string;
  affectedProps: string[]; // IDs of affected props
  affectedPropsData?: {
    id: string;
    selection: string;
    market: string;
  }[];
  recommendation?: string;
  details?: string;
}

interface CorrelationWarningsProps {
  slipId?: string; // Optional: for specific slip, otherwise uses current manual slip
  compact?: boolean; // Compact display for sidebars
  showActions?: boolean; // Show remove/ignore buttons
  onWarningClick?: (warning: CorrelationWarning) => void;
  className?: string;
}

/**
 * Calculate correlation warnings from current slip entries
 */
function calculateCorrelationWarnings(
  entries: ReturnType<typeof useSlipStore.getState>['entries']
): CorrelationWarning[] {
  const warnings: CorrelationWarning[] = [];

  // Check for same game correlations
  const gameMap = new Map<string, typeof entries>();
  entries.forEach((entry) => {
    const gameKey = `${entry.gameInfo.teams.sort().join('-')}-${entry.gameInfo.startTime}`;
    if (!gameMap.has(gameKey)) {
      gameMap.set(gameKey, []);
    }
    gameMap.get(gameKey)!.push(entry);
  });

  gameMap.forEach((gameEntries, gameKey) => {
    if (gameEntries.length > 1) {
      // Calculate correlation based on number of props
      const correlation = Math.min(0.3 + (gameEntries.length - 2) * 0.15, 0.75);
      const severity: 'low' | 'medium' | 'high' =
        correlation > 0.5 ? 'high' : correlation > 0.3 ? 'medium' : 'low';

      warnings.push({
        id: `same-game-${gameKey}`,
        severity,
        correlation,
        type: 'same_game',
        description: `Same game: ${gameEntries[0].gameInfo.teams.join(' vs ')}`,
        affectedProps: gameEntries.map((e) => e.id),
        affectedPropsData: gameEntries.map((e) => ({
          id: e.id,
          selection: e.selection,
          market: e.market,
        })),
        recommendation:
          severity === 'high'
            ? 'Consider removing some props to reduce correlation risk'
            : 'Monitor correlation - props may be related',
        details: `Props from the same game have natural correlation. When one event happens, it can affect the probability of others occurring.`,
      });
    }
  });

  // Check for same player correlations
  const playerMap = new Map<string, typeof entries>();
  entries.forEach((entry) => {
    // Extract player name (assuming format "Player Name Over/Under X")
    const playerMatch = entry.selection.match(/^([\w\s'.-]+?)(?:\s+(?:Over|Under|OVER|UNDER))/i);
    if (playerMatch) {
      const player = playerMatch[1].trim();
      if (!playerMap.has(player)) {
        playerMap.set(player, []);
      }
      playerMap.get(player)!.push(entry);
    }
  });

  playerMap.forEach((playerEntries, player) => {
    if (playerEntries.length > 1) {
      // Same player, different markets = high correlation
      const correlation = 0.55 + (playerEntries.length - 2) * 0.1;
      const severity: 'low' | 'medium' | 'high' =
        correlation > 0.5 ? 'high' : correlation > 0.3 ? 'medium' : 'low';

      warnings.push({
        id: `same-player-${player}`,
        severity,
        correlation: Math.min(correlation, 0.85),
        type: 'same_player',
        description: `Same player: ${player}`,
        affectedProps: playerEntries.map((e) => e.id),
        affectedPropsData: playerEntries.map((e) => ({
          id: e.id,
          selection: e.selection,
          market: e.market,
        })),
        recommendation:
          'Multiple props for the same player are highly correlated',
        details: `Different stat categories for the same player (e.g., passing yards + touchdowns) are strongly correlated since they reflect the same game performance.`,
      });
    }
  });

  // Check for dependent stats (QB + receiver)
  const qbEntries = entries.filter((e) =>
    e.market.toLowerCase().includes('passing') ||
    e.selection.toLowerCase().includes('pass')
  );

  const receiverEntries = entries.filter((e) =>
    e.market.toLowerCase().includes('receiving') ||
    e.selection.toLowerCase().includes('rec')
  );

  // Check if they're from the same game
  qbEntries.forEach((qbEntry) => {
    receiverEntries.forEach((recEntry) => {
      const sameGame =
        qbEntry.gameInfo.teams.some((team) => recEntry.gameInfo.teams.includes(team)) &&
        qbEntry.gameInfo.startTime === recEntry.gameInfo.startTime;

      if (sameGame) {
        const correlation = 0.42;
        warnings.push({
          id: `dependent-${qbEntry.id}-${recEntry.id}`,
          severity: 'medium',
          correlation,
          type: 'dependent_stats',
          description: 'Dependent stats: QB and receiver from same game',
          affectedProps: [qbEntry.id, recEntry.id],
          affectedPropsData: [
            {
              id: qbEntry.id,
              selection: qbEntry.selection,
              market: qbEntry.market,
            },
            {
              id: recEntry.id,
              selection: recEntry.selection,
              market: recEntry.market,
            },
          ],
          recommendation: 'QB and receiver stats are positively correlated',
          details: `When a QB has high passing yards, receivers on their team are more likely to have high receiving yards. This creates positive correlation.`,
        });
      }
    });
  });

  return warnings;
}

/**
 * Get severity badge config
 */
function getSeverityConfig(severity: 'low' | 'medium' | 'high') {
  switch (severity) {
    case 'high':
      return {
        icon: AlertCircle,
        color: 'text-red-500',
        bg: 'bg-red-500/10',
        border: 'border-red-500/30',
        label: 'HIGH',
        badgeClass: 'bg-red-500/20 text-red-500 border-red-500/30',
      };
    case 'medium':
      return {
        icon: AlertTriangle,
        color: 'text-yellow-500',
        bg: 'bg-yellow-500/10',
        border: 'border-yellow-500/30',
        label: 'MEDIUM',
        badgeClass: 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
      };
    case 'low':
      return {
        icon: Info,
        color: 'text-blue-500',
        bg: 'bg-blue-500/10',
        border: 'border-blue-500/30',
        label: 'LOW',
        badgeClass: 'bg-blue-500/20 text-blue-500 border-blue-500/30',
      };
  }
}

/**
 * Get type icon
 */
function getTypeIcon(type: CorrelationWarning['type']) {
  switch (type) {
    case 'same_game':
      return Calendar;
    case 'same_player':
      return Users;
    case 'dependent_stats':
      return TrendingUp;
    case 'lineup':
      return Users;
  }
}

/**
 * Individual warning card
 */
function WarningCard({
  warning,
  showActions,
  onRemove,
  onIgnore,
  onClick,
  compact,
}: {
  warning: CorrelationWarning;
  showActions?: boolean;
  onRemove?: (propId: string) => void;
  onIgnore?: (warningId: string) => void;
  onClick?: (warning: CorrelationWarning) => void;
  compact?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  const severityConfig = getSeverityConfig(warning.severity);
  const TypeIcon = getTypeIcon(warning.type);
  const SeverityIcon = severityConfig.icon;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
    >
      <Card
        className={cn(
          'border transition-colors cursor-pointer hover:bg-accent/50',
          severityConfig.border,
          onClick && 'hover:shadow-md'
        )}
        onClick={() => onClick?.(warning)}
      >
        <CardContent className={cn('p-4', compact && 'p-3')}>
          {/* Header */}
          <div className="flex items-start gap-3">
            <div className={cn('rounded-full p-2', severityConfig.bg)}>
              <SeverityIcon className={cn('h-4 w-4', severityConfig.color)} />
            </div>

            <div className="flex-1 min-w-0">
              {/* Title row */}
              <div className="flex items-center gap-2 mb-1">
                <Badge
                  className={cn(
                    'text-xs font-bold',
                    severityConfig.badgeClass
                  )}
                >
                  {severityConfig.label}
                </Badge>
                <span className="text-sm font-semibold text-muted-foreground">
                  {(warning.correlation * 100).toFixed(0)}% correlation
                </span>
              </div>

              {/* Description */}
              <div className="flex items-center gap-2 mb-2">
                <TypeIcon className="h-3.5 w-3.5 text-muted-foreground" />
                <p className="text-sm font-medium">{warning.description}</p>
              </div>

              {/* Affected props */}
              {warning.affectedPropsData && !compact && (
                <div className="space-y-1 mt-2">
                  {warning.affectedPropsData.map((prop) => (
                    <div
                      key={prop.id}
                      className="flex items-center gap-2 text-xs text-muted-foreground pl-1"
                    >
                      <div className="h-1 w-1 rounded-full bg-muted-foreground" />
                      <span>{prop.selection}</span>
                      <span className="text-xs opacity-60">({prop.market})</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Recommendation */}
              {warning.recommendation && !compact && (
                <div className="mt-2 text-xs text-muted-foreground italic">
                  {warning.recommendation}
                </div>
              )}

              {/* Expandable details */}
              {warning.details && !compact && (
                <>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setExpanded(!expanded);
                    }}
                    className="mt-2 flex items-center gap-1 text-xs text-primary hover:underline"
                  >
                    {expanded ? (
                      <>
                        <ChevronUp className="h-3 w-3" />
                        Hide details
                      </>
                    ) : (
                      <>
                        <ChevronDown className="h-3 w-3" />
                        Show details
                      </>
                    )}
                  </button>

                  <AnimatePresence>
                    {expanded && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                      >
                        <div className="mt-2 rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
                          {warning.details}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </>
              )}

              {/* Actions */}
              {showActions && warning.affectedPropsData && (
                <div className="flex gap-2 mt-3">
                  {warning.affectedPropsData.map((prop) => (
                    <Button
                      key={prop.id}
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onRemove?.(prop.id);
                      }}
                      className="h-7 text-xs"
                    >
                      <X className="h-3 w-3 mr-1" />
                      Remove {prop.market.split(' ')[0]}
                    </Button>
                  ))}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      onIgnore?.(warning.id);
                    }}
                    className="h-7 text-xs"
                  >
                    Ignore
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

/**
 * Main Correlation Warnings Component
 */
export function CorrelationWarnings({
  slipId,
  compact = false,
  showActions = true,
  onWarningClick,
  className,
}: CorrelationWarningsProps) {
  const { entries, removeEntry } = useSlipStore();
  const { correlationWarnings: optimizationWarnings } = useOptimizationStore();
  const [ignoredWarnings, setIgnoredWarnings] = useState<Set<string>>(new Set());

  // Calculate warnings from slip entries
  const slipWarnings = useMemo(() => {
    if (entries.length < 2) return [];
    return calculateCorrelationWarnings(entries);
  }, [entries]);

  // Filter out ignored warnings
  const activeWarnings = useMemo(() => {
    return slipWarnings.filter((w) => !ignoredWarnings.has(w.id));
  }, [slipWarnings, ignoredWarnings]);

  // Calculate overall risk
  const overallRisk = useMemo(() => {
    if (activeWarnings.length === 0) return 'none';

    const highCount = activeWarnings.filter((w) => w.severity === 'high').length;
    const mediumCount = activeWarnings.filter((w) => w.severity === 'medium').length;

    if (highCount > 0) return 'high';
    if (mediumCount > 0) return 'medium';
    return 'low';
  }, [activeWarnings]);

  const highestCorrelation = useMemo(() => {
    if (activeWarnings.length === 0) return 0;
    return Math.max(...activeWarnings.map((w) => w.correlation));
  }, [activeWarnings]);

  // Handle ignore warning
  const handleIgnore = (warningId: string) => {
    setIgnoredWarnings((prev) => new Set([...prev, warningId]));
  };

  // Handle remove prop
  const handleRemove = (propId: string) => {
    removeEntry(propId);
  };

  // Empty state (no correlations)
  if (activeWarnings.length === 0) {
    return (
      <Card className={cn('border-green-500/30', className)}>
        <CardContent className={cn('p-6', compact && 'p-4')}>
          <div className="flex flex-col items-center justify-center text-center py-4">
            <div className="rounded-full bg-green-500/10 p-3">
              <CheckCircle2 className="h-8 w-8 text-green-500" />
            </div>
            <h3 className="mt-3 text-base font-semibold">No Correlation Issues</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Your slip has good diversity!
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Group warnings by severity
  const warningsBySeverity = {
    high: activeWarnings.filter((w) => w.severity === 'high'),
    medium: activeWarnings.filter((w) => w.severity === 'medium'),
    low: activeWarnings.filter((w) => w.severity === 'low'),
  };

  return (
    <Card className={className}>
      <CardHeader className={cn('pb-3', compact && 'p-4 pb-2')}>
        <div className="flex items-center justify-between">
          <CardTitle className={cn('text-lg', compact && 'text-base')}>
            Correlation Warnings
          </CardTitle>
          <Badge variant="outline" className="font-mono">
            {activeWarnings.length}
          </Badge>
        </div>
        <CardDescription className={cn(compact && 'text-xs')}>
          {overallRisk === 'high' && (
            <span className="text-red-500 font-medium">
              High correlation risk detected
            </span>
          )}
          {overallRisk === 'medium' && (
            <span className="text-yellow-500 font-medium">
              Moderate correlation risk
            </span>
          )}
          {overallRisk === 'low' && (
            <span className="text-blue-500 font-medium">
              Low correlation risk
            </span>
          )}
        </CardDescription>
      </CardHeader>

      <CardContent className={cn('space-y-3', compact && 'p-4 pt-0')}>
        {/* Summary stats */}
        {!compact && (
          <div className="grid grid-cols-3 gap-3 pb-3 border-b">
            <div className="text-center">
              <div className="text-xs text-muted-foreground">Highest</div>
              <div className="text-lg font-bold">
                {(highestCorrelation * 100).toFixed(0)}%
              </div>
            </div>
            <div className="text-center">
              <div className="text-xs text-muted-foreground">Risk Level</div>
              <div className="text-lg font-bold capitalize">{overallRisk}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-muted-foreground">Warnings</div>
              <div className="text-lg font-bold">{activeWarnings.length}</div>
            </div>
          </div>
        )}

        {/* Warnings list */}
        <div className="space-y-2">
          <AnimatePresence>
            {/* High severity first */}
            {warningsBySeverity.high.map((warning) => (
              <WarningCard
                key={warning.id}
                warning={warning}
                showActions={showActions}
                onRemove={handleRemove}
                onIgnore={handleIgnore}
                onClick={onWarningClick}
                compact={compact}
              />
            ))}

            {/* Medium severity */}
            {warningsBySeverity.medium.map((warning) => (
              <WarningCard
                key={warning.id}
                warning={warning}
                showActions={showActions}
                onRemove={handleRemove}
                onIgnore={handleIgnore}
                onClick={onWarningClick}
                compact={compact}
              />
            ))}

            {/* Low severity */}
            {warningsBySeverity.low.map((warning) => (
              <WarningCard
                key={warning.id}
                warning={warning}
                showActions={showActions}
                onRemove={handleRemove}
                onIgnore={handleIgnore}
                onClick={onWarningClick}
                compact={compact}
              />
            ))}
          </AnimatePresence>
        </div>

        {/* Overall recommendation */}
        {!compact && overallRisk === 'high' && (
          <div className="mt-4 rounded-md bg-red-500/10 border border-red-500/30 p-3">
            <div className="flex gap-2">
              <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-red-500">
                <strong>Recommendation:</strong> Consider removing one or more
                correlated props to reduce risk. Highly correlated props reduce
                your effective odds and increase variance.
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
