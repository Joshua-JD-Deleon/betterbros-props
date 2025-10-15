/**
 * Root layout with providers and offline sync
 */
import { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client';
import { queryClient, asyncStoragePersister } from '@/lib/api/query-client';
import { offlineSyncManager } from '@/lib/offline-sync';

export default function RootLayout() {
  useEffect(() => {
    // Initialize app and trigger sync on mount
    const initializeApp = async () => {
      console.log('App initialized, checking for updates...');

      // Check if cache is stale (older than 5 minutes)
      const isStale = await offlineSyncManager.isCacheStale(5 * 60 * 1000);

      if (isStale) {
        console.log('Cache is stale, syncing...');
        await offlineSyncManager.syncWhenOnline();
      } else {
        console.log('Cache is fresh, skipping sync');
      }
    };

    initializeApp();
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <PersistQueryClientProvider
          client={queryClient}
          persistOptions={{ persister: asyncStoragePersister }}
        >
          <StatusBar style="light" />
          <Stack
            screenOptions={{
              headerStyle: {
                backgroundColor: '#0f172a',
              },
              headerTintColor: '#f1f5f9',
              headerTitleStyle: {
                fontWeight: '600',
              },
              contentStyle: {
                backgroundColor: '#0f172a',
              },
            }}
          >
            <Stack.Screen
              name="(tabs)"
              options={{
                headerShown: false,
              }}
            />
          </Stack>
        </PersistQueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
