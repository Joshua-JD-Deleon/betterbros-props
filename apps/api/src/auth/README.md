# Authentication System

Comprehensive authentication system with environment-based switching between **Clerk** and **Supabase**.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Frontend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Clerk UI   │  │  Supabase    │  │   Unified    │         │
│  │  Components  │  │  Auth Client │  │  Auth Module │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                   │                  │                 │
│         └───────────────────┴──────────────────┘                │
│                            │                                     │
│                  ┌─────────▼─────────┐                         │
│                  │   middleware.ts   │                         │
│                  │  (Route Protection)│                        │
│                  └─────────┬─────────┘                         │
└────────────────────────────┼─────────────────────────────────┘
                             │ JWT Token
                   ┌─────────▼─────────┐
                   │   API Gateway     │
                   │  FastAPI Backend  │
                   └─────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
     ┌──────▼──────┐  ┌──────▼──────┐  ┌────▼─────┐
     │   Clerk     │  │  Supabase   │  │  deps.py │
     │  Provider   │  │  Provider   │  │(Switcher)│
     └──────┬──────┘  └──────┬──────┘  └────┬─────┘
            │                │                │
            └────────────────┴────────────────┘
                             │
                      ┌──────▼──────┐
                      │  PostgreSQL │
                      │    Users    │
                      └─────────────┘
```

## Components

### Backend (FastAPI)

#### 1. Auth Providers (`src/auth/`)

**Clerk Provider** (`clerk.py`):
- JWT verification using JWKS (JSON Web Key Set)
- Fetches public keys from `https://api.clerk.com/v1/jwks`
- Validates RS256 signatures
- Extracts user info from token claims

**Supabase Provider** (`supabase.py`):
- JWT verification using symmetric secret (HS256)
- Validates against `SUPABASE_JWT_SECRET`
- Extracts user info from token claims
- Supports Supabase-specific audience validation

#### 2. Authentication Dependencies (`deps.py`)

Main Functions:
- `get_current_user()`: Validates JWT, fetches/creates user in DB
- `get_current_active_user()`: Ensures user is active
- `require_subscription_tier()`: Enforces subscription tiers
- `require_pro_tier()`: Shortcut for pro/enterprise access
- `require_enterprise_tier()`: Shortcut for enterprise access

Environment Switching:
```python
if settings.AUTH_PROVIDER == "clerk":
    provider = get_clerk_provider()
    # Clerk-specific verification
elif settings.AUTH_PROVIDER == "supabase":
    provider = get_supabase_provider()
    # Supabase-specific verification
```

Database Integration:
- Automatically creates user on first authentication
- Stores provider-specific IDs (clerk_user_id or supabase_user_id)
- Tracks subscription tier, status, and metadata
- Updates last_login_at on each request

#### 3. Database Models (`src/db/models.py`)

**User Model**:
```python
class User(Base):
    id: UUID  # Internal UUID
    clerk_user_id: Optional[str]  # Clerk ID if using Clerk
    supabase_user_id: Optional[UUID]  # Supabase ID if using Supabase
    email: str
    full_name: Optional[str]
    subscription_tier: str  # free, pro, enterprise
    subscription_status: str  # active, cancelled, past_due
    is_active: bool
    is_verified: bool
    user_metadata: JSONB
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
```

### Frontend (Next.js)

#### 1. Clerk Integration (`src/lib/auth/clerk.ts`)

Server Functions:
- `getCurrentUser()`: Get Clerk user from server
- `getAuthToken()`: Get JWT token
- `getUserMetadata()`: Extract user metadata
- `getSubscriptionTier()`: Get subscription from metadata
- `fetchWithAuth()`: Make authenticated API requests

#### 2. Supabase Integration (`src/lib/auth/supabase.ts`)

Client Functions:
- `authClient.signIn()`: Email/password sign in
- `authClient.signUp()`: Email/password sign up
- `authClient.signOut()`: Sign out user
- `authClient.getSession()`: Get current session
- `authClient.getUser()`: Get current user

Services:
- `UserProfileService`: Manage user profiles
- `BetTrackingService`: Track user bets
- `rlsHelpers`: Row-level security helpers

#### 3. Unified Auth Module (`src/lib/auth/index.ts`)

Provider-agnostic interface:
```typescript
import { isAuthenticated, getAuthToken, apiRequest } from '@/lib/auth';

// Works with both Clerk and Supabase
const isAuth = await isAuthenticated();
const token = await getAuthToken();
const data = await apiRequest('/api/endpoint');
```

#### 4. Middleware (`middleware.ts`)

Environment-based routing protection:
- Clerk: Uses `clerkMiddleware()` with route matchers
- Supabase: Custom middleware checking session cookies
- Protects `/dashboard`, `/props`, `/optimize`, etc.
- Allows public routes: `/`, `/sign-in`, `/sign-up`, etc.

## Authentication Flows

### Clerk Flow

1. **Sign In/Up**:
   ```
   User → Clerk UI Component → Clerk API → JWT Token → Browser
   ```

2. **Authenticated Request**:
   ```
   Browser → Next.js (middleware checks session)
          → API Request with JWT in Authorization header
          → FastAPI validates JWT using JWKS
          → Queries/creates user in PostgreSQL
          → Returns user profile
   ```

3. **Token Validation**:
   ```python
   # Backend (FastAPI)
   token = credentials.credentials
   provider = get_clerk_provider()
   user_info = await provider.get_user_info(token)
   # Creates signing key client with JWKS URL
   # Verifies RS256 signature
   # Extracts user_id, email, name
   ```

### Supabase Flow

1. **Sign In/Up**:
   ```
   User → Supabase Auth Client → Supabase API → JWT Token → LocalStorage
   ```

2. **Authenticated Request**:
   ```
   Browser → Next.js (middleware checks sb-access-token cookie)
          → API Request with JWT in Authorization header
          → FastAPI validates JWT using JWT_SECRET
          → Queries/creates user in PostgreSQL
          → Returns user profile
   ```

3. **Token Validation**:
   ```python
   # Backend (FastAPI)
   token = credentials.credentials
   provider = get_supabase_provider()
   user_info = await provider.get_user_info(token)
   # Verifies HS256 signature with JWT_SECRET
   # Validates issuer and audience
   # Extracts user_id, email, metadata
   ```

## Environment Configuration

### Backend (.env)

```bash
# Required
AUTH_PROVIDER=clerk  # or supabase

# Clerk Configuration (if using Clerk)
CLERK_SECRET_KEY=sk_live_xxxxx
CLERK_JWT_ISSUER=https://clerk.your-domain.com  # Optional

# Supabase Configuration (if using Supabase)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
```

### Frontend (.env.local)

```bash
# Required
NEXT_PUBLIC_AUTH_PROVIDER=clerk  # or supabase

# Clerk Configuration (if using Clerk)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxxxx
CLERK_SECRET_KEY=sk_live_xxxxx
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/dashboard
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/dashboard

# Supabase Configuration (if using Supabase)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...

# API Configuration
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## Subscription Tiers

### Tier Hierarchy

```
Free < Pro < Enterprise
```

### Usage in Endpoints

```python
from fastapi import Depends
from src.auth.deps import require_pro_tier, get_current_active_user

@router.get("/premium-feature")
async def premium_feature(
    user: UserProfile = Depends(require_pro_tier)
):
    # Only accessible to Pro and Enterprise users
    return {"message": "Premium content"}

# Alternative: Using dependency directly
@router.get("/enterprise-feature")
async def enterprise_feature(
    user: UserProfile = Depends(require_enterprise_tier)
):
    # Only accessible to Enterprise users
    return {"message": "Enterprise content"}

# Or check tier manually
@router.get("/check-tier")
async def check_tier(user: UserProfile = Depends(get_current_active_user)):
    if user.subscription_tier in ["pro", "enterprise"]:
        return {"access": "granted"}
    raise HTTPException(403, "Pro subscription required")
```

## Security Features

### JWT Verification

**Clerk** (Asymmetric):
- RS256 algorithm
- Public key from JWKS endpoint
- Automatic key rotation support
- Caches signing keys (1 hour TTL)

**Supabase** (Symmetric):
- HS256 algorithm
- Shared secret (JWT_SECRET)
- Validates issuer and audience
- Checks expiration

### Token Handling

1. **Expiration**: Both providers check `exp` claim
2. **Issuer Validation**: Verifies token came from expected provider
3. **Signature Verification**: Cryptographic validation
4. **Audience Check**: Ensures token is for our API

### Database Security

- UUIDs for primary keys (not sequential)
- Separate auth provider IDs from internal IDs
- Row-level security (RLS) ready for Supabase
- Encrypted sensitive fields (future: API keys)

## Error Handling

### Common Errors

1. **401 Unauthorized**:
   - Invalid token
   - Expired token
   - Missing Authorization header

2. **403 Forbidden**:
   - Inactive user account
   - Insufficient subscription tier

3. **500 Internal Server Error**:
   - Invalid AUTH_PROVIDER configuration
   - Database connection issues

### Error Responses

```json
{
  "detail": "Token has expired",
  "headers": {
    "WWW-Authenticate": "Bearer"
  }
}
```

## Testing

### Backend Tests

```python
# Test Clerk authentication
async def test_clerk_auth():
    token = "eyJxxx..."  # Valid Clerk JWT
    provider = get_clerk_provider()
    user_info = await provider.get_user_info(token)
    assert user_info["user_id"]

# Test Supabase authentication
async def test_supabase_auth():
    token = "eyJxxx..."  # Valid Supabase JWT
    provider = get_supabase_provider()
    user_info = await provider.get_user_info(token)
    assert user_info["user_id"]

# Test subscription tier enforcement
async def test_subscription_tier():
    user = UserProfile(subscription_tier="free")
    with pytest.raises(HTTPException):
        await require_subscription_tier("pro", user)
```

### Frontend Tests

```typescript
// Test unified auth module
import { getAuthToken, isAuthenticated } from '@/lib/auth';

test('gets auth token', async () => {
  const token = await getAuthToken();
  expect(token).toBeTruthy();
});

test('checks authentication', async () => {
  const isAuth = await isAuthenticated();
  expect(isAuth).toBe(true);
});
```

## Migration Guide

### Switching Providers

1. **Update Environment Variables**:
   ```bash
   # Change from Clerk to Supabase
   AUTH_PROVIDER=supabase
   NEXT_PUBLIC_AUTH_PROVIDER=supabase
   ```

2. **No Code Changes Required**:
   - Backend automatically switches providers
   - Frontend uses unified auth module
   - Middleware adapts to new provider

3. **Database Considerations**:
   - Existing users keep their provider-specific IDs
   - Can support both providers simultaneously
   - User identified by either clerk_user_id or supabase_user_id

## Best Practices

1. **Token Storage**:
   - Never store tokens in localStorage (XSS risk)
   - Use httpOnly cookies when possible
   - Short-lived access tokens (< 1 hour)

2. **API Requests**:
   - Always include Authorization header
   - Use apiRequest() helper for consistency
   - Handle 401/403 errors gracefully

3. **Subscription Checks**:
   - Use dependency injection for tier enforcement
   - Check tiers at API level, not just UI
   - Cache subscription status with short TTL

4. **Error Handling**:
   - Log authentication failures
   - Don't expose sensitive error details to clients
   - Return generic "unauthorized" messages

## Troubleshooting

### Token Verification Fails

1. Check AUTH_PROVIDER matches between frontend/backend
2. Verify JWT secret/JWKS URL is correct
3. Check token hasn't expired
4. Ensure issuer matches expected value

### User Not Created in Database

1. Check database connection
2. Verify unique constraints (email must be unique)
3. Check auth provider ID field is set correctly
4. Review database logs for constraint violations

### Middleware Not Protecting Routes

1. Verify AUTH_PROVIDER environment variable is set
2. Check route patterns match your actual routes
3. Test with protected route (e.g., /dashboard)
4. Review middleware logs

## Future Enhancements

- [ ] API key authentication for M2M
- [ ] Multi-factor authentication (MFA)
- [ ] Session management with Redis
- [ ] OAuth provider support (Google, GitHub)
- [ ] Webhook handlers for auth events
- [ ] Rate limiting per user
- [ ] Audit logging for auth events
