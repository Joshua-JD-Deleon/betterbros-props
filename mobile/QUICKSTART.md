# BetterBros Props Mobile - Quick Start Guide

Get the mobile app running in 5 minutes.

## Prerequisites

- **Node.js** 18+ installed
- **Expo CLI**: `npm install -g expo-cli`
- **iOS**: Xcode and iOS Simulator (Mac only)
- **Android**: Android Studio and Emulator

## Setup Steps

### 1. Install Dependencies

```bash
cd mobile
npm install
```

This installs:
- Expo 50
- React Native 0.73
- React Query with persistence
- Zustand for state
- All required dependencies

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```bash
# Point to your running API
API_URL=http://localhost:8000
API_TIMEOUT=15000
NODE_ENV=development
```

**Important**:
- For iOS Simulator: Use `http://localhost:8000`
- For Android Emulator: Use `http://10.0.2.2:8000`
- For Physical Device: Use your computer's IP (e.g., `http://192.168.1.100:8000`)

### 3. Start the Development Server

```bash
npm start
```

This opens Expo DevTools in your browser.

### 4. Run on iOS Simulator

```bash
# Option 1: From terminal
npm run ios

# Option 2: From Expo DevTools
# Press 'i' in the terminal
```

**First launch**: Installs Expo Go app automatically

### 5. Run on Android Emulator

```bash
# Make sure Android emulator is running first
# Then:
npm run android

# Or press 'a' in Expo DevTools
```

## Verify Installation

After the app launches, you should see:

1. **Props Tab** (default): Empty or loading state
2. **Top Sets Tab**: Optimized parlay recommendations
3. **Insights Tab**: Calibration metrics
4. **Slip Tab**: Empty slip builder

## Testing Offline Mode

1. **Turn off WiFi** on your device/simulator
2. **Offline banner** should appear at top
3. **Pull to refresh** - should show cached data
4. **Turn WiFi back on** - banner disappears, auto-syncs

## Common Issues

### Port 8000 Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or change API_URL in .env to different port
```

### Can't Connect to API
```bash
# Check API is running
curl http://localhost:8000/health

# For Android, use special IP
API_URL=http://10.0.2.2:8000

# For physical device, use computer's local IP
API_URL=http://192.168.1.XXX:8000
```

### Metro Bundler Cache Issues
```bash
# Clear cache and restart
npx expo start -c
```

### iOS Build Errors
```bash
# Clean and reinstall pods
cd ios
pod deintegrate
pod install
cd ..
npm run ios
```

### Android Build Errors
```bash
# Clean gradle cache
cd android
./gradlew clean
cd ..
npm run android
```

## Development Workflow

### 1. Making Changes
- **Hot Reload**: Most changes auto-refresh
- **Shake Device**: Opens developer menu
- **Cmd+D (iOS) / Cmd+M (Android)**: Developer menu

### 2. Debugging
```bash
# Open React DevTools
npx react-devtools

# View logs
# iOS: Xcode Console
# Android: Android Studio Logcat
# Both: Terminal running 'npm start'
```

### 3. Testing Features

**Add Props to Slip**:
1. Go to Props tab
2. Tap any prop card leg
3. Checkbox turns blue
4. Go to Slip tab - see added prop

**View Optimized Sets**:
1. Go to Top Sets tab
2. See AI-optimized parlays
3. Tap "Add to Slip" to import

**Check Insights**:
1. Go to Insights tab
2. View calibration curve
3. See model metrics

## Next Steps

### Add Real Data
1. Start your API backend: `cd apps/api && python main.py`
2. Mobile app auto-connects to `API_URL`
3. Pull to refresh to fetch latest props

### Customize
1. Edit design tokens: `src/lib/theme/tokens.ts`
2. Adjust filters: `src/lib/store/ui-store.ts`
3. Modify screens: `src/app/(tabs)/*.tsx`

### Deploy

**iOS TestFlight**:
```bash
eas build --platform ios
eas submit --platform ios
```

**Android Play Store**:
```bash
eas build --platform android
eas submit --platform android
```

## Useful Commands

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Clear all caches
npx expo start -c
rm -rf node_modules
npm install

# Update dependencies
npx expo install --check
npx expo install --fix
```

## File Structure Reference

```
mobile/
├── src/
│   ├── app/              # Screens (Expo Router)
│   ├── components/       # Reusable UI components
│   ├── lib/
│   │   ├── api/         # API client + React Query
│   │   ├── store/       # Zustand stores
│   │   └── theme/       # Design tokens
│   ├── hooks/           # Custom hooks
│   └── types/           # TypeScript types
├── app.json             # Expo config
├── tsconfig.json        # TypeScript config
└── package.json         # Dependencies
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_URL` | Backend API endpoint | `http://localhost:8000` |
| `API_TIMEOUT` | Request timeout (ms) | `15000` |
| `NODE_ENV` | Environment | `development` |

## Performance Tips

1. **Use Production Build**: `expo build` is optimized
2. **Enable Hermes**: Included by default in Expo 50
3. **Profile with Flipper**: Install Flipper for debugging
4. **Monitor Memory**: Use Xcode Instruments / Android Profiler

## Support

- **Expo Docs**: https://docs.expo.dev
- **React Native Docs**: https://reactnative.dev
- **React Query Docs**: https://tanstack.com/query

## Ready to Code?

```bash
# Start coding!
cd mobile
npm start
# Open src/app/(tabs)/index.tsx
# Make changes and see them live
```

Happy coding! 🚀
