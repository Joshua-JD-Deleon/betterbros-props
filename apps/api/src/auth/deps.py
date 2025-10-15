"""
Authentication dependencies for FastAPI endpoints

Provides environment-based authentication switching between Clerk and Supabase.
Integrates with database to fetch/create user profiles.
Implements subscription tier enforcement.
"""
import logging
from typing import Optional, Callable
from datetime import datetime
from functools import wraps
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.config import settings
from src.types import UserProfile
from src.db import get_db
from src.db.models import User
from src.auth.clerk import get_clerk_provider
from src.auth.supabase import get_supabase_provider

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """
    Validate JWT token and return current user profile.
    Switches between Clerk and Supabase based on AUTH_PROVIDER setting.
    Creates user in database if not exists.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        UserProfile with user information and subscription tier

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    try:
        # Verify token and extract user info based on provider
        if settings.AUTH_PROVIDER == "clerk":
            provider = get_clerk_provider()
            user_info = await provider.get_user_info(token)
            auth_user_id = user_info["user_id"]
            auth_field = "clerk_user_id"

        elif settings.AUTH_PROVIDER == "supabase":
            provider = get_supabase_provider()
            user_info = await provider.get_user_info(token)
            auth_user_id = user_info["user_id"]
            auth_field = "supabase_user_id"

        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid auth provider: {settings.AUTH_PROVIDER}",
            )

        # Query database for user
        query = select(User).where(
            getattr(User, auth_field) == auth_user_id
        )
        result = await db.execute(query)
        db_user = result.scalar_one_or_none()

        # Create user if doesn't exist
        if not db_user:
            logger.info(f"Creating new user in database: {auth_user_id}")
            db_user = await _create_user_from_auth_info(
                db=db,
                auth_field=auth_field,
                auth_user_id=auth_user_id,
                user_info=user_info,
            )

        # Update last login timestamp
        db_user.last_login_at = datetime.utcnow()
        await db.commit()

        # Build UserProfile response
        return UserProfile(
            user_id=str(db_user.id),
            email=db_user.email,
            name=db_user.full_name,
            subscription_tier=db_user.subscription_tier,
            is_active=db_user.is_active,
            created_at=db_user.created_at,
            last_login_at=db_user.last_login_at,
        )

    except ValueError as e:
        # Token verification failed
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating token: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def _create_user_from_auth_info(
    db: AsyncSession,
    auth_field: str,
    auth_user_id: str,
    user_info: dict,
) -> User:
    """
    Create a new user in the database from auth provider info

    Args:
        db: Database session
        auth_field: Field name for auth provider ID (clerk_user_id or supabase_user_id)
        auth_user_id: Auth provider user ID
        user_info: User information from auth provider

    Returns:
        Created User model
    """
    # Build user model
    user_data = {
        "id": uuid4(),
        "email": user_info.get("email"),
        "full_name": user_info.get("name"),
        "subscription_tier": "free",
        "subscription_status": "active",
        "is_active": True,
        "is_verified": user_info.get("email_verified", False),
        "user_metadata": user_info.get("metadata", {}),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    # Set auth provider-specific ID
    if auth_field == "clerk_user_id":
        user_data["clerk_user_id"] = auth_user_id
    elif auth_field == "supabase_user_id":
        user_data["supabase_user_id"] = UUID(auth_user_id)

    # Create user
    db_user = User(**user_data)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    logger.info(f"Created new user: {db_user.email} (ID: {db_user.id})")
    return db_user


async def get_current_active_user(
    current_user: UserProfile = Depends(get_current_user),
) -> UserProfile:
    """
    Ensure the current user is active

    Args:
        current_user: Current user from token

    Returns:
        UserProfile if user is active

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user


async def require_subscription_tier(
    required_tier: str,
    current_user: UserProfile = Depends(get_current_active_user),
) -> UserProfile:
    """
    Require specific subscription tier for endpoint access

    Args:
        required_tier: Required subscription tier (free, pro, enterprise)
        current_user: Current authenticated user

    Returns:
        UserProfile if user has required tier

    Raises:
        HTTPException: If user doesn't have required tier
    """
    tier_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}

    user_tier_level = tier_hierarchy.get(current_user.subscription_tier, 0)
    required_tier_level = tier_hierarchy.get(required_tier, 0)

    if user_tier_level < required_tier_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This endpoint requires {required_tier} subscription. "
                   f"Your current tier: {current_user.subscription_tier}",
        )

    return current_user


# Convenience dependencies for different tiers
async def require_pro_tier(
    current_user: UserProfile = Depends(get_current_active_user),
) -> UserProfile:
    """Require Pro or Enterprise subscription"""
    return await require_subscription_tier("pro", current_user)


async def require_enterprise_tier(
    current_user: UserProfile = Depends(get_current_active_user),
) -> UserProfile:
    """Require Enterprise subscription"""
    return await require_subscription_tier("enterprise", current_user)


def require_subscription(tier: str) -> Callable:
    """
    Decorator factory for requiring subscription tiers on endpoints

    Usage:
        @router.get("/premium-feature")
        @require_subscription("pro")
        async def premium_feature(user: UserProfile = Depends(get_current_active_user)):
            ...

    Args:
        tier: Required subscription tier

    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from kwargs
            user = kwargs.get("user") or kwargs.get("current_user")
            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            # Check tier
            tier_hierarchy = {"free": 0, "pro": 1, "enterprise": 2}
            user_tier_level = tier_hierarchy.get(user.subscription_tier, 0)
            required_tier_level = tier_hierarchy.get(tier, 0)

            if user_tier_level < required_tier_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"This feature requires {tier} subscription. "
                           f"Your current tier: {user.subscription_tier}",
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    db: AsyncSession = Depends(get_db),
) -> Optional[UserProfile]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that have different behavior for authenticated users.

    Args:
        credentials: Optional HTTP Bearer token
        db: Database session

    Returns:
        UserProfile if authenticated, None otherwise
    """
    if credentials is None:
        return None

    try:
        # Create a mock credentials object for get_current_user
        return await get_current_user(credentials=credentials, db=db)
    except HTTPException:
        return None


async def verify_api_key(
    api_key: str,
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """
    Verify API key for machine-to-machine authentication
    Alternative to JWT tokens for programmatic access

    Args:
        api_key: API key string
        db: Database session

    Returns:
        UserProfile associated with API key

    Raises:
        HTTPException: If API key is invalid
    """
    # TODO: Implement API key verification
    # This would query a separate api_keys table linked to users
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="API key authentication not yet implemented",
    )
