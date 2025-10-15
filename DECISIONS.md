# Architecture Decision Records (ADRs)

This document captures key architectural decisions made during the transformation of BetterBros Props from Streamlit to a production-grade platform.

---

## Table of Contents

1. [Monorepo Structure](#1-monorepo-structure)
2. [Authentication Strategy](#2-authentication-strategy)
3. [Database Choice](#3-database-choice)
4. [Caching Layer](#4-caching-layer)
5. [Frontend Framework](#5-frontend-framework)
6. [Mobile Strategy](#6-mobile-strategy)
7. [ML Model Architecture](#7-ml-model-architecture)
8. [Correlation Modeling](#8-correlation-modeling)
9. [Optimization Approach](#9-optimization-approach)
10. [Deployment Strategy](#10-deployment-strategy)

---

## 1. Monorepo Structure

**Decision**: Use a pnpm workspace monorepo with clear separation of concerns.

**Context**: We needed to manage web, API, and mobile codebases with shared configuration and coordinated deployments.

**Rationale**:
- **Single source of truth** for dependencies and configuration
- **Shared types** between frontend and backend via TypeScript
- **Coordinated releases** across all platforms
- **Developer experience** improved with unified commands

**Structure**:
```
betterbros/
├── apps/
│   ├── web/          # Next.js 15 web application
│   └── api/          # FastAPI Python service
├── mobile/           # Expo React Native app
├── infra/            # Infrastructure configs (Docker, Fly.io, Vercel)
├── data/             # Data snapshots and models
├── exports/          # Generated exports
└── experiments/      # ML experiment tracking
```

**Alternatives Considered**:
- ❌ **Polyrepo**: More complex coordination, duplicate configs
- ❌ **Lerna**: More overhead than pnpm workspaces
- ❌ **Turborepo**: Overkill for 3 apps, adds complexity

**Status**: ✅ Accepted

---

## 2. Authentication Strategy

**Decision**: Support both Clerk (default) and Supabase with environment-based switching.

**Context**: Different users prefer different auth providers. Some want simplicity (Clerk), others want open-source and full control (Supabase).

**Rationale**:
- **Clerk Advantages**:
  - Best-in-class UX with pre-built components
  - Multiple OAuth providers out of the box
  - Excellent documentation and developer experience
  - Automatic session management

- **Supabase Advantages**:
  - Open source, self-hostable
  - Direct PostgreSQL integration with RLS
  - No per-user pricing
  - Full control over auth flow

**Implementation**:
```python
# Backend switching
AUTH_PROVIDER = os.getenv("AUTH_PROVIDER", "clerk")  # clerk or supabase

if AUTH_PROVIDER == "clerk":
    from src.auth.clerk import ClerkAuthProvider as AuthProvider
else:
    from src.auth.supabase import SupabaseAuthProvider as AuthProvider
```

**Alternatives Considered**:
- ❌ **Clerk only**: Locks users into commercial service
- ❌ **Supabase only**: Missing polished OAuth flows
- ❌ **Custom JWT**: Too much security work, reinventing wheel

**Status**: ✅ Accepted

---

## 3. Database Choice

**Decision**: Use Neon Postgres for production, PostgreSQL locally.

**Context**: Need serverless, auto-scaling database with branching for development.

**Rationale**:
- **Neon Advantages**:
  - Serverless with scale-to-zero (cost efficient)
  - Instant branching for development/staging
  - AWS-hosted with excellent uptime
  - Generous free tier
  - PostgreSQL compatibility (no vendor lock-in)

- **PostgreSQL**:
  - Industry standard for reliability
  - Excellent JSONB support for flexible schemas
  - Strong ecosystem and tooling
  - SQLAlchemy support with async

**Schema Design**:
- UUID primary keys for scalability
- JSONB for flexible metadata (config, metrics, correlations)
- Proper indexes on frequently queried fields
- Foreign keys with cascade rules
- Timestamps with timezone

**Alternatives Considered**:
- ❌ **MongoDB**: Schema flexibility not worth trade-off of no joins
- ❌ **Supabase Postgres**: Tied to Supabase ecosystem
- ❌ **PlanetScale**: MySQL limitations, no JSONB

**Status**: ✅ Accepted

---

## 4. Caching Layer

**Decision**: Use Upstash Redis with aggressive TTLs for expensive computations.

**Context**: ML predictions, correlation matrices, and feature engineering are CPU-intensive and benefit from caching.

**Rationale**:
- **Upstash Advantages**:
  - Serverless Redis with pay-per-request
  - Global replication with low latency
  - REST API for environments without Redis client
  - Generous free tier

**Caching Strategy**:
```
Props list:         30 min TTL (changes infrequently)
Features:           12 hour TTL (stable within day)
Model predictions:  1 hour TTL (confidence updates)
Correlation matrix: 1 hour TTL (expensive to compute)
Simulation samples: 30 min TTL (Monte Carlo results)
User snapshots:     24 hour TTL (historical data)
```

**Cache Keys**:
- Namespaced by entity: `props:week:8`, `features:snapshot:xyz`
- Includes relevant parameters: `corr:matrix:leg_ids:hash`
- Versioned for model updates: `pred:v2:player:123`

**Alternatives Considered**:
- ❌ **No caching**: Too slow, expensive recomputation
- ❌ **In-memory**: Lost on restart, doesn't scale horizontally
- ❌ **PostgreSQL caching**: Not designed for this use case

**Status**: ✅ Accepted

---

## 5. Frontend Framework

**Decision**: Use Next.js 15 with App Router, Tailwind CSS, and shadcn/ui.

**Context**: Need modern, performant web framework with server components and excellent DX.

**Rationale**:
- **Next.js 15 Advantages**:
  - React Server Components reduce bundle size
  - App Router provides file-based routing
  - Built-in image optimization
  - Excellent Vercel deployment integration
  - Server actions for mutations

- **Tailwind CSS**:
  - Utility-first approach speeds development
  - Small production bundle with PurgeCSS
  - Easy theming with CSS variables
  - Mobile-first responsive design

- **shadcn/ui**:
  - Copy-paste components (not npm package)
  - Full customization control
  - Radix UI primitives (accessibility)
  - Tailwind styling
  - sportsbook-style aesthetic achievable

**State Management**:
- **Server State**: TanStack Query (caching, invalidation)
- **Client State**: Zustand (lightweight, no boilerplate)
- **Form State**: React Hook Form (performance, validation)

**Alternatives Considered**:
- ❌ **React SPA**: No SSR, worse SEO, larger bundle
- ❌ **Vue/Nuxt**: Smaller ecosystem than React
- ❌ **Remix**: Less mature than Next.js

**Status**: ✅ Accepted

---

## 6. Mobile Strategy

**Decision**: Build Expo React Native app with offline-first architecture.

**Context**: Users want mobile access with offline support for reviewing props on the go.

**Rationale**:
- **Expo Advantages**:
  - Managed workflow (OTA updates without app store)
  - Expo Router for file-based routing
  - Pre-built modules (camera, notifications, etc.)
  - EAS Build for cloud builds
  - Web support (same codebase)

- **Offline-First**:
  - AsyncStorage for last snapshot
  - React Query with persistence plugin
  - NetInfo for network detection
  - Auto-refresh on app open if online

**Architecture**:
```
App Launch → Check Network → Cache Stale?
    ↓ Yes               ↓ No
Fetch Latest        Use Cached
    ↓
Save to AsyncStorage
    ↓
Render UI
```

**Alternatives Considered**:
- ❌ **Native iOS/Android**: Too expensive (2 codebases)
- ❌ **Flutter**: Team not familiar with Dart
- ❌ **PWA**: Limited native features, worse UX

**Status**: ✅ Accepted

---

## 7. ML Model Architecture

**Decision**: Use ensemble of gradient boosting (XGBoost/LightGBM) and Bayesian hierarchical models.

**Context**: Need accurate probability estimates with proper uncertainty quantification for betting decisions.

**Rationale**:
- **Gradient Boosting (60% weight)**:
  - Best accuracy on tabular data
  - Fast inference (< 50ms)
  - Feature importance via SHAP
  - Handles missing data well

- **Bayesian Hierarchical (40% weight)**:
  - Proper uncertainty quantification
  - Player-level and league-level effects
  - Principled handling of small samples
  - Credible intervals for confidence

- **Calibration Pipeline**:
  - Isotonic regression post-calibration
  - Rolling window recalibration (last 500 predictions)
  - ECE and Brier score monitoring
  - Alerts on degradation

**Ensemble Rationale**:
- Combines accuracy (GBM) with uncertainty (Bayes)
- Model disagreement increases uncertainty (robust)
- Learned weights adapt to data drift

**Output Schema**:
```python
{
    "p_hit": 0.65,           # Calibrated probability
    "sigma": 0.12,           # Uncertainty (std dev)
    "ci_low": 0.42,          # 95% CI lower
    "ci_high": 0.88,         # 95% CI upper
    "drivers": [             # SHAP feature attribution
        ("usage_rate", 0.12),
        ("opponent_rank", 0.08),
        ...
    ]
}
```

**Alternatives Considered**:
- ❌ **GBM only**: No uncertainty, overconfident
- ❌ **Bayesian only**: Slower, less accurate point estimates
- ❌ **Deep learning**: Overkill, needs more data, harder to interpret

**Status**: ✅ Accepted

---

## 8. Correlation Modeling

**Decision**: Use copulas for multivariate correlation with sport-specific adjustments.

**Context**: Parlays require modeling dependencies between prop outcomes for accurate EV calculation.

**Rationale**:
- **Copulas**:
  - Separate marginal distributions from dependence structure
  - Gaussian copula for normal-ish dependencies
  - t-copula for tail dependencies (extreme outcomes)
  - Efficient sampling for Monte Carlo

- **Sport-Specific Rules**:
  ```
  Same game:        +0.4 correlation boost
  Same player:      +0.6 (yards + TDs)
  Opposing players: -0.25 (QB vs defense)
  ```

- **Constraint Thresholds**:
  ```
  |ρ| < 0.35:  ✅ OK (green)
  0.35 ≤ |ρ| < 0.75:  ⚠️ WARNING (yellow, soft penalty)
  |ρ| ≥ 0.75:  ❌ BLOCK (red, hard constraint)
  ```

**Implementation**:
1. Empirical Spearman correlation from residuals
2. Apply sport-specific adjustments
3. Fit copula to correlation matrix
4. Sample 10k correlated outcomes for Monte Carlo

**Alternatives Considered**:
- ❌ **Independence assumption**: Underestimates risk, wrong EVs
- ❌ **Multivariate Gaussian**: Misses tail dependencies
- ❌ **Vine copulas**: Overkill, too complex

**Status**: ✅ Accepted

---

## 9. Optimization Approach

**Decision**: Use greedy + beam search optimization with correlation penalties and diversity bonuses.

**Context**: Need to find high-EV parlays quickly while respecting correlation and diversity constraints.

**Objective Function**:
```
maximize: EV - λ * Σ|ρ_ij| + μ * DiversityScore

where:
  EV = Expected Value from Monte Carlo simulation
  λ = Correlation penalty (0.05-0.30 by risk mode)
  ρ_ij = Pairwise correlations
  μ = Diversity bonus weight (0.05)
  DiversityScore = unique_games / total_legs
```

**Rationale**:
- **Greedy Algorithm**:
  - Fast (< 0.2s for 200 candidates)
  - 85-95% of optimal
  - Good enough for real-time UI

- **Beam Search**:
  - Moderate speed (< 1.5s)
  - 90-97% of optimal
  - Better exploration of solution space

- **Correlation Penalty**:
  - Soft constraint via objective function
  - Prevents over-correlated parlays
  - Tunable by risk mode

- **Diversity Bonus**:
  - Encourages multi-game parlays
  - Reduces single-game risk
  - Better user experience

**Risk Modes**:
```
Conservative: λ=0.30, min_ev=0.15, max_legs=4
Moderate:     λ=0.15, min_ev=0.10, max_legs=6
Aggressive:   λ=0.05, min_ev=0.05, max_legs=8
```

**Kelly Sizing**:
- Fractional Kelly (1/4 by default)
- Clamps: $5 min, $50 max per slip
- Multi-bet portfolio allocation

**Alternatives Considered**:
- ❌ **Genetic algorithm**: Too slow (8s), marginal improvement
- ❌ **Exhaustive search**: Exponential complexity
- ❌ **Integer programming**: Setup overhead, limited solver availability

**Status**: ✅ Accepted

---

## 10. Deployment Strategy

**Decision**: Deploy web to Vercel, API to Fly.io, use Neon + Upstash for data layer.

**Context**: Need cost-effective, scalable deployment with CI/CD and monitoring.

**Rationale**:
- **Vercel for Next.js**:
  - Best Next.js hosting (same company)
  - Automatic deployments from Git
  - Edge network (low latency)
  - Free hobby tier generous
  - Preview deployments for PRs

- **Fly.io for FastAPI**:
  - Global edge deployment
  - Automatic health checks
  - Zero-downtime deployments
  - Reasonable pricing (scale-to-zero)
  - Docker-based (portable)

- **Neon Postgres**:
  - Serverless with branching
  - Scale-to-zero (cost savings)
  - Instant copies for staging

- **Upstash Redis**:
  - Serverless with per-request pricing
  - Global replication
  - REST API fallback

**CI/CD**:
- GitHub Actions for testing
- Automatic deployments on merge to main
- Preview environments for PRs
- Alembic migrations on deploy

**Monitoring**:
- Vercel Analytics for web
- Fly.io logs and metrics for API
- Neon query insights
- Upstash Redis metrics

**Alternatives Considered**:
- ❌ **AWS ECS**: Too complex, higher ops burden
- ❌ **Heroku**: More expensive, less flexible
- ❌ **Railway**: Less mature than Fly.io

**Status**: ✅ Accepted

---

## Summary of Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Repo Structure** | pnpm monorepo | Shared config, coordinated deploys |
| **Auth** | Clerk (default) + Supabase (option) | Flexibility, best UX + open-source |
| **Database** | Neon Postgres | Serverless, branching, PostgreSQL |
| **Cache** | Upstash Redis | Serverless, global, pay-per-request |
| **Web Framework** | Next.js 15 + Tailwind | Modern, performant, excellent DX |
| **Mobile** | Expo + offline-first | Cross-platform, managed, OTA updates |
| **ML Models** | Ensemble (GBM + Bayes) | Accuracy + uncertainty, calibrated |
| **Correlation** | Copulas + sport rules | Proper dependencies, Monte Carlo |
| **Optimization** | Greedy + beam search | Fast, good solutions, constraint handling |
| **Deployment** | Vercel + Fly.io + Neon + Upstash | Scalable, cost-effective, low ops |

---

## Decision Review Process

These decisions should be reviewed:
- **Quarterly**: Check if assumptions still hold
- **On issues**: If problems arise, revisit decision
- **New features**: Ensure new features align with decisions

To propose changes, open a GitHub issue with:
1. Problem statement
2. Current decision recap
3. Proposed alternative
4. Trade-offs analysis

---

**Maintained by**: BetterBros Engineering Team
**Last reviewed**: 2025-01-14
