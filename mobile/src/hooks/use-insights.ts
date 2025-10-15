/**
 * Custom hooks for insights (calibration, trends, etc.)
 */
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { queryKeys } from '@/lib/api/query-client';
import type { CalibrationMetrics } from '@/types';

export function useCalibrationMetrics() {
  return useQuery({
    queryKey: queryKeys.insights.calibration,
    queryFn: async () => {
      const response = await apiClient.getCalibrationMetrics();
      return response as CalibrationMetrics;
    },
    staleTime: 30 * 60 * 1000, // 30 minutes - calibration changes slowly
  });
}

export function useHistoricalTrends(
  playerId?: string,
  statType?: string,
  enabled: boolean = true
) {
  return useQuery({
    queryKey: queryKeys.insights.trends(playerId!, statType!),
    queryFn: async () => {
      const response = await apiClient.getHistoricalTrends(playerId!, statType!);
      return response;
    },
    enabled: enabled && !!playerId && !!statType,
    staleTime: 60 * 60 * 1000, // 1 hour - historical data doesn't change often
  });
}
