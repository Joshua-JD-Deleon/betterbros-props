'use client';

import { useState, useEffect } from 'react';
import {
  Download,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Database,
  TrendingUp,
  Zap,
  Clock,
  Coins
} from 'lucide-react';
import { usePropsStore } from '@/lib/store/props-store';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { Sport } from '@/lib/types/stats';
import type { FetchPropsRequest } from '@/lib/types/props';

interface FormState {
  sport: Sport;
  week: string;
  season: string;
}

interface ValidationErrors {
  week?: string;
  season?: string;
}

const SPORTS: Sport[] = ['NFL', 'NBA', 'MLB', 'NHL'];

const SPORT_METADATA: Record<Sport, { maxWeek: number; seasonFormat: string; example: string }> = {
  NFL: { maxWeek: 18, seasonFormat: 'YYYY', example: '2024' },
  NBA: { maxWeek: 82, seasonFormat: 'YYYY-YY', example: '2023-24' },
  MLB: { maxWeek: 162, seasonFormat: 'YYYY', example: '2024' },
  NHL: { maxWeek: 82, seasonFormat: 'YYYY-YY', example: '2023-24' },
};

export function APIConnectionPanel() {
  const {
    fetchProps,
    loadingState,
    apiCredits,
    useMockData,
    toggleMockData,
    props,
    cache
  } = usePropsStore();

  const [formState, setFormState] = useState<FormState>({
    sport: 'NFL',
    week: '1',
    season: '2024',
  });

  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [showSuccess, setShowSuccess] = useState(false);
  const [lastFetchTime, setLastFetchTime] = useState<Date | null>(null);

  // Get cache status
  const cacheKey = JSON.stringify({ sport: formState.sport });
  const cachedData = cache.get(cacheKey);
  const isCached = cachedData && new Date(cachedData.metadata.expires_at).getTime() > Date.now();

  // Calculate time since last fetch
  const getTimeSinceLastFetch = () => {
    if (!lastFetchTime) return null;

    const now = Date.now();
    const diff = now - lastFetchTime.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    return 'Just now';
  };

  // Validate form
  const validateForm = (): boolean => {
    const errors: ValidationErrors = {};
    const weekNum = parseInt(formState.week);
    const sportMetadata = SPORT_METADATA[formState.sport];

    // Validate week
    if (!formState.week || isNaN(weekNum)) {
      errors.week = 'Week number is required';
    } else if (weekNum < 1) {
      errors.week = 'Week number must be positive';
    } else if (weekNum > sportMetadata.maxWeek) {
      errors.week = `${formState.sport} has a maximum of ${sportMetadata.maxWeek} weeks`;
    }

    // Validate season
    if (!formState.season) {
      errors.season = 'Season is required';
    } else if (formState.sport === 'NFL' || formState.sport === 'MLB') {
      // Format: YYYY
      if (!/^\d{4}$/.test(formState.season)) {
        errors.season = `Format: ${sportMetadata.seasonFormat} (e.g., ${sportMetadata.example})`;
      }
    } else {
      // Format: YYYY-YY for NBA/NHL
      if (!/^\d{4}-\d{2}$/.test(formState.season)) {
        errors.season = `Format: ${sportMetadata.seasonFormat} (e.g., ${sportMetadata.example})`;
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handle form submission
  const handleFetchProps = async () => {
    // Clear previous success state
    setShowSuccess(false);

    // Validate form
    if (!validateForm()) {
      return;
    }

    const request: FetchPropsRequest = {
      filters: {
        sport: formState.sport,
        week: parseInt(formState.week),
        season: parseInt(formState.season.split('-')[0]),
      },
      use_mock: useMockData,
      refresh_cache: false,
    };

    try {
      await fetchProps(request);

      // Show success feedback
      setShowSuccess(true);
      setLastFetchTime(new Date());

      // Hide success message after 3 seconds
      setTimeout(() => setShowSuccess(false), 3000);
    } catch (error) {
      // Error is handled by the store
      console.error('Failed to fetch props:', error);
    }
  };

  // Update season format when sport changes
  useEffect(() => {
    const metadata = SPORT_METADATA[formState.sport];
    if (formState.sport === 'NBA' || formState.sport === 'NHL') {
      if (!/^\d{4}-\d{2}$/.test(formState.season)) {
        setFormState(prev => ({ ...prev, season: '2023-24' }));
      }
    } else {
      if (!/^\d{4}$/.test(formState.season)) {
        setFormState(prev => ({ ...prev, season: '2024' }));
      }
    }
    // Clear errors when sport changes
    setValidationErrors({});
  }, [formState.sport]);

  // Calculate credit warnings
  const creditWarning = apiCredits && apiCredits.remaining < apiCredits.cost_per_fetch * 5;
  const creditsNeeded = apiCredits?.cost_per_fetch || 10;

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5 text-primary" />
              API Connection
            </CardTitle>
            <CardDescription>
              Fetch props data from the API
            </CardDescription>
          </div>

          {/* Data Source Toggle */}
          <button
            onClick={toggleMockData}
            className={cn(
              'flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-all hover:scale-105',
              useMockData
                ? 'border-secondary/30 bg-secondary/10 text-secondary hover:bg-secondary/20'
                : 'border-live/30 bg-live/10 text-live hover:bg-live/20'
            )}
          >
            <Zap className="h-3.5 w-3.5" />
            {useMockData ? 'Mock Data' : 'Live API'}
          </button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Form Controls */}
        <div className="space-y-4">
          {/* Sport Selector */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Sport</label>
            <div className="flex flex-wrap gap-2">
              {SPORTS.map((sport) => (
                <Badge
                  key={sport}
                  variant={formState.sport === sport ? 'default' : 'outline'}
                  className="cursor-pointer px-4 py-2 text-sm transition-all hover:scale-105"
                  onClick={() => setFormState(prev => ({ ...prev, sport }))}
                >
                  {sport}
                </Badge>
              ))}
            </div>
          </div>

          {/* Week and Season Inputs */}
          <div className="grid grid-cols-2 gap-4">
            {/* Week Input */}
            <div className="space-y-2">
              <label htmlFor="week" className="text-sm font-medium">
                Week Number
              </label>
              <input
                id="week"
                type="number"
                min="1"
                max={SPORT_METADATA[formState.sport].maxWeek}
                value={formState.week}
                onChange={(e) => {
                  setFormState(prev => ({ ...prev, week: e.target.value }));
                  setValidationErrors(prev => ({ ...prev, week: undefined }));
                }}
                className={cn(
                  'w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background transition-colors',
                  'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                  'disabled:cursor-not-allowed disabled:opacity-50',
                  validationErrors.week && 'border-destructive'
                )}
                placeholder="1"
                disabled={loadingState.isLoading}
              />
              {validationErrors.week && (
                <p className="text-xs text-destructive">{validationErrors.week}</p>
              )}
              <p className="text-xs text-muted-foreground">
                1-{SPORT_METADATA[formState.sport].maxWeek}
              </p>
            </div>

            {/* Season Input */}
            <div className="space-y-2">
              <label htmlFor="season" className="text-sm font-medium">
                Season
              </label>
              <input
                id="season"
                type="text"
                value={formState.season}
                onChange={(e) => {
                  setFormState(prev => ({ ...prev, season: e.target.value }));
                  setValidationErrors(prev => ({ ...prev, season: undefined }));
                }}
                className={cn(
                  'w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background transition-colors',
                  'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
                  'disabled:cursor-not-allowed disabled:opacity-50',
                  validationErrors.season && 'border-destructive'
                )}
                placeholder={SPORT_METADATA[formState.sport].example}
                disabled={loadingState.isLoading}
              />
              {validationErrors.season && (
                <p className="text-xs text-destructive">{validationErrors.season}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Format: {SPORT_METADATA[formState.sport].example}
              </p>
            </div>
          </div>
        </div>

        {/* API Credits Display */}
        {apiCredits && (
          <div className={cn(
            'rounded-lg border p-4 space-y-2 transition-colors',
            creditWarning ? 'border-destructive/30 bg-destructive/5' : 'border-border bg-muted/50'
          )}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Coins className={cn(
                  "h-4 w-4",
                  creditWarning ? "text-destructive" : "text-muted-foreground"
                )} />
                <span className="text-sm font-medium">API Credits</span>
              </div>
              <span className={cn(
                "text-lg font-bold",
                creditWarning ? "text-destructive" : "text-primary"
              )}>
                {apiCredits.remaining.toLocaleString()}
              </span>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>This fetch will use:</span>
                <span className="font-medium text-foreground">{creditsNeeded} credits</span>
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Resets:</span>
                <span className="font-medium text-foreground">
                  {new Date(apiCredits.reset_date).toLocaleDateString()}
                </span>
              </div>
            </div>

            {creditWarning && (
              <div className="flex items-start gap-2 pt-2 border-t border-destructive/20">
                <AlertCircle className="h-4 w-4 text-destructive mt-0.5" />
                <p className="text-xs text-destructive">
                  Low credits remaining. Consider using mock data or wait for reset.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Fetch Button */}
        <Button
          onClick={handleFetchProps}
          disabled={loadingState.isLoading}
          className="w-full"
          size="lg"
        >
          {loadingState.isLoading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              {loadingState.message || 'Fetching...'}
            </>
          ) : (
            <>
              <Download className="h-4 w-4" />
              Fetch Props
            </>
          )}
        </Button>

        {/* Status Messages */}
        <div className="space-y-2">
          {/* Success Message */}
          {showSuccess && !loadingState.error && (
            <div className="flex items-center gap-2 rounded-md border border-profit/30 bg-profit/10 px-3 py-2 text-sm text-profit">
              <CheckCircle2 className="h-4 w-4" />
              <span className="font-medium">
                Successfully fetched {props.length} props
              </span>
            </div>
          )}

          {/* Error Message */}
          {loadingState.error && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium">Failed to fetch props</p>
                <p className="text-xs mt-1 opacity-90">{loadingState.error}</p>
              </div>
            </div>
          )}

          {/* Cache Status */}
          {isCached && !loadingState.isLoading && (
            <div className="flex items-center gap-2 rounded-md border border-secondary/30 bg-secondary/10 px-3 py-2 text-xs text-secondary">
              <TrendingUp className="h-3.5 w-3.5" />
              <span>
                Using cached data - expires {new Date(cachedData.metadata.expires_at).toLocaleTimeString()}
              </span>
            </div>
          )}

          {/* Last Fetch Time */}
          {lastFetchTime && !loadingState.isLoading && (
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <div className="flex items-center gap-2">
                <Clock className="h-3.5 w-3.5" />
                <span>Last fetched: {getTimeSinceLastFetch()}</span>
              </div>
              {props.length > 0 && (
                <span className="font-medium text-foreground">
                  {props.length} props loaded
                </span>
              )}
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="rounded-lg border border-primary/20 bg-primary/5 p-3 text-xs text-muted-foreground">
          <p className="font-medium text-foreground mb-1">How it works:</p>
          <ul className="space-y-1 list-disc list-inside">
            <li>Select sport, week, and season</li>
            <li>Data is cached for 5 minutes to save credits</li>
            <li>Toggle between mock data and live API</li>
            <li>View fetched props in the table below</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
