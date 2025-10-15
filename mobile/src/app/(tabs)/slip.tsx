/**
 * Slip Screen - User's selected props and parlay builder
 */
import React from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
} from 'react-native';
import { useSlipStore } from '@/lib/store/slip-store';
import { usePredictions, useCorrelations } from '@/hooks/use-props';
import { SlipItemCard } from '@/components/SlipItemCard';
import { colors, spacing, typography, borderRadius } from '@/lib/theme/tokens';

export default function SlipScreen() {
  const { items, clearSlip, legIds, getTotalMultiplier } = useSlipStore();

  const { data: predictions } = usePredictions(legIds());
  const { data: correlations } = useCorrelations(legIds(), legIds().length >= 2);

  const totalMultiplier = getTotalMultiplier();
  const winProbability = items.length > 0
    ? items.reduce((acc, item) => {
        const prediction = predictions?.predictions?.find(
          (p: any) => p.prop_leg_id === item.leg.id
        );
        return acc * (prediction?.prob_over || 0.65);
      }, 1)
    : 0;

  const expectedValue = items.length > 0
    ? items.reduce((acc, item) => {
        const prediction = predictions?.predictions?.find(
          (p: any) => p.prop_leg_id === item.leg.id
        );
        return acc + (prediction?.edge || 0);
      }, 0)
    : 0;

  const renderEmpty = () => (
    <View style={styles.emptyContainer}>
      <Text style={styles.emptyIcon}>🎫</Text>
      <Text style={styles.emptyTitle}>Your slip is empty</Text>
      <Text style={styles.emptyText}>
        Add props from the Props tab to build your parlay
      </Text>
    </View>
  );

  if (items.length === 0) {
    return (
      <View style={styles.container}>
        {renderEmpty()}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <View style={styles.headerRow}>
            <Text style={styles.title}>
              {items.length} {items.length === 1 ? 'Leg' : 'Legs'}
            </Text>
            <TouchableOpacity onPress={clearSlip} style={styles.clearButton}>
              <Text style={styles.clearButtonText}>Clear All</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.itemsList}>
          {items.map((item) => {
            const prediction = predictions?.predictions?.find(
              (p: any) => p.prop_leg_id === item.leg.id
            );
            return (
              <SlipItemCard
                key={item.leg.id}
                item={item}
                prediction={prediction}
              />
            );
          })}
        </View>

        {items.length >= 2 && (
          <View style={styles.analysisSection}>
            <Text style={styles.sectionTitle}>Parlay Analysis</Text>

            <View style={styles.statsGrid}>
              <View style={styles.statCard}>
                <Text style={styles.statLabel}>Multiplier</Text>
                <Text style={styles.statValue}>{totalMultiplier}x</Text>
              </View>

              <View style={styles.statCard}>
                <Text style={styles.statLabel}>Win Probability</Text>
                <Text style={styles.statValue}>
                  {(winProbability * 100).toFixed(1)}%
                </Text>
              </View>

              <View style={styles.statCard}>
                <Text style={styles.statLabel}>Total Edge</Text>
                <Text
                  style={[
                    styles.statValue,
                    { color: expectedValue > 0 ? colors.profit : colors.loss },
                  ]}
                >
                  {expectedValue > 0 ? '+' : ''}
                  {expectedValue.toFixed(2)}
                </Text>
              </View>

              <View style={styles.statCard}>
                <Text style={styles.statLabel}>Expected Value</Text>
                <Text
                  style={[
                    styles.statValue,
                    {
                      color:
                        winProbability * totalMultiplier > 1
                          ? colors.profit
                          : colors.loss,
                    },
                  ]}
                >
                  {((winProbability * totalMultiplier - 1) * 100).toFixed(1)}%
                </Text>
              </View>
            </View>

            {correlations && correlations.correlations && correlations.correlations.length > 0 && (
              <View style={styles.correlationSection}>
                <Text style={styles.correlationTitle}>Correlations</Text>
                {correlations.correlations
                  .filter((c: any) => Math.abs(c.correlation) > 0.3)
                  .map((corr: any, index: number) => (
                    <View key={index} style={styles.correlationCard}>
                      <Text style={styles.correlationText}>
                        {corr.player_1} vs {corr.player_2}
                      </Text>
                      <Text
                        style={[
                          styles.correlationValue,
                          {
                            color:
                              Math.abs(corr.correlation) > 0.5
                                ? colors.destructive
                                : colors.neutral,
                          },
                        ]}
                      >
                        {(corr.correlation * 100).toFixed(0)}%
                      </Text>
                    </View>
                  ))}
              </View>
            )}
          </View>
        )}
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity style={styles.placeButton}>
          <Text style={styles.placeButtonText}>Review & Place Bet</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  header: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    ...typography.h2,
    color: colors.foreground,
  },
  clearButton: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  clearButtonText: {
    ...typography.body,
    color: colors.destructive,
    fontWeight: '600',
  },
  itemsList: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
  },
  analysisSection: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.lg,
  },
  sectionTitle: {
    ...typography.h3,
    color: colors.foreground,
    marginBottom: spacing.md,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: colors.card,
    borderRadius: borderRadius.md,
    padding: spacing.md,
  },
  statLabel: {
    ...typography.caption,
    color: colors.mutedForeground,
    marginBottom: spacing.xs,
  },
  statValue: {
    ...typography.h3,
    color: colors.primary,
  },
  correlationSection: {
    marginTop: spacing.md,
  },
  correlationTitle: {
    ...typography.body,
    fontWeight: '600',
    color: colors.foreground,
    marginBottom: spacing.sm,
  },
  correlationCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.card,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    marginBottom: spacing.xs,
  },
  correlationText: {
    ...typography.bodySmall,
    color: colors.foreground,
    flex: 1,
  },
  correlationValue: {
    ...typography.body,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: spacing.md,
  },
  emptyTitle: {
    ...typography.h2,
    color: colors.foreground,
    marginBottom: spacing.sm,
    textAlign: 'center',
  },
  emptyText: {
    ...typography.body,
    color: colors.mutedForeground,
    textAlign: 'center',
  },
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: colors.card,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    padding: spacing.md,
  },
  placeButton: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
  },
  placeButtonText: {
    ...typography.button,
    color: colors.primaryForeground,
  },
});
