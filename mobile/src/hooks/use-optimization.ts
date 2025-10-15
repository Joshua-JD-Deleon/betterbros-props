/**
 * Custom hooks for parlay optimization and slip detection
 */
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { queryKeys } from '@/lib/api/query-client';
import { useUIStore } from '@/lib/store/ui-store';
import type { OptimizationResponse, SlipDetectionResponse, OptimizationConstraints } from '@/types';

export function useOptimizedParlays(
  propLegIds: string[],
  constraints?: OptimizationConstraints,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: queryKeys.optimization.parlays(propLegIds, constraints),
    queryFn: async () => {
      const response = await apiClient.optimizeParlays(propLegIds, constraints);
      return response as OptimizationResponse;
    },
    enabled: enabled && propLegIds.length >= 2,
    staleTime: 3 * 60 * 1000, // 3 minutes
  });
}

export function useSlipDetection() {
  const filters = useUIStore((state) => state.filters);

  return useQuery({
    queryKey: queryKeys.slips.list(filters),
    queryFn: async () => {
      const response = await apiClient.detectSlips({
        min_edge: filters.minEdge,
        min_confidence: filters.minConfidence,
        max_risk: filters.maxRisk,
        top_k: 20,
      });
      return response as SlipDetectionResponse;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

export function useTopSets(enabled: boolean = true) {
  const filters = useUIStore((state) => state.filters);

  return useQuery({
    queryKey: ['topSets', filters],
    queryFn: async () => {
      // First get top slips
      const slips = await apiClient.detectSlips({
        min_edge: filters.minEdge,
        min_confidence: filters.minConfidence,
        max_risk: filters.maxRisk,
        top_k: 30,
      }) as SlipDetectionResponse;

      // Get prop leg IDs from top slips
      const propLegIds = slips.slips.map(slip => slip.prop_leg_id);

      if (propLegIds.length < 2) {
        return { candidates: [], total_evaluated: 0, computation_time_ms: 0 };
      }

      // Optimize parlays from top slips
      const optimized = await apiClient.optimizeParlays(propLegIds, {
        min_legs: 2,
        max_legs: 5,
        min_edge: filters.minEdge,
        min_confidence: filters.minConfidence,
        max_correlation: 0.3,
        max_player_exposure: 1,
        max_team_exposure: 3,
        max_game_exposure: 2,
        require_diverse_stats: true,
        require_diverse_games: true,
      });

      return optimized as OptimizationResponse;
    },
    enabled,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
