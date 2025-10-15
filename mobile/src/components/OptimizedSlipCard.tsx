/**
 * OptimizedSlipCard - Card for displaying optimized parlay sets
 */
import React, { memo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useSlipStore } from '@/lib/store/slip-store';
import { colors, spacing, typography, borderRadius, shadows } from '@/lib/theme/tokens';
import type { ParlayCandidate } from '@/types';

interface OptimizedSlipCardProps {
  parlay: ParlayCandidate;
}

export const OptimizedSlipCard = memo(({ parlay }: OptimizedSlipCardProps) => {
  const { clearSlip, items } = useSlipStore();

  const handleImport = () => {
    // Clear current slip
    clearSlip();

    // Add all legs from this optimized set
    parlay.legs.forEach((leg) => {
      const prediction = parlay.predictions.find(
        (p) => p.prop_leg_id === leg.id
      );
      useSlipStore.getState().addLeg(leg, prediction);
    });
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return colors.profit;
    if (score >= 0.6) return colors.accent;
    return colors.neutral;
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.rankBadge}>
          <Text style={styles.rankText}>#{parlay.rank}</Text>
        </View>
        <View style={styles.scoreContainer}>
          <Text style={styles.scoreLabel}>Score</Text>
          <Text style={[styles.scoreValue, { color: getScoreColor(parlay.score) }]}>
            {(parlay.score * 100).toFixed(0)}
          </Text>
        </View>
      </View>

      <View style={styles.statsRow}>
        <View style={styles.stat}>
          <Text style={styles.statLabel}>EV</Text>
          <Text
            style={[
              styles.statValue,
              { color: parlay.expected_value > 0 ? colors.profit : colors.loss },
            ]}
          >
            {parlay.expected_value > 0 ? '+' : ''}
            {parlay.expected_value.toFixed(2)}
          </Text>
        </View>

        <View style={styles.stat}>
          <Text style={styles.statLabel}>Win %</Text>
          <Text style={styles.statValue}>
            {(parlay.win_probability * 100).toFixed(1)}%
          </Text>
        </View>

        <View style={styles.stat}>
          <Text style={styles.statLabel}>Edge</Text>
          <Text style={[styles.statValue, { color: colors.accent }]}>
            {(parlay.total_edge * 100).toFixed(1)}%
          </Text>
        </View>

        <View style={styles.stat}>
          <Text style={styles.statLabel}>Legs</Text>
          <Text style={styles.statValue}>{parlay.legs.length}</Text>
        </View>
      </View>

      <View style={styles.legsContainer}>
        {parlay.legs.map((leg, index) => {
          const prediction = parlay.predictions[index];
          return (
            <View key={leg.id} style={styles.legRow}>
              <View style={styles.legInfo}>
                <Text style={styles.playerName} numberOfLines={1}>
                  {leg.player_name}
                </Text>
                <Text style={styles.legDetails}>
                  {leg.stat_type} {leg.direction.toUpperCase()} {leg.line}
                </Text>
              </View>
              {prediction && (
                <View style={styles.predictionInfo}>
                  <Text style={styles.confidence}>
                    {(prediction.confidence * 100).toFixed(0)}%
                  </Text>
                  <Text
                    style={[
                      styles.edge,
                      { color: prediction.edge > 0 ? colors.profit : colors.loss },
                    ]}
                  >
                    {prediction.edge > 0 ? '+' : ''}
                    {prediction.edge.toFixed(2)}
                  </Text>
                </View>
              )}
            </View>
          );
        })}
      </View>

      <View style={styles.footer}>
        <View style={styles.riskMetrics}>
          <View style={styles.riskItem}>
            <Text style={styles.riskLabel}>Max Corr</Text>
            <Text
              style={[
                styles.riskValue,
                {
                  color:
                    parlay.max_correlation > 0.5
                      ? colors.destructive
                      : parlay.max_correlation > 0.3
                      ? colors.neutral
                      : colors.profit,
                },
              ]}
            >
              {(parlay.max_correlation * 100).toFixed(0)}%
            </Text>
          </View>
          <View style={styles.riskItem}>
            <Text style={styles.riskLabel}>Diversity</Text>
            <Text style={[styles.riskValue, { color: colors.accent }]}>
              {(parlay.diversification_score * 100).toFixed(0)}
            </Text>
          </View>
        </View>

        <TouchableOpacity style={styles.importButton} onPress={handleImport}>
          <Text style={styles.importButtonText}>Add to Slip</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
});

OptimizedSlipCard.displayName = 'OptimizedSlipCard';

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    marginHorizontal: spacing.md,
    marginBottom: spacing.md,
    ...shadows.md,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  rankBadge: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
  },
  rankText: {
    ...typography.body,
    color: colors.primaryForeground,
    fontWeight: '700',
  },
  scoreContainer: {
    alignItems: 'flex-end',
  },
  scoreLabel: {
    ...typography.caption,
    color: colors.mutedForeground,
  },
  scoreValue: {
    ...typography.h3,
    fontWeight: '700',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: spacing.md,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.md,
  },
  stat: {
    alignItems: 'center',
  },
  statLabel: {
    ...typography.caption,
    color: colors.mutedForeground,
    marginBottom: spacing.xs,
  },
  statValue: {
    ...typography.body,
    color: colors.foreground,
    fontWeight: '600',
  },
  legsContainer: {
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  legRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: colors.background,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
  },
  legInfo: {
    flex: 1,
  },
  playerName: {
    ...typography.body,
    color: colors.foreground,
    fontWeight: '600',
    marginBottom: 2,
  },
  legDetails: {
    ...typography.bodySmall,
    color: colors.mutedForeground,
  },
  predictionInfo: {
    alignItems: 'flex-end',
    marginLeft: spacing.sm,
  },
  confidence: {
    ...typography.bodySmall,
    color: colors.accent,
    fontWeight: '600',
    marginBottom: 2,
  },
  edge: {
    ...typography.caption,
    fontWeight: '600',
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderColor: colors.border,
  },
  riskMetrics: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  riskItem: {
    alignItems: 'center',
  },
  riskLabel: {
    ...typography.caption,
    color: colors.mutedForeground,
    marginBottom: spacing.xs,
  },
  riskValue: {
    ...typography.bodySmall,
    fontWeight: '600',
  },
  importButton: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
  },
  importButtonText: {
    ...typography.body,
    color: colors.primaryForeground,
    fontWeight: '600',
  },
});
