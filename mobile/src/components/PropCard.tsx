/**
 * PropCard - Touchable card for individual prop
 * Optimized for 60fps with minimal re-renders
 */
import React, { memo, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Pressable,
} from 'react-native';
import * as Haptics from 'expo-haptics';
import { useSlipStore } from '@/lib/store/slip-store';
import { useUIStore } from '@/lib/store/ui-store';
import { colors, spacing, typography, borderRadius, shadows } from '@/lib/theme/tokens';
import type { PropMarket } from '@/types';

interface PropCardProps {
  market: PropMarket;
}

export const PropCard = memo(({ market }: PropCardProps) => {
  const { toggleLeg, hasLeg } = useSlipStore();
  const hapticEnabled = useUIStore((state) => state.preferences.hapticFeedback);

  const handleToggleLeg = useCallback((leg: any) => {
    if (hapticEnabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    toggleLeg(leg);
  }, [toggleLeg, hapticEnabled]);

  // Get first leg for preview
  const firstLeg = market.legs[0];
  if (!firstLeg) return null;

  const isSelected = hasLeg(firstLeg.id);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.platform}>{market.platform.toUpperCase()}</Text>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{market.legs.length} Legs</Text>
          </View>
        </View>
        <View style={styles.headerRight}>
          <Text style={styles.multiplier}>{market.payout_multiplier}x</Text>
        </View>
      </View>

      <View style={styles.legsContainer}>
        {market.legs.slice(0, 3).map((leg) => {
          const isLegSelected = hasLeg(leg.id);
          return (
            <Pressable
              key={leg.id}
              style={({ pressed }) => [
                styles.legCard,
                isLegSelected && styles.legCardSelected,
                pressed && styles.legCardPressed,
              ]}
              onPress={() => handleToggleLeg(leg)}
            >
              <View style={styles.legHeader}>
                <Text style={styles.playerName} numberOfLines={1}>
                  {leg.player_name}
                </Text>
                <View style={styles.checkbox}>
                  {isLegSelected && <View style={styles.checkboxInner} />}
                </View>
              </View>

              <View style={styles.legDetails}>
                <Text style={styles.statType}>{leg.stat_type}</Text>
                <View style={styles.lineContainer}>
                  <Text style={styles.direction}>
                    {leg.direction.toUpperCase()}
                  </Text>
                  <Text style={styles.line}>{leg.line}</Text>
                </View>
              </View>

              <View style={styles.legFooter}>
                <Text style={styles.team}>{leg.team}</Text>
                <Text style={styles.opponent}>vs {leg.opponent}</Text>
              </View>
            </Pressable>
          );
        })}

        {market.legs.length > 3 && (
          <View style={styles.moreLegs}>
            <Text style={styles.moreLegsText}>
              +{market.legs.length - 3} more legs
            </Text>
          </View>
        )}
      </View>
    </View>
  );
});

PropCard.displayName = 'PropCard';

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
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  headerRight: {
    backgroundColor: colors.primary,
    borderRadius: borderRadius.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: 4,
  },
  platform: {
    ...typography.caption,
    color: colors.mutedForeground,
    fontWeight: '600',
  },
  badge: {
    backgroundColor: colors.secondary,
    borderRadius: borderRadius.sm,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
  },
  badgeText: {
    ...typography.caption,
    color: colors.foreground,
    fontWeight: '500',
  },
  multiplier: {
    ...typography.body,
    color: colors.primaryForeground,
    fontWeight: '700',
  },
  legsContainer: {
    gap: spacing.sm,
  },
  legCard: {
    backgroundColor: colors.background,
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  legCardSelected: {
    borderColor: colors.primary,
    backgroundColor: `${colors.primary}15`,
  },
  legCardPressed: {
    opacity: 0.7,
  },
  legHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  playerName: {
    ...typography.body,
    color: colors.foreground,
    fontWeight: '600',
    flex: 1,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxInner: {
    width: 12,
    height: 12,
    borderRadius: 2,
    backgroundColor: colors.primary,
  },
  legDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.xs,
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
  legFooter: {
    flexDirection: 'row',
    gap: spacing.xs,
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
  moreLegs: {
    paddingVertical: spacing.sm,
    alignItems: 'center',
  },
  moreLegsText: {
    ...typography.bodySmall,
    color: colors.mutedForeground,
  },
});
