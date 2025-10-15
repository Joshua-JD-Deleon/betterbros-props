/**
 * SlipItemCard - Card for slip item with swipe-to-delete
 */
import React, { memo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useSlipStore } from '@/lib/store/slip-store';
import { colors, spacing, typography, borderRadius } from '@/lib/theme/tokens';
import type { SlipItem, ModelPrediction } from '@/types';

interface SlipItemCardProps {
  item: SlipItem;
  prediction?: ModelPrediction;
}

export const SlipItemCard = memo(({ item, prediction }: SlipItemCardProps) => {
  const removeLeg = useSlipStore((state) => state.removeLeg);

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.playerName} numberOfLines={1}>
            {item.leg.player_name}
          </Text>
          <TouchableOpacity
            onPress={() => removeLeg(item.leg.id)}
            style={styles.removeButton}
          >
            <Text style={styles.removeText}>✕</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.details}>
          <Text style={styles.statType}>{item.leg.stat_type}</Text>
          <View style={styles.lineContainer}>
            <Text style={styles.direction}>
              {item.leg.direction.toUpperCase()}
            </Text>
            <Text style={styles.line}>{item.leg.line}</Text>
          </View>
        </View>

        <View style={styles.matchup}>
          <Text style={styles.team}>{item.leg.team}</Text>
          <Text style={styles.opponent}>vs {item.leg.opponent}</Text>
        </View>

        {prediction && (
          <View style={styles.predictionContainer}>
            <View style={styles.predictionRow}>
              <View style={styles.predictionStat}>
                <Text style={styles.predictionLabel}>Projected</Text>
                <Text style={styles.predictionValue}>
                  {prediction.predicted_value.toFixed(1)}
                </Text>
              </View>
              <View style={styles.predictionStat}>
                <Text style={styles.predictionLabel}>Confidence</Text>
                <Text style={styles.predictionValue}>
                  {(prediction.confidence * 100).toFixed(0)}%
                </Text>
              </View>
              <View style={styles.predictionStat}>
                <Text style={styles.predictionLabel}>Edge</Text>
                <Text
                  style={[
                    styles.predictionValue,
                    { color: prediction.edge > 0 ? colors.profit : colors.loss },
                  ]}
                >
                  {prediction.edge > 0 ? '+' : ''}
                  {prediction.edge.toFixed(2)}
                </Text>
              </View>
            </View>
          </View>
        )}
      </View>
    </View>
  );
});

SlipItemCard.displayName = 'SlipItemCard';

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.md,
    overflow: 'hidden',
  },
  content: {
    padding: spacing.md,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  playerName: {
    ...typography.body,
    color: colors.foreground,
    fontWeight: '600',
    flex: 1,
  },
  removeButton: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.destructive,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: spacing.sm,
  },
  removeText: {
    color: colors.destructiveForeground,
    fontSize: 16,
    fontWeight: '600',
  },
  details: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  statType: {
    ...typography.bodySmall,
    color: colors.mutedForeground,
    textTransform: 'capitalize',
  },
  lineContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  direction: {
    ...typography.caption,
    color: colors.accent,
    fontWeight: '700',
  },
  line: {
    ...typography.body,
    color: colors.foreground,
    fontWeight: '700',
  },
  matchup: {
    flexDirection: 'row',
    gap: spacing.xs,
    marginBottom: spacing.sm,
  },
  team: {
    ...typography.caption,
    color: colors.foreground,
    fontWeight: '600',
  },
  opponent: {
    ...typography.caption,
    color: colors.mutedForeground,
  },
  predictionContainer: {
    backgroundColor: colors.background,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    marginTop: spacing.sm,
  },
  predictionRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  predictionStat: {
    alignItems: 'center',
  },
  predictionLabel: {
    ...typography.caption,
    color: colors.mutedForeground,
    marginBottom: spacing.xs,
  },
  predictionValue: {
    ...typography.body,
    color: colors.foreground,
    fontWeight: '600',
  },
});
