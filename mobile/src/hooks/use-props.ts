/**
 * Custom hooks for fetching props data
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { queryKeys } from '@/lib/api/query-client';
import { useUIStore } from '@/lib/store/ui-store';
import type { PropMarketsResponse, Sport, Platform } from '@/types';

interface UsePropsOptions {
  sport?: Sport;
  platform?: Platform;
  enabled?: boolean;
}

export function useProps(options: UsePropsOptions = {}) {
  const { sport, platform, enabled = true } = options;

  return useQuery({
    queryKey: queryKeys.props.list({ sport, platform }),
    queryFn: async () => {
      const response = await apiClient.getProps({
        sport,
        platform,
        page: 1,
        page_size: 100,
      });
      return response as PropMarketsResponse;
    },
    enabled,
    staleTime: 2 * 60 * 1000, // 2 minutes - props change frequently
  });
}

export function usePropById(id?: string) {
  return useQuery({
    queryKey: queryKeys.props.detail(id!),
    queryFn: async () => {
      const response = await apiClient.getPropById(id!);
      return response;
    },
    enabled: !!id,
  });
}

export function useRefreshProps() {
  const queryClient = useQueryClient();
  const setLastSync = useUIStore((state) => state.setLastSync);

  return useMutation({
    mutationFn: async (options: UsePropsOptions = {}) => {
      const { sport, platform } = options;
      const response = await apiClient.getProps({
        sport,
        platform,
        page: 1,
        page_size: 100,
      });
      return response as PropMarketsResponse;
    },
    onSuccess: (data, variables) => {
      // Update cache
      queryClient.setQueryData(
        queryKeys.props.list(variables),
        data
      );

      // Invalidate all props queries to trigger refetch
      queryClient.invalidateQueries({
        queryKey: queryKeys.props.all,
      });

      // Update sync time
      setLastSync(Date.now());
    },
  });
}

export function usePredictions(propLegIds: string[], enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.predictions.forLegs(propLegIds),
    queryFn: async () => {
      const response = await apiClient.getPredictions(propLegIds);
      return response;
    },
    enabled: enabled && propLegIds.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCorrelations(propLegIds: string[], enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.correlations.forLegs(propLegIds),
    queryFn: async () => {
      const response = await apiClient.getCorrelations(propLegIds);
      return response;
    },
    enabled: enabled && propLegIds.length >= 2,
    staleTime: 10 * 60 * 1000, // 10 minutes - correlations are more stable
  });
}
