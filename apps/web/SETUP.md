# BetterBros Web Setup Guide

Quick setup guide for the Next.js 15 frontend application.

## Installation Steps

### 1. Install Dependencies

```bash
cd apps/web
pnpm install
```

This will install all required packages including:
- Next.js 15
- React 18
- Tailwind CSS
- shadcn/ui components
- Clerk authentication
- Supabase client
- TanStack Query
- Zustand
- Framer Motion

### 2. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Fill in the following required values in `.env`:

```bash
# Clerk (get from https://clerk.com)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# Supabase (get from https://supabase.com)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Set Up Clerk Authentication

1. Go to [clerk.com](https://clerk.com) and create an account
2. Create a new application
3. Copy the publishable key and secret key to your `.env` file
4. Configure redirect URLs:
   - Sign in URL: `/sign-in`
   - Sign up URL: `/sign-up`
   - After sign in URL: `/`
   - After sign up URL: `/`

### 4. Set Up Supabase Database

1. Go to [supabase.com](https://supabase.com) and create a project
2. Copy the project URL and anon key to your `.env` file
3. Create the following tables using the SQL editor:

```sql
-- User profiles
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_id TEXT UNIQUE NOT NULL,
  email TEXT NOT NULL,
  bankroll DECIMAL(10, 2) DEFAULT 1000.00,
  total_profit DECIMAL(10, 2) DEFAULT 0.00,
  total_bets INTEGER DEFAULT 0,
  win_rate DECIMAL(5, 2) DEFAULT 0.00,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prop bets
CREATE TABLE prop_bets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prop_id TEXT NOT NULL,
  user_id UUID REFERENCES user_profiles(id),
  market TEXT NOT NULL,
  selection TEXT NOT NULL,
  odds INTEGER NOT NULL,
  stake DECIMAL(10, 2) NOT NULL,
  expected_value DECIMAL(10, 4) NOT NULL,
  result TEXT CHECK (result IN ('win', 'loss', 'push')),
  placed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  settled_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_user_profiles_clerk_id ON user_profiles(clerk_id);
CREATE INDEX idx_prop_bets_user_id ON prop_bets(user_id);
CREATE INDEX idx_prop_bets_placed_at ON prop_bets(placed_at DESC);
```

### 5. Run Development Server

```bash
pnpm dev
```

The app will be available at [http://localhost:3000](http://localhost:3000)

## Troubleshooting

### Port Already in Use

If port 3000 is already in use:

```bash
pnpm dev -- -p 3001
```

### TypeScript Errors

Run type checking:

```bash
pnpm typecheck
```

### Build Errors

Clear Next.js cache:

```bash
rm -rf .next
pnpm dev
```

### Missing Dependencies

If you see import errors, ensure all dependencies are installed:

```bash
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

## shadcn/ui Components

The project uses shadcn/ui components. To add more components:

```bash
npx shadcn@latest add dialog
npx shadcn@latest add dropdown-menu
npx shadcn@latest add tabs
npx shadcn@latest add slider
npx shadcn@latest add select
```

## Project Structure Quick Reference

```
apps/web/
├── src/
│   ├── app/                      # Next.js pages (App Router)
│   │   ├── (auth)/              # Sign in/up pages
│   │   ├── (dashboard)/         # Main dashboard
│   │   ├── layout.tsx           # Root layout
│   │   ├── providers.tsx        # React Query provider
│   │   └── globals.css          # Global styles
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   └── app/                 # App-specific components
│   └── lib/
│       ├── api/                 # API client
│       ├── auth/                # Auth utilities
│       ├── store/               # Zustand stores
│       ├── theme/               # Design tokens
│       └── utils.ts             # Utility functions
├── public/                       # Static files
├── next.config.js               # Next.js config
├── tailwind.config.ts           # Tailwind config
└── tsconfig.json                # TypeScript config
```

## Available Scripts

```bash
pnpm dev          # Start development server
pnpm build        # Build for production
pnpm start        # Start production server
pnpm lint         # Run ESLint
pnpm typecheck    # Check TypeScript types
```

## Next Steps

1. **Connect to Backend**: Ensure the FastAPI backend is running on `http://localhost:8000`
2. **Test Authentication**: Visit `/sign-in` to test Clerk authentication
3. **Explore Dashboard**: Navigate to `/` to see the props dashboard
4. **Add Props to Slip**: Click "Add" on any prop to add it to the bet slip
5. **Open Slip Drawer**: Click the "Slip" button in the top nav

## Development Tips

### Hot Reload
Next.js automatically hot reloads when you save files. No need to restart the server.

### Component Development
Use the dashboard page to test new components in isolation.

### State Management
- Use `useUIStore` for UI state (filters, theme, drawer)
- Use `useSlipStore` for bet slip management
- Use TanStack Query for server state

### Styling
- Use Tailwind utility classes for styling
- Reference design tokens in `lib/theme/tokens.ts`
- Use custom utility classes defined in `globals.css`

### Type Safety
All components use TypeScript. Run `pnpm typecheck` to catch type errors.

## Support

For issues or questions:
1. Check the README.md
2. Review component documentation
3. Check Clerk docs: https://clerk.com/docs
4. Check Supabase docs: https://supabase.com/docs
5. Check Next.js docs: https://nextjs.org/docs
