/**
 * Insights Screen - Calibration metrics and trends
 */
import React from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Text,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useCalibrationMetrics } from '@/hooks/use-insights';
import { useNetworkStatus } from '@/hooks/use-network-status';
import { CalibrationCard } from '@/components/CalibrationCard';
import { OfflineBanner } from '@/components/OfflineBanner';
import { colors, spacing, typography } from '@/lib/theme/tokens';

export default function InsightsScreen() {
  const { isOffline } = useNetworkStatus();
  const { data, isLoading, isError, error, refetch, isFetching } = useCalibrationMetrics();

  if (isLoading) {
    return (
      <View style={styles.container}>
        {isOffline && <OfflineBanner />}
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Loading insights...</Text>
        </View>
      </View>
    );
  }

  if (isError) {
    return (
      <View style={styles.container}>
        {isOffline && <OfflineBanner />}
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Failed to load insights</Text>
          <Text style={styles.errorText}>
            {error?.message || 'An error occurred'}
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {isOffline && <OfflineBanner />}

      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isFetching}
            onRefresh={() => refetch()}
            tintColor={colors.primary}
            colors={[colors.primary]}
          />
        }
      >
        <View style={styles.header}>
          <Text style={styles.title}>Model Insights</Text>
          <Text style={styles.subtitle}>
            Calibration metrics and performance analytics
          </Text>
        </View>

        {data && <CalibrationCard metrics={data} />}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Key Metrics</Text>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Brier Score</Text>
            <Text style={styles.metricValue}>
              {data?.brier_score.toFixed(4) || 'N/A'}
            </Text>
            <Text style={styles.metricDescription}>
              Lower is better. Measures accuracy of probabilistic predictions.
            </Text>
          </View>

          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Log Loss</Text>
            <Text style={styles.metricValue}>
              {data?.log_loss.toFixed(4) || 'N/A'}
            </Text>
            <Text style={styles.metricDescription}>
              Lower is better. Penalizes confident wrong predictions.
            </Text>
          </View>
        </View>

        {data?.confidence_buckets && data.confidence_buckets.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Confidence Buckets</Text>
            {data.confidence_buckets.map((bucket, index) => (
              <View key={index} style={styles.bucketCard}>
                <View style={styles.bucketHeader}>
                  <Text style={styles.bucketLabel}>{bucket.bucket}</Text>
                  <Text style={styles.bucketCount}>{bucket.count} bets</Text>
                </View>
                <View style={styles.bucketRow}>
                  <View style={styles.bucketStat}>
                    <Text style={styles.bucketStatLabel}>Actual</Text>
                    <Text style={styles.bucketStatValue}>
                      {(bucket.win_rate * 100).toFixed(1)}%
                    </Text>
                  </View>
                  <View style={styles.bucketStat}>
                    <Text style={styles.bucketStatLabel}>Expected</Text>
                    <Text style={styles.bucketStatValue}>
                      {(bucket.expected_rate * 100).toFixed(1)}%
                    </Text>
                  </View>
                  <View style={styles.bucketStat}>
                    <Text style={styles.bucketStatLabel}>Delta</Text>
                    <Text
                      style={[
                        styles.bucketStatValue,
                        {
                          color:
                            bucket.win_rate > bucket.expected_rate
                              ? colors.profit
                              : colors.loss,
                        },
                      ]}
                    >
                      {((bucket.win_rate - bucket.expected_rate) * 100).toFixed(1)}%
                    </Text>
                  </View>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    paddingBottom: spacing.xl,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    ...typography.body,
    color: colors.mutedForeground,
    marginTop: spacing.md,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  errorTitle: {
    ...typography.h3,
    color: colors.foreground,
    marginBottom: spacing.sm,
  },
  errorText: {
    ...typography.body,
    color: colors.destructive,
    textAlign: 'center',
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
  },
  section: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.lg,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.foreground,
    marginBottom: spacing.md,
  },
  metricCard: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
  metricLabel: {
    ...typography.bodySmall,
    color: colors.mutedForeground,
    marginBottom: spacing.xs,
  },
  metricValue: {
    ...typography.h2,
    color: colors.primary,
    marginBottom: spacing.xs,
  },
  metricDescription: {
    ...typography.caption,
    color: colors.mutedForeground,
  },
  bucketCard: {
    backgroundColor: colors.card,
    borderRadius: 12,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  bucketHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  bucketLabel: {
    ...typography.body,
    fontWeight: '600',
    color: colors.foreground,
  },
  bucketCount: {
    ...typography.caption,
    color: colors.mutedForeground,
  },
  bucketRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  bucketStat: {
    alignItems: 'center',
  },
  bucketStatLabel: {
    ...typography.caption,
    color: colors.mutedForeground,
    marginBottom: spacing.xs,
  },
  bucketStatValue: {
    ...typography.body,
    fontWeight: '600',
    color: colors.foreground,
  },
});
