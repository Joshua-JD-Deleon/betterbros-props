'use client';

import { useState } from 'react';
import { Shield, Target, TrendingUp, ChevronDown, HelpCircle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { useOptimizationStore } from '@/lib/store/optimization-store';
import { RISK_PROFILES } from '@/lib/types/props';

type RiskMode = 'conservative' | 'balanced' | 'aggressive';

interface RiskOption {
  mode: RiskMode;
  label: string;
  icon: typeof Shield;
  color: string;
  bgColor: string;
  hoverColor: string;
  borderColor: string;
  description: string;
}

const riskOptions: RiskOption[] = [
  {
    mode: 'conservative',
    label: 'Conservative',
    icon: Shield,
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50',
    hoverColor: 'hover:bg-emerald-100',
    borderColor: 'border-emerald-300',
    description: 'Lower risk, higher win probability',
  },
  {
    mode: 'balanced',
    label: 'Balanced',
    icon: Target,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    hoverColor: 'hover:bg-blue-100',
    borderColor: 'border-blue-300',
    description: 'Optimal risk-reward balance',
  },
  {
    mode: 'aggressive',
    label: 'Aggressive',
    icon: TrendingUp,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    hoverColor: 'hover:bg-orange-100',
    borderColor: 'border-orange-300',
    description: 'Higher risk, higher potential payouts',
  },
];

interface RiskProfileSelectorProps {
  className?: string;
  showDetails?: boolean;
  compact?: boolean;
}

export function RiskProfileSelector({
  className,
  showDetails = true,
  compact = false,
}: RiskProfileSelectorProps) {
  const { riskProfile, setRiskProfile, loadingState } = useOptimizationStore();
  const [isExpanded, setIsExpanded] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  const currentProfile = RISK_PROFILES[riskProfile];
  const currentOption = riskOptions.find((opt) => opt.mode === riskProfile);

  const handleProfileChange = (mode: RiskMode) => {
    setRiskProfile(mode);
    // Success feedback could be added here if needed
  };

  // Format percentage for display
  const formatPercent = (value: number): string => {
    return `${(value * 100).toFixed(0)}%`;
  };

  // Format edge as percentage (convert from multiplier)
  const formatEdge = (value: number): string => {
    return `${((value - 1) * 100).toFixed(0)}%`;
  };

  // Format Kelly fraction
  const formatKelly = (value: number): string => {
    if (value === 0.25) return '1/4 Kelly';
    if (value === 0.5) return '1/2 Kelly';
    if (value === 0.75) return '3/4 Kelly';
    return `${value} Kelly`;
  };

  if (compact) {
    return (
      <div className={cn('flex gap-2', className)}>
        {riskOptions.map((option) => {
          const Icon = option.icon;
          const isSelected = option.mode === riskProfile;

          return (
            <button
              key={option.mode}
              onClick={() => handleProfileChange(option.mode)}
              className={cn(
                'relative flex items-center gap-2 rounded-lg border-2 px-3 py-2 text-sm font-medium transition-all',
                'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                'hover:scale-105',
                isSelected
                  ? `${option.bgColor} ${option.borderColor} ${option.color} shadow-md`
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
              )}
              disabled={loadingState.isLoading}
              aria-pressed={isSelected}
              aria-label={`${option.label} risk profile`}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{option.label}</span>
              {isSelected && (
                <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                  Active
                </Badge>
              )}
            </button>
          );
        })}
        {loadingState.isLoading && (
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        )}
      </div>
    );
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">Risk Profile</CardTitle>
            <CardDescription>Choose your betting strategy</CardDescription>
          </div>
          <button
            onClick={() => setShowHelp(!showHelp)}
            className="rounded-full p-1 hover:bg-muted transition-colors"
            aria-label="Toggle help information"
          >
            <HelpCircle className="h-5 w-5 text-muted-foreground" />
          </button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Help Section */}
        {showHelp && (
          <div className="rounded-lg bg-muted/50 p-4 text-sm space-y-2">
            <p className="font-medium">What&apos;s a risk profile?</p>
            <p className="text-muted-foreground">
              Your risk profile determines how the optimizer builds parlays. Conservative focuses on
              safer bets with higher win probability, while Aggressive pursues larger payouts with
              more legs and higher variance.
            </p>
          </div>
        )}

        {/* Risk Profile Options */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {riskOptions.map((option) => {
            const Icon = option.icon;
            const isSelected = option.mode === riskProfile;

            return (
              <button
                key={option.mode}
                onClick={() => handleProfileChange(option.mode)}
                className={cn(
                  'relative flex flex-col items-center gap-3 rounded-lg border-2 p-4 transition-all',
                  'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                  'hover:scale-105 hover:shadow-md',
                  isSelected
                    ? `${option.bgColor} ${option.borderColor} ${option.color} shadow-md`
                    : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                )}
                disabled={loadingState.isLoading}
                aria-pressed={isSelected}
                aria-label={`${option.label} risk profile: ${option.description}`}
              >
                {/* Icon */}
                <Icon className="h-8 w-8" />

                {/* Label */}
                <div className="text-center">
                  <div className="font-semibold">{option.label}</div>
                  <div className="text-xs mt-1 opacity-80">{option.description}</div>
                </div>

                {/* Active Badge */}
                {isSelected && (
                  <Badge
                    variant="secondary"
                    className="absolute top-2 right-2 h-5 px-2 text-xs"
                  >
                    Active
                  </Badge>
                )}
              </button>
            );
          })}
        </div>

        {/* Loading State */}
        {loadingState.isLoading && (
          <div className="flex items-center justify-center gap-2 py-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Updating profile...</span>
          </div>
        )}

        {/* Details Panel */}
        {showDetails && currentProfile && (
          <div className="space-y-3">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex w-full items-center justify-between rounded-lg bg-muted/50 px-4 py-3 text-sm font-medium hover:bg-muted transition-colors"
              aria-expanded={isExpanded}
              aria-controls="profile-details"
            >
              <span className="flex items-center gap-2">
                {currentOption && <currentOption.icon className="h-4 w-4" />}
                {currentOption?.label} Settings
              </span>
              <ChevronDown
                className={cn(
                  'h-4 w-4 transition-transform',
                  isExpanded && 'rotate-180'
                )}
              />
            </button>

            {isExpanded && (
              <div
                id="profile-details"
                className="space-y-3 rounded-lg border bg-card p-4"
              >
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Parlay Size */}
                  <div className="space-y-1">
                    <div className="text-xs font-medium text-muted-foreground">
                      Parlay Size
                    </div>
                    <div className="text-sm font-semibold">
                      Up to {currentProfile.max_legs} legs
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Maximum props per parlay
                    </div>
                  </div>

                  {/* Minimum Edge */}
                  <div className="space-y-1">
                    <div className="text-xs font-medium text-muted-foreground">
                      Minimum Edge
                    </div>
                    <div className="text-sm font-semibold">
                      {formatEdge(currentProfile.min_edge)}+
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Expected value threshold
                    </div>
                  </div>

                  {/* Minimum Confidence */}
                  <div className="space-y-1">
                    <div className="text-xs font-medium text-muted-foreground">
                      Minimum Confidence
                    </div>
                    <div className="text-sm font-semibold">
                      {formatPercent(currentProfile.min_prob)}+
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Win probability threshold
                    </div>
                  </div>

                  {/* Kelly Fraction */}
                  <div className="space-y-1">
                    <div className="text-xs font-medium text-muted-foreground">
                      Stake Sizing
                    </div>
                    <div className="text-sm font-semibold">
                      {formatKelly(currentProfile.kelly_fraction)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Kelly criterion multiplier
                    </div>
                  </div>

                  {/* Correlation Penalty */}
                  <div className="space-y-1">
                    <div className="text-xs font-medium text-muted-foreground">
                      Correlation Penalty
                    </div>
                    <div className="text-sm font-semibold">
                      {currentProfile.corr_penalty.toFixed(1)}x
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Same-game correlation weight
                    </div>
                  </div>
                </div>

                {/* What This Means */}
                <div className="mt-4 rounded-md bg-muted/50 p-3 text-xs space-y-2">
                  <div className="font-medium">What this means:</div>
                  <ul className="space-y-1 text-muted-foreground list-disc list-inside">
                    {riskProfile === 'conservative' && (
                      <>
                        <li>Smaller parlays with fewer legs for safer bets</li>
                        <li>Higher confidence requirements reduce variance</li>
                        <li>Conservative stake sizing protects bankroll</li>
                        <li>Strong correlation penalties avoid risky combinations</li>
                      </>
                    )}
                    {riskProfile === 'balanced' && (
                      <>
                        <li>Medium-sized parlays balance risk and reward</li>
                        <li>Moderate confidence thresholds for quality bets</li>
                        <li>Half-Kelly sizing for sustainable growth</li>
                        <li>Balanced correlation management</li>
                      </>
                    )}
                    {riskProfile === 'aggressive' && (
                      <>
                        <li>Larger parlays with more legs for bigger payouts</li>
                        <li>Lower thresholds allow more betting opportunities</li>
                        <li>Aggressive stake sizing maximizes EV</li>
                        <li>Relaxed correlation rules for flexibility</li>
                      </>
                    )}
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
