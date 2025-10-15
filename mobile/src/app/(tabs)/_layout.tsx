/**
 * Tabs layout with bottom navigation
 */
import { Tabs } from 'expo-router';
import { Platform } from 'react-native';
import { colors } from '@/lib/theme/tokens';

// Simple icon components (you can replace with icon library)
const TabBarIcon = ({ name, color }: { name: string; color: string }) => {
  const icons: Record<string, string> = {
    props: '📋',
    'top-sets': '⭐',
    insights: '📊',
    slip: '🎫',
  };
  return <span style={{ fontSize: 24 }}>{icons[name] || '•'}</span>;
};

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.mutedForeground,
        tabBarStyle: {
          backgroundColor: colors.card,
          borderTopColor: colors.border,
          borderTopWidth: 1,
          paddingBottom: Platform.OS === 'ios' ? 20 : 10,
          height: Platform.OS === 'ios' ? 88 : 68,
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '600',
        },
        headerStyle: {
          backgroundColor: colors.background,
          borderBottomColor: colors.border,
          borderBottomWidth: 1,
        },
        headerTintColor: colors.foreground,
        headerTitleStyle: {
          fontWeight: '700',
          fontSize: 20,
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Props',
          tabBarIcon: ({ color }) => <TabBarIcon name="props" color={color} />,
          headerTitle: 'Props Feed',
        }}
      />
      <Tabs.Screen
        name="top-sets"
        options={{
          title: 'Top Sets',
          tabBarIcon: ({ color }) => <TabBarIcon name="top-sets" color={color} />,
          headerTitle: 'Optimized Sets',
        }}
      />
      <Tabs.Screen
        name="insights"
        options={{
          title: 'Insights',
          tabBarIcon: ({ color }) => <TabBarIcon name="insights" color={color} />,
          headerTitle: 'Analytics',
        }}
      />
      <Tabs.Screen
        name="slip"
        options={{
          title: 'Slip',
          tabBarIcon: ({ color }) => <TabBarIcon name="slip" color={color} />,
          headerTitle: 'My Slip',
        }}
      />
    </Tabs>
  );
}
