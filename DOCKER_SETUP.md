# Docker Setup Guide for BetterBros

## Quick Start (After Installing Docker Desktop)

### Option 1: Backend Services Only (Recommended for Development)

**Use this when running Next.js locally with `pnpm dev`**

```bash
cd "/Users/joshuadeleon/BetterBros Bets/infra"
docker-compose -f docker-compose.backend.yml up
```

This starts:
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ FastAPI API (port 8000)

Your local Next.js app (port 3001) will connect to these services.

### Option 2: Full Stack (API + Web in Docker)

**Use this to run everything in containers**

```bash
cd "/Users/joshuadeleon/BetterBros Bets/infra"
docker-compose up
```

This starts:
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ FastAPI API (port 8000)
- ✅ Next.js Web (port 3000)

---

## Installation Steps

### 1. Install Docker Desktop for Mac (Apple Silicon)

**Download:**
- Visit: https://www.docker.com/products/docker-desktop
- Click "Download for Mac - Apple Chip"
- Or direct: https://desktop.docker.com/mac/main/arm64/Docker.dmg

**Install:**
1. Open `Docker.dmg`
2. Drag Docker to Applications
3. Launch Docker from Applications
4. Accept service agreement
5. Wait for whale icon to appear in menu bar (steady = ready)

### 2. Verify Installation

```bash
docker --version
# Should show: Docker version 24.x.x

docker ps
# Should show empty list (no errors)
```

### 3. Start Backend Services

```bash
cd "/Users/joshuadeleon/BetterBros Bets/infra"
docker-compose -f docker-compose.backend.yml up
```

**First run will:**
- Download PostgreSQL image (~80MB)
- Download Redis image (~30MB)
- Build FastAPI image (~300MB)
- Takes 3-5 minutes on first run

**Subsequent runs:**
- Start in 10-30 seconds
- Uses cached images

### 4. Verify Services Are Running

**Check containers:**
```bash
docker ps
```

Should show:
```
CONTAINER ID   IMAGE                    STATUS         PORTS
xxxxx          betterbros-api           Up 2 minutes   0.0.0.0:8000->8000/tcp
xxxxx          redis:7-alpine           Up 2 minutes   0.0.0.0:6379->6379/tcp
xxxxx          postgres:16-alpine       Up 2 minutes   0.0.0.0:5432->5432/tcp
```

**Test API:**
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

**Visit API docs:**
- Open browser: http://localhost:8000/docs
- You'll see the FastAPI interactive documentation

### 5. Update Next.js to Use Local API

Your Next.js app should already be configured via `.env.local`:
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

Restart your Next.js dev server if it's running:
```bash
# In a new terminal
cd "/Users/joshuadeleon/BetterBros Bets/apps/web"
pnpm dev
```

Now visit http://localhost:3001 - your app will have live data!

---

## Common Commands

### Start services (foreground - see logs)
```bash
docker-compose -f docker-compose.backend.yml up
```

### Start services (background - detached)
```bash
docker-compose -f docker-compose.backend.yml up -d
```

### View logs
```bash
docker-compose -f docker-compose.backend.yml logs -f
```

### Stop services
```bash
docker-compose -f docker-compose.backend.yml down
```

### Stop and remove data volumes (fresh start)
```bash
docker-compose -f docker-compose.backend.yml down -v
```

### Rebuild API after code changes
```bash
docker-compose -f docker-compose.backend.yml up --build api
```

---

## Troubleshooting

### "Cannot connect to Docker daemon"
**Solution:** Make sure Docker Desktop is running (whale icon in menu bar)

### "Port 5432 already in use"
**Solution:** You have PostgreSQL running locally
```bash
# Stop local PostgreSQL
brew services stop postgresql@16
# Or use different port in docker-compose.yml
```

### "Port 8000 already in use"
**Solution:** Another process is using port 8000
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill
```

### API container keeps restarting
**Solution:** Check logs
```bash
docker logs betterbros-api
```

Common issues:
- Missing Python dependencies (rebuild: `docker-compose up --build`)
- Database not ready (wait 10 seconds and retry)
- Environment variables not set (check .env files)

### Can't access API from Next.js
**Solution:**
1. Verify API is running: `curl http://localhost:8000/health`
2. Check Next.js `.env.local` has: `NEXT_PUBLIC_API_BASE=http://localhost:8000`
3. Restart Next.js dev server

---

## What's Running Where

```
┌─────────────────────────────────────────────────────────┐
│                    Your Mac (Host)                      │
│                                                         │
│  ┌──────────────┐          ┌────────────────────────┐  │
│  │  Next.js     │  API     │   Docker Containers     │  │
│  │  localhost:  │ ────────>│                        │  │
│  │  3001        │  calls   │  ┌──────────────────┐  │  │
│  └──────────────┘          │  │  FastAPI API     │  │  │
│                            │  │  :8000           │  │  │
│  ┌──────────────┐          │  └────────┬─────────┘  │  │
│  │  Browser     │          │           │            │  │
│  │              │          │     ┌─────▼──────┐     │  │
│  │  View at:    │          │     │ PostgreSQL │     │  │
│  │  localhost:  │          │     │ :5432      │     │  │
│  │  3001        │          │     └────────────┘     │  │
│  └──────────────┘          │                        │  │
│                            │     ┌────────────┐     │  │
│                            │     │   Redis    │     │  │
│                            │     │   :6379    │     │  │
│                            │     └────────────┘     │  │
│                            └────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Next Steps After Setup

1. **Database Migration** - Create tables
   ```bash
   docker exec -it betterbros-api python -m alembic upgrade head
   ```

2. **Seed Sample Data** - Add test props
   ```bash
   docker exec -it betterbros-api python scripts/seed_data.py
   ```

3. **Test API Endpoints**
   - Visit http://localhost:8000/docs
   - Try `/api/props` endpoint
   - Check `/api/health` endpoint

4. **View in Browser**
   - Open http://localhost:3001
   - You should see props data in the dashboard
   - Try adding props to your slip
   - Test the optimization features

---

## Environment Variables

The API needs these environment variables (already configured in docker-compose):

**Required:**
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `AUTH_PROVIDER` - Authentication provider

**Optional (for live data):**
- `ODDS_API_KEY` - The Odds API key
- `SPORTGAMEODDS_API_KEY` - SportsGameOdds key
- `SLEEPER_API_KEY` - Sleeper API key
- `OPENWEATHER_KEY` - Weather data key

Add these to `/Users/joshuadeleon/BetterBros Bets/apps/api/.env`

---

## Performance Tips

**Speed up builds:**
- Docker Desktop settings → Resources → Increase CPU/Memory
- Recommended: 4 CPUs, 8GB RAM

**Reduce Docker image size:**
- Images are already optimized (Alpine Linux)
- Total size: ~400MB

**Hot reload:**
- Code changes in `apps/api/` auto-reload API
- No need to rebuild container

---

## When to Use Each Option

### Backend-only (docker-compose.backend.yml)
**Use when:**
- Developing frontend (Next.js)
- Need fast hot reload on web
- Want to see Next.js logs easily
- Debugging web components

### Full stack (docker-compose.yml)
**Use when:**
- Testing production-like setup
- Deploying to staging
- Need everything isolated
- Sharing environment with team

---

**Need help?** Check logs with:
```bash
docker-compose -f docker-compose.backend.yml logs -f
```
