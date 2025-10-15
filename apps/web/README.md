# BetterBros Web Application

Professional sportsbook-style props trading platform built with Next.js 15, featuring real-time data, advanced analytics, and seamless bet slip management.

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand (UI state + slip builder)
- **Data Fetching**: TanStack Query (React Query v5)
- **Authentication**: Clerk + Supabase
- **Animations**: Framer Motion
- **Icons**: Lucide React

## Project Structure

```
apps/web/
├── src/
│   ├── app/                      # Next.js App Router pages
│   │   ├── (auth)/              # Auth pages (sign-in/sign-up)
│   │   ├── (dashboard)/         # Dashboard layout & pages
│   │   ├── layout.tsx           # Root layout with providers
│   │   ├── providers.tsx        # React Query provider
│   │   └── globals.css          # Global styles & design tokens
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   └── table.tsx
│   │   └── app/                 # Application components
│   │       ├── dashboard-shell.tsx
│   │       ├── props-table.tsx
│   │       ├── slip-drawer.tsx
│   │       ├── filter-panel.tsx
│   │       ├── prop-card.tsx
│   │       ├── trend-chips.tsx
│   │       ├── calibration-monitor.tsx
│   │       └── correlation-heatmap.tsx
│   └── lib/
│       ├── api/
│       │   └── client.ts        # API client with auth
│       ├── auth/
│       │   ├── clerk.ts         # Clerk utilities
│       │   └── supabase.ts      # Supabase client & services
│       ├── store/
│       │   ├── ui-store.ts      # UI state (filters, theme, drawer)
│       │   └── slip-store.ts    # Bet slip builder
│       ├── theme/
│       │   └── tokens.ts        # Design system tokens
│       └── utils.ts             # Utility functions
├── public/                       # Static assets
├── next.config.js               # Next.js configuration
├── tailwind.config.ts           # Tailwind configuration
├── tsconfig.json                # TypeScript configuration
├── postcss.config.js            # PostCSS configuration
├── components.json              # shadcn/ui configuration
└── middleware.ts                # Clerk auth middleware
```

## Getting Started

### Prerequisites

- Node.js 18+ and pnpm
- Clerk account (for authentication)
- Supabase account (for database)

### Installation

1. Install dependencies:
```bash
cd apps/web
pnpm install
```

2. Set up environment variables:
```bash
cp .env.example .env
```

Fill in your Clerk and Supabase credentials.

3. Run development server:
```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Key Features

### 1. Dashboard Shell
- Collapsible left sidebar with filters
- Top navigation with user profile
- Right drawer for bet slip
- Responsive layout optimized for desktop

### 2. Props Table
- Real-time props with calculated EV
- Sortable columns (EV, odds, probability)
- Live game indicators
- Quick add to slip

### 3. Bet Slip Builder
- Add/remove props
- Auto-stake with Kelly Criterion
- Single bets and parlays
- Correlation warnings
- Live EV calculations

### 4. State Management

#### UI Store (Zustand)
- Theme (dark/light/system)
- Sidebar collapsed state
- Drawer open/closed
- View mode (table/cards/compact)
- Sorting preferences
- Filters (sports, markets, EV range)

#### Slip Store (Zustand)
- Bet slip entries
- Bankroll management
- Kelly fraction settings
- Auto-stake toggle
- Parlay calculations
- Bet history

### 5. Design System

#### Colors
- Dark theme optimized for sportsbook
- Profit (green) and loss (red) semantic colors
- Live indicator (orange) for in-progress games
- Neutral grays for secondary content

#### Typography
- Inter for UI text
- JetBrains Mono for odds/numbers
- Bold weights for emphasis

#### Animations
- Framer Motion for smooth transitions
- Slide-in drawer
- Fade-in content
- Hover effects on cards

## API Integration

The app connects to the FastAPI backend via the API client (`lib/api/client.ts`):

```typescript
import { apiClient } from '@/lib/api/client';

// Example: Fetch props
const props = await apiClient.get('/api/props', {
  params: { sport: 'NBA', minEV: 3 }
});
```

All requests automatically include Clerk authentication headers.

## Styling Guidelines

### Using Design Tokens
```tsx
import { colors, spacing, animations } from '@/lib/theme/tokens';

// Use in motion components
<motion.div {...animations.fadeIn}>
  Content
</motion.div>
```

### Utility Classes
```tsx
// EV formatting
<span className="ev-positive">+4.2%</span>
<span className="ev-negative">-2.1%</span>

// Odds display
<span className="odds-american">-110</span>

// Custom scrollbar
<div className="custom-scrollbar">...</div>
```

## Performance Optimizations

- **Code Splitting**: Dynamic imports for heavy components
- **Image Optimization**: Next.js Image component
- **React Query**: Intelligent caching and background refetching
- **Zustand**: Minimal re-renders with selective subscriptions
- **Suspense**: Loading states for async components

## Deployment

### Vercel (Recommended)
```bash
vercel
```

### Docker
```bash
docker build -t betterbros-web .
docker run -p 3000:3000 betterbros-web
```

### Build for Production
```bash
pnpm build
pnpm start
```

## Environment Variables

See `.env.example` for required variables:

- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`: Clerk public key
- `CLERK_SECRET_KEY`: Clerk secret key
- `NEXT_PUBLIC_SUPABASE_URL`: Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
- `NEXT_PUBLIC_API_URL`: Backend API URL

## Development Commands

```bash
pnpm dev          # Start dev server
pnpm build        # Build for production
pnpm start        # Start production server
pnpm lint         # Run ESLint
pnpm typecheck    # Run TypeScript compiler check
```

## Contributing

1. Follow the component structure in `src/components/`
2. Use TypeScript for all new files
3. Follow the design system tokens
4. Add proper error boundaries
5. Optimize for performance (lazy load, memoize)

## License

Proprietary - BetterBros
