/**
 * CalibrationCard - Displays calibration metrics and curve
 */
import React, { memo } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing, typography, borderRadius } from '@/lib/theme/tokens';
import type { CalibrationMetrics } from '@/types';

interface CalibrationCardProps {
  metrics: CalibrationMetrics;
}

export const CalibrationCard = memo(({ metrics }: CalibrationCardProps) => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Calibration Curve</Text>
      <Text style={styles.subtitle}>
        How well predicted probabilities match actual outcomes
      </Text>

      {metrics.calibration_curve && metrics.calibration_curve.length > 0 && (
        <View style={styles.curveContainer}>
          {metrics.calibration_curve.map((point, index) => {
            const deviation = Math.abs(point.predicted_prob - point.actual_prob);
            const barHeight = point.actual_prob * 100;
            const isWellCalibrated = deviation < 0.1;

            return (
              <View key={index} style={styles.curveBar}>
                <View
                  style={[
                    styles.bar,
                    {
                      height: `${barHeight}%`,
                      backgroundColor: isWellCalibrated
                        ? colors.profit
                        : deviation < 0.2
                        ? colors.neutral
                        : colors.loss,
                    },
                  ]}
                />
                <Text style={styles.barLabel}>
                  {(point.predicted_prob * 100).toFixed(0)}
                </Text>
              </View>
            );
          })}
        </View>
      )}

      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.profit }]} />
          <Text style={styles.legendText}>Well calibrated</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.neutral }]} />
          <Text style={styles.legendText}>Moderate</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.loss }]} />
          <Text style={styles.legendText}>Poor</Text>
        </View>
      </View>
    </View>
  );
});

CalibrationCard.displayName = 'CalibrationCard';

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.card,
    borderRadius: borderRadius.lg,
    padding: spacing.md,
    marginHorizontal: spacing.md,
    marginTop: spacing.md,
  },
  title: {
    ...typography.h3,
    color: colors.foreground,
    marginBottom: spacing.xs,
  },
  subtitle: {
    ...typography.bodySmall,
    color: colors.mutedForeground,
    marginBottom: spacing.md,
  },
  curveContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'flex-end',
    height: 120,
    marginBottom: spacing.md,
  },
  curveBar: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginHorizontal: 2,
  },
  bar: {
    width: '100%',
    borderTopLeftRadius: 4,
    borderTopRightRadius: 4,
    minHeight: 4,
  },
  barLabel: {
    ...typography.caption,
    color: colors.mutedForeground,
    marginTop: spacing.xs,
    fontSize: 10,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: spacing.md,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.xs,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    ...typography.caption,
    color: colors.mutedForeground,
  },
});
