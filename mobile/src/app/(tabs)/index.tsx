/**
 * Props Feed Screen - Main screen with virtualized list of props
 */
import React, { useCallback, useState } from 'react';
import {
  View,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
} from 'react-native';
import { useProps, useRefreshProps } from '@/hooks/use-props';
import { useNetworkStatus } from '@/hooks/use-network-status';
import { useUIStore } from '@/lib/store/ui-store';
import { PropCard } from '@/components/PropCard';
import { OfflineBanner } from '@/components/OfflineBanner';
import { FilterButton } from '@/components/FilterButton';
import { colors, spacing, typography } from '@/lib/theme/tokens';
import type { PropMarket } from '@/types';
import { formatDistanceToNow } from 'date-fns';

export default function PropsScreen() {
  const { isOffline } = useNetworkStatus();
  const filters = useUIStore((state) => state.filters);
  const lastSyncTime = useUIStore((state) => state.lastSyncTime);

  const { data, isLoading, isError, error } = useProps({
    sport: filters.sport,
  });

  const refreshMutation = useRefreshProps();

  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await refreshMutation.mutateAsync({ sport: filters.sport });
    } catch (err) {
      console.error('Refresh failed:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, [filters.sport, refreshMutation]);

  const renderItem = useCallback(
    ({ item }: { item: PropMarket }) => <PropCard market={item} />,
    []
  );

  const keyExtractor = useCallback((item: PropMarket) => item.id, []);

  const getItemLayout = useCallback(
    (_: any, index: number) => ({
      length: 160, // Approximate item height
      offset: 160 * index,
      index,
    }),
    []
  );

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <Text style={styles.emptyText}>
        {isLoading ? 'Loading props...' : 'No props available'}
      </Text>
      {isError && (
        <Text style={styles.errorText}>
          {error?.message || 'Failed to load props'}
        </Text>
      )}
    </View>
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <View style={styles.headerRow}>
        <Text style={styles.headerTitle}>
          {data?.total || 0} Props Available
        </Text>
        <FilterButton />
      </View>
      {lastSyncTime && (
        <Text style={styles.lastSync}>
          Last updated {formatDistanceToNow(lastSyncTime, { addSuffix: true })}
        </Text>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      {isOffline && <OfflineBanner />}

      <FlatList
        data={data?.markets || []}
        renderItem={renderItem}
        keyExtractor={keyExtractor}
        getItemLayout={getItemLayout}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={renderEmpty}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor={colors.primary}
            colors={[colors.primary]}
          />
        }
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        removeClippedSubviews={true}
        maxToRenderPerBatch={10}
        windowSize={10}
        initialNumToRender={10}
        updateCellsBatchingPeriod={50}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  listContent: {
    paddingBottom: spacing.xl,
  },
  header: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    paddingBottom: spacing.sm,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  headerTitle: {
    ...typography.h3,
    color: colors.foreground,
  },
  lastSync: {
    ...typography.caption,
    color: colors.mutedForeground,
  },
  emptyContainer: {
    padding: spacing.xl,
    alignItems: 'center',
  },
  emptyText: {
    ...typography.body,
    color: colors.mutedForeground,
    textAlign: 'center',
  },
  errorText: {
    ...typography.bodySmall,
    color: colors.destructive,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
});
