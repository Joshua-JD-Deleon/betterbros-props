# BetterBros Props - Development & Deployment Guide

> **Transform your Streamlit prototype into a production-grade, sportsbook-style betting platform**

This guide provides complete instructions for running the BetterBros Props platform locally and deploying to production.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [Running the Services](#running-the-services)
5. [Deployment](#deployment)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     BetterBros Props Platform                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Next.js 15 │  │  FastAPI     │  │  Expo Mobile │       │
│  │  Web App    │  │  API Service │  │  React Native│       │
│  │  (Vercel)   │  │  (Fly.io)    │  │              │       │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                  │               │
│         └─────────────────┼──────────────────┘               │
│                           │                                  │
│                  ┌────────▼─────────┐                        │
│                  │  Auth (Clerk or  │                        │
│                  │  Supabase)       │                        │
│                  └────────┬─────────┘                        │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐               │
│         │                 │                 │               │
│  ┌──────▼──────┐   ┌─────▼─────┐   ┌──────▼──────┐        │
│  │  Neon       │   │   Upstash  │   │  Data APIs  │        │
│  │  Postgres   │   │   Redis    │   │  (External) │        │
│  │             │   │            │   │             │        │
│  └─────────────┘   └────────────┘   └─────────────┘        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

**Frontend (Web)**
- Next.js 15 (App Router)
- React 18, TypeScript
- Tailwind CSS + shadcn/ui
- TanStack Query + Zustand
- Clerk or Supabase Auth

**Backend (API)**
- FastAPI (Python 3.11+)
- SQLAlchemy (Async)
- Redis caching
- XGBoost, LightGBM, PyMC
- Copulas, SHAP

**Mobile**
- Expo 50
- React Native 0.73
- Expo Router
- Offline-first architecture

**Infrastructure**
- Database: Neon Postgres
- Cache: Upstash Redis
- Web Hosting: Vercel
- API Hosting: Fly.io

---

## Prerequisites

### Required Software

- **Node.js** 18+ and **pnpm** 8+
- **Python** 3.11+
- **Docker** and **Docker Compose** (for local services)
- **Git**

### Optional but Recommended

- **PostgreSQL** 16+ (or use Docker)
- **Redis** 7+ (or use Docker)
- **Expo CLI** (for mobile development)

### API Keys Needed

- **The Odds API**: [https://the-odds-api.com](https://the-odds-api.com) (500 free requests/month)
- **OpenWeather API**: [https://openweathermap.org/api](https://openweathermap.org/api) (free tier available)
- **Clerk** (default auth): [https://clerk.com](https://clerk.com) OR
- **Supabase** (alternative auth): [https://supabase.com](https://supabase.com)

---

## Local Development Setup

### 1. Clone and Navigate

```bash
cd "/Users/joshuadeleon/BetterBros Bets"
```

### 2. Install Dependencies

#### Root and Web App
```bash
# Install root dependencies and web app
pnpm install
```

#### API Service
```bash
cd apps/api
pip install -r requirements.txt
cd ../..
```

#### Mobile App (optional)
```bash
cd mobile
npm install
cd ..
```

### 3. Configure Environment Variables

#### Copy Example Files
```bash
cp .env.example .env
cp apps/web/.env.example apps/web/.env.local
cp apps/api/.env.example apps/api/.env
cp mobile/.env.example mobile/.env
```

#### Edit Configuration Files

**Root `.env`** (shared configuration):
```bash
# Auth Provider (clerk or supabase)
AUTH_PROVIDER=clerk

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/betterbros

# Redis
REDIS_URL=redis://localhost:6379

# API Keys
ODDS_API_KEY=your_odds_api_key
SLEEPER_API_KEY=
OPENWEATHER_KEY=your_openweather_key
SPORTGAMEODDS_API_KEY=

# API Base URL
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

**apps/web/.env.local** (Next.js specific):
```bash
# Clerk (default)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# OR Supabase (alternative)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
```

**apps/api/.env** (FastAPI specific):
```bash
# Use same values as root .env
# Plus any API-specific overrides
```

### 4. Start Local Services with Docker

```bash
cd infra
docker-compose up -d postgres redis
cd ..
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379

### 5. Initialize Database

```bash
cd apps/api
python scripts/db_migrate.py init
cd ../..
```

---

## Running the Services

### Option A: Run All Services (Recommended for Development)

#### Terminal 1: FastAPI Backend
```bash
cd apps/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at:
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

#### Terminal 2: Next.js Web App
```bash
cd apps/web
pnpm dev
```

Web app available at: http://localhost:3000

#### Terminal 3: Mobile App (optional)
```bash
cd mobile
npm start
```

Then press:
- `i` for iOS Simulator
- `a` for Android Emulator
- Scan QR code with Expo Go app on device

### Option B: Use Docker Compose (Full Stack)

```bash
cd infra
docker-compose up
```

This starts all services:
- Web app on http://localhost:3000
- API on http://localhost:8000
- PostgreSQL on port 5432
- Redis on port 6379

---

## Deployment

### Deploy FastAPI to Fly.io

#### 1. Install Fly CLI
```bash
curl -L https://fly.io/install.sh | sh
```

#### 2. Login and Create App
```bash
fly auth login
fly launch --config infra/fly.toml
```

#### 3. Set Secrets
```bash
fly secrets set \
  DATABASE_URL="postgresql://user:pass@host:5432/db?sslmode=require" \
  REDIS_URL="rediss://:token@upstash-host:6379" \
  ODDS_API_KEY="your_key" \
  OPENWEATHER_KEY="your_key" \
  CLERK_SECRET_KEY="your_key"
```

#### 4. Deploy
```bash
fly deploy --config infra/fly.toml
```

Your API will be at: `https://your-app.fly.dev`

### Deploy Next.js to Vercel

#### 1. Install Vercel CLI
```bash
npm i -g vercel
```

#### 2. Link Project
```bash
cd apps/web
vercel link
```

#### 3. Set Environment Variables

In Vercel Dashboard → Project Settings → Environment Variables:
```
NEXT_PUBLIC_API_BASE=https://your-app.fly.dev
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
CLERK_SECRET_KEY=sk_live_...
```

#### 4. Deploy
```bash
vercel --prod
```

### Set Up Production Database (Neon)

1. Go to [https://neon.tech](https://neon.tech)
2. Create new project
3. Copy connection string
4. Update `DATABASE_URL` in Fly.io secrets and Vercel env vars

### Set Up Production Redis (Upstash)

1. Go to [https://upstash.com](https://upstash.com)
2. Create Redis database
3. Copy connection string
4. Update `REDIS_URL` in Fly.io secrets and Vercel env vars

---

## Configuration

### Authentication Provider Switching

To switch between Clerk and Supabase:

1. Update `.env`:
```bash
AUTH_PROVIDER=supabase  # or clerk
```

2. Update environment variables for the chosen provider

3. Restart services - no code changes needed!

### Risk Modes

Adjust optimizer behavior in API requests:

- **Conservative**: Lower risk, higher confidence (min_ev=0.15, max_legs=4)
- **Moderate**: Balanced approach (min_ev=0.10, max_legs=6)
- **Aggressive**: Higher risk, more opportunities (min_ev=0.05, max_legs=8)

### Feature Flags

Enable/disable features via environment variables:

```bash
ENABLE_MOBILE_OFFLINE=true
ENABLE_WHAT_IF_SANDBOX=true
ENABLE_CORRELATION_INSPECTOR=true
ENABLE_CALIBRATION_MONITOR=true
ENABLE_EXPERIMENT_TRACKING=true
```

---

## Testing

### Backend Tests

```bash
cd apps/api
pytest tests/ -v
```

### Frontend Tests

```bash
cd apps/web
pnpm test
```

### E2E Smoke Test

```bash
# Start all services, then:
curl http://localhost:8000/health
curl http://localhost:3000
```

Expected responses:
- API: `{"status": "healthy", "database": "connected", "redis": "connected"}`
- Web: HTML page loads

---

## Troubleshooting

### Database Connection Errors

**Problem**: `could not connect to server`

**Solution**:
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Restart if needed
cd infra && docker-compose restart postgres
```

### Redis Connection Errors

**Problem**: `Connection refused to Redis`

**Solution**:
```bash
# Check if Redis is running
docker ps | grep redis

# Restart if needed
cd infra && docker-compose restart redis
```

### Port Already in Use

**Problem**: `Address already in use` on port 3000 or 8000

**Solution**:
```bash
# Find process using port
lsof -ti:3000  # or :8000

# Kill process
kill -9 $(lsof -ti:3000)
```

### Module Import Errors (Python)

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
# Ensure you're running from apps/api/ directory
cd apps/api
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn main:app --reload
```

### Mobile App Build Errors

**Problem**: Expo build fails

**Solution**:
```bash
cd mobile
rm -rf node_modules
npm install
npm start -- --clear
```

### Authentication Errors

**Problem**: `401 Unauthorized` or JWT verification fails

**Solution**:
1. Check `AUTH_PROVIDER` matches your setup (clerk/supabase)
2. Verify API keys are correct
3. Ensure tokens haven't expired
4. Check middleware is configured in `middleware.ts`

### Slow API Responses

**Problem**: API endpoints taking > 5 seconds

**Solution**:
1. Check Redis connection - caching may be disabled
2. Monitor with `/health` endpoint
3. Check database query performance
4. Verify external API keys are valid (Sleeper, OpenWeather)

---

## Quick Command Reference

```bash
# Development
pnpm dev                          # Start Next.js
uvicorn main:app --reload         # Start FastAPI
npm start                         # Start Expo

# Database
python scripts/db_migrate.py init        # Initialize DB
python scripts/db_migrate.py upgrade     # Run migrations
python scripts/db_migrate.py reset       # Reset DB (careful!)

# Docker
docker-compose up -d              # Start services
docker-compose down               # Stop services
docker-compose logs -f api        # View logs

# Deployment
fly deploy                        # Deploy API
vercel --prod                     # Deploy Web

# Testing
pytest tests/ -v                  # Backend tests
pnpm test                         # Frontend tests
```

---

## Additional Resources

- **Architecture Decisions**: See `DECISIONS.md`
- **API Documentation**: http://localhost:8000/docs (when running)
- **Component Documentation**: `apps/web/README.md`
- **Mobile App Guide**: `mobile/README.md`
- **Database Schema**: `apps/api/DATABASE.md`
- **Feature Engineering**: `apps/api/src/features/README.md`
- **ML Models**: `apps/api/src/models/README.md`

---

## Support

For issues and questions:
1. Check existing documentation in component directories
2. Review GitHub issues: https://github.com/Joshua-JD-Deleon/betterbros-props
3. Check logs: `docker-compose logs -f` or `fly logs`

---

**Built with** ❤️ **by the BetterBros team**

*Last updated: 2025-01-14*
