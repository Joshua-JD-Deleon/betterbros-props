/**
 * Top Sets Screen - Optimized parlay recommendations
 */
import React from 'react';
import {
  View,
  FlatList,
  StyleSheet,
  Text,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useTopSets } from '@/hooks/use-optimization';
import { useNetworkStatus } from '@/hooks/use-network-status';
import { OptimizedSlipCard } from '@/components/OptimizedSlipCard';
import { OfflineBanner } from '@/components/OfflineBanner';
import { colors, spacing, typography } from '@/lib/theme/tokens';
import type { ParlayCandidate } from '@/types';

export default function TopSetsScreen() {
  const { isOffline } = useNetworkStatus();
  const { data, isLoading, isError, error, refetch, isFetching } = useTopSets();

  const renderItem = ({ item }: { item: ParlayCandidate }) => (
    <OptimizedSlipCard parlay={item} />
  );

  const keyExtractor = (item: ParlayCandidate, index: number) =>
    `${item.rank}-${index}`;

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      {isLoading ? (
        <>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>
            Analyzing props and optimizing sets...
          </Text>
        </>
      ) : (
        <>
          <Text style={styles.emptyText}>
            No optimized sets available
          </Text>
          {isError && (
            <Text style={styles.errorText}>
              {error?.message || 'Failed to load optimized sets'}
            </Text>
          )}
          <Text style={styles.hintText}>
            Try adjusting your filters to see more options
          </Text>
        </>
      )}
    </View>
  );

  const renderHeader = () => (
    <View style={styles.header}>
      <Text style={styles.title}>Top Optimized Sets</Text>
      <Text style={styles.subtitle}>
        AI-powered parlays with optimal EV and low correlation
      </Text>
      {data && data.candidates.length > 0 && (
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{data.candidates.length}</Text>
            <Text style={styles.statLabel}>Sets</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{data.total_evaluated}</Text>
            <Text style={styles.statLabel}>Evaluated</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>
              {Math.round(data.computation_time_ms)}ms
            </Text>
            <Text style={styles.statLabel}>Computed</Text>
          </View>
        </View>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      {isOffline && <OfflineBanner />}

      <FlatList
        data={data?.candidates || []}
        renderItem={renderItem}
        keyExtractor={keyExtractor}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={renderEmpty}
        refreshControl={
          <RefreshControl
            refreshing={isFetching}
            onRefresh={() => refetch()}
            tintColor={colors.primary}
            colors={[colors.primary]}
          />
        }
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
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
    paddingBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  title: {
    ...typography.h2,
    color: colors.foreground,
    marginBottom: spacing.xs,
  },
  subtitle: {
    ...typography.bodySmall,
    color: colors.mutedForeground,
    marginBottom: spacing.md,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: spacing.md,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    ...typography.h3,
    color: colors.primary,
  },
  statLabel: {
    ...typography.caption,
    color: colors.mutedForeground,
    marginTop: spacing.xs,
  },
  emptyContainer: {
    padding: spacing.xl,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 400,
  },
  loadingText: {
    ...typography.body,
    color: colors.mutedForeground,
    marginTop: spacing.md,
    textAlign: 'center',
  },
  emptyText: {
    ...typography.body,
    color: colors.foreground,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  errorText: {
    ...typography.bodySmall,
    color: colors.destructive,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
  hintText: {
    ...typography.caption,
    color: colors.mutedForeground,
    textAlign: 'center',
    marginTop: spacing.md,
  },
});
