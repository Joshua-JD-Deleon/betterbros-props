/**
 * OfflineBanner - Shows when app is offline
 */
import React, { memo } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useUIStore } from '@/lib/store/ui-store';
import { colors, spacing, typography } from '@/lib/theme/tokens';
import { formatDistanceToNow } from 'date-fns';

export const OfflineBanner = memo(() => {
  const lastSyncTime = useUIStore((state) => state.lastSyncTime);

  return (
    <View style={styles.container}>
      <Text style={styles.icon}>📡</Text>
      <View style={styles.textContainer}>
        <Text style={styles.title}>Offline Mode</Text>
        {lastSyncTime && (
          <Text style={styles.subtitle}>
            Last synced {formatDistanceToNow(lastSyncTime, { addSuffix: true })}
          </Text>
        )}
        {!lastSyncTime && (
          <Text style={styles.subtitle}>No cached data available</Text>
        )}
      </View>
    </View>
  );
});

OfflineBanner.displayName = 'OfflineBanner';

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.neutral,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    gap: spacing.sm,
  },
  icon: {
    fontSize: 20,
  },
  textContainer: {
    flex: 1,
  },
  title: {
    ...typography.body,
    color: colors.foreground,
    fontWeight: '600',
  },
  subtitle: {
    ...typography.caption,
    color: colors.neutralForeground,
  },
});
