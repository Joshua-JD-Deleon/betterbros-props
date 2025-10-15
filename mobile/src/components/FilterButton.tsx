/**
 * FilterButton - Button to open filter sheet
 */
import React, { memo } from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { useUIStore } from '@/lib/store/ui-store';
import { colors, spacing, typography, borderRadius } from '@/lib/theme/tokens';

export const FilterButton = memo(() => {
  const setFilterSheetOpen = useUIStore((state) => state.setFilterSheetOpen);

  return (
    <TouchableOpacity
      style={styles.button}
      onPress={() => setFilterSheetOpen(true)}
    >
      <Text style={styles.icon}>⚙️</Text>
      <Text style={styles.text}>Filters</Text>
    </TouchableOpacity>
  );
});

FilterButton.displayName = 'FilterButton';

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.secondary,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.sm,
    paddingVertical: spacing.xs,
    gap: spacing.xs,
  },
  icon: {
    fontSize: 14,
  },
  text: {
    ...typography.bodySmall,
    color: colors.foreground,
    fontWeight: '600',
  },
});
