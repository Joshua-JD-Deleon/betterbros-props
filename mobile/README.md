# BetterBros Props Mobile App

A production-ready React Native mobile app built with Expo for BetterBros Props betting platform. Features offline-first architecture, real-time data sync, and optimized performance for 60fps.

## Features

### Core Functionality
- **Props Feed**: Virtualized list of props with pull-to-refresh
- **Slip Builder**: Add/remove props with real-time predictions
- **Top Sets**: AI-optimized parlay recommendations
- **Insights**: Calibration metrics and performance analytics

### Offline Capabilities
- **AsyncStorage Persistence**: All data cached locally
- **Auto-sync on Launch**: Checks for latest props when app opens
- **Network Status Detection**: Shows offline banner with last sync time
- **React Query Offline Mode**: Serves cached data when offline
- **Zustand Persistence**: User preferences and slip stored locally

### Performance Optimizations
- **FlatList Virtualization**: Efficient rendering of large lists
- **Memoized Components**: Prevents unnecessary re-renders
- **Optimized Item Layouts**: Pre-calculated heights for smooth scrolling
- **Batch Rendering**: Limited renders per frame for 60fps
- **Haptic Feedback**: Native feel with optional haptics

## Tech Stack

- **Framework**: Expo 50 + React Native 0.73
- **Routing**: Expo Router (file-based routing)
- **State Management**: Zustand with AsyncStorage persistence
- **Data Fetching**: TanStack Query (React Query) v5 with offline support
- **Networking**: Axios with interceptors and offline detection
- **Styling**: StyleSheet with design tokens
- **Gestures**: React Native Gesture Handler
- **Animations**: React Native Reanimated

## Project Structure

```
mobile/
├── app.json                    # Expo configuration
├── babel.config.js            # Babel configuration
├── tsconfig.json              # TypeScript configuration
├── src/
│   ├── app/                   # Expo Router pages
│   │   ├── _layout.tsx       # Root layout with providers
│   │   └── (tabs)/           # Tab navigation
│   │       ├── _layout.tsx   # Tab layout
│   │       ├── index.tsx     # Props feed
│   │       ├── top-sets.tsx  # Optimized sets
│   │       ├── insights.tsx  # Analytics
│   │       └── slip.tsx      # Slip builder
│   ├── components/           # Reusable components
│   │   ├── PropCard.tsx
│   │   ├── OptimizedSlipCard.tsx
│   │   ├── SlipItemCard.tsx
│   │   ├── OfflineBanner.tsx
│   │   ├── FilterButton.tsx
│   │   └── CalibrationCard.tsx
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts     # API client with offline support
│   │   │   └── query-client.ts # React Query configuration
│   │   ├── store/
│   │   │   ├── slip-store.ts  # Slip state (persisted)
│   │   │   └── ui-store.ts    # UI state (persisted)
│   │   └── theme/
│   │       └── tokens.ts      # Design tokens
│   ├── hooks/                 # Custom hooks
│   │   ├── use-props.ts
│   │   ├── use-optimization.ts
│   │   ├── use-insights.ts
│   │   └── use-network-status.ts
│   └── types/                 # TypeScript types
│       └── index.ts
```

## Setup

### Prerequisites
- Node.js 18+
- npm or yarn
- Expo CLI: `npm install -g expo-cli`
- iOS Simulator (Mac) or Android Emulator

### Installation

1. **Install dependencies**:
```bash
cd mobile
npm install
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your API URL
```

3. **Start development server**:
```bash
npm start
```

4. **Run on iOS**:
```bash
npm run ios
```

5. **Run on Android**:
```bash
npm run android
```

## Offline Architecture

### How Offline Sync Works

1. **On App Launch**:
   - Check network connectivity with NetInfo
   - If online, fetch latest props and predictions
   - Store snapshot_id and timestamp in AsyncStorage
   - Cache all data in React Query + AsyncStorage

2. **During Use**:
   - All queries use `networkMode: 'offlineFirst'`
   - Stale data served immediately, then refetched in background
   - Network errors fallback to cached data
   - Offline banner shows when disconnected

3. **Manual Refresh**:
   - Pull-to-refresh triggers new fetch
   - Updates cache and last_sync timestamp
   - Invalidates stale queries

4. **Mutations**:
   - Only work when online
   - Queue for retry when connection restored (future enhancement)

### Storage Strategy

- **React Query Cache**: Short-term (5-30 min stale time)
- **AsyncStorage Persistence**: Long-term (survives app restarts)
- **Zustand Store**: User preferences and slip (persisted)
- **Last Sync Metadata**: Timestamp and snapshot_id

## API Integration

### Endpoints Used

- `GET /props` - Fetch props markets
- `POST /model/predict` - Get predictions
- `POST /optimize` - Optimize parlays
- `GET /optimize/slips` - Detect slip opportunities
- `POST /correlations` - Calculate correlations
- `GET /eval/calibration` - Calibration metrics

### Authentication

Currently uses bearer token auth. To integrate Clerk or Supabase:

1. **Install SDK**:
```bash
npm install @clerk/clerk-expo
# or
npm install @supabase/supabase-js
```

2. **Update API client** (`src/lib/api/client.ts`):
```typescript
// Add auth provider initialization
// Update getAuthToken() to use Clerk/Supabase
```

## Performance Targets

- **App Launch**: < 2 seconds (cold start)
- **Frame Rate**: Consistent 60fps scrolling
- **Memory**: < 150MB baseline
- **Network Efficiency**: Batch requests, cache aggressively

## Development

### Type Checking
```bash
npm run type-check
```

### Linting
```bash
npm run lint
```

### Building for Production

**iOS**:
```bash
expo build:ios
```

**Android**:
```bash
expo build:android
```

### EAS Build (Recommended)
```bash
eas build --platform ios
eas build --platform android
```

## Future Enhancements

### Phase 1 (Current)
- ✅ Offline caching
- ✅ Auto-refresh on launch
- ✅ Virtualized lists
- ✅ Design tokens matching web

### Phase 2 (Planned)
- [ ] Push notifications for line movements
- [ ] Biometric authentication
- [ ] Background refresh
- [ ] Optimistic UI updates
- [ ] Offline mutation queue
- [ ] Deep linking
- [ ] Share slip functionality

### Phase 3 (Future)
- [ ] Live odds tracking
- [ ] In-app notifications
- [ ] Settings screen
- [ ] Historical performance graphs
- [ ] Player search
- [ ] Filter persistence

## Troubleshooting

### Metro bundler issues
```bash
rm -rf node_modules
npm install
npx expo start -c
```

### iOS build issues
```bash
cd ios
pod install
cd ..
npm run ios
```

### Cache issues
```bash
npx expo start -c
# Clear AsyncStorage in app settings
```

## Design System

Colors, spacing, and typography match the web app's design tokens. See `src/lib/theme/tokens.ts` for the complete design system.

Key colors:
- Primary: `#2563eb` (blue-600)
- Background: `#0f172a` (slate-900)
- Card: `#1e293b` (slate-800)
- Profit: `#22c55e` (green-500)
- Loss: `#ef4444` (red-500)

## Contributing

1. Create feature branch
2. Make changes with TypeScript + ESLint compliance
3. Test on both iOS and Android
4. Ensure 60fps performance
5. Submit PR with description

## License

Proprietary - BetterBros
