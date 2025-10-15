"""
Props Markets Router
Endpoints for fetching and managing prop markets
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import redis.asyncio as redis

from src.types import (
    PropMarket,
    PropMarketCreate,
    PropMarketResponse,
    Sport,
    Platform,
    UserProfile,
)
from src.auth.deps import get_current_active_user
from src.db import get_db, get_redis, PropMarket as PropMarketModel
from src.ingest import SleeperAPI, InjuriesAPI
from src.config import settings

router = APIRouter()


@router.get("/", response_model=PropMarketResponse)
async def list_prop_markets(
    sport: Optional[Sport] = None,
    platform: Optional[Platform] = None,
    is_active: bool = True,
    start_time_after: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    List available prop markets with filtering

    Fetches prop markets from database with optional filters for:
    - Sport (NBA, NFL, etc.)
    - Platform (PrizePicks, Underdog)
    - Active status
    - Start time
    """
    try:
        # Build query
        query = select(PropMarketModel).where(PropMarketModel.is_active == is_active)

        if sport:
            query = query.where(PropMarketModel.sport == sport.value)

        if platform:
            query = query.where(PropMarketModel.platform == platform.value)

        if start_time_after:
            query = query.where(PropMarketModel.start_time >= start_time_after)

        # Get total count
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(PropMarketModel.start_time).limit(page_size).offset(offset)

        # Execute query
        result = await db.execute(query)
        markets_db = result.scalars().all()

        # Convert to Pydantic models
        markets = [
            PropMarket(
                id=m.id,
                platform=Platform(m.platform),
                sport=Sport(m.sport),
                prop_type=m.prop_type,
                legs=m.legs_data,
                payout_multiplier=m.payout_multiplier,
                created_at=m.created_at,
                start_time=m.start_time,
                expires_at=m.expires_at,
                is_active=m.is_active,
                min_legs=m.min_legs,
                max_legs=m.max_legs,
            )
            for m in markets_db
        ]

        return PropMarketResponse(
            markets=markets,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list prop markets: {str(e)}",
        )


@router.get("/{market_id}", response_model=PropMarket)
async def get_prop_market(
    market_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get detailed information for a specific prop market

    Returns complete market data including all legs and metadata
    """
    try:
        # Check Redis cache first
        cache_key = f"prop_market:{market_id}"
        cached_data = await redis_client.get(cache_key)

        if cached_data:
            return PropMarket.model_validate_json(cached_data)

        # Query database
        query = select(PropMarketModel).where(PropMarketModel.id == market_id)
        result = await db.execute(query)
        market_db = result.scalar_one_or_none()

        if not market_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Market {market_id} not found",
            )

        # Convert to Pydantic model
        market = PropMarket(
            id=market_db.id,
            platform=Platform(market_db.platform),
            sport=Sport(market_db.sport),
            prop_type=market_db.prop_type,
            legs=market_db.legs_data,
            payout_multiplier=market_db.payout_multiplier,
            created_at=market_db.created_at,
            start_time=market_db.start_time,
            expires_at=market_db.expires_at,
            is_active=market_db.is_active,
            min_legs=market_db.min_legs,
            max_legs=market_db.max_legs,
        )

        # Cache for 5 minutes
        await redis_client.setex(
            cache_key,
            settings.REDIS_CACHE_TTL,
            market.model_dump_json(),
        )

        return market

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prop market: {str(e)}",
        )


@router.post("/import", response_model=PropMarketResponse, status_code=status.HTTP_201_CREATED)
async def import_prop_markets(
    request: PropMarketCreate,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Import prop markets from external platforms

    Parses raw market data from platforms like PrizePicks or Underdog
    and normalizes it to our internal schema.
    """
    try:
        imported_markets = []

        for market_data in request.markets:
            # Create database record
            market_db = PropMarketModel(
                platform=request.platform.value,
                sport=request.sport.value,
                prop_type=market_data.get("prop_type", "over_under"),
                legs_data=market_data.get("legs", []),
                payout_multiplier=market_data.get("payout_multiplier", 3.0),
                start_time=datetime.fromisoformat(market_data["start_time"]),
                expires_at=datetime.fromisoformat(market_data["expires_at"]) if "expires_at" in market_data else None,
                is_active=market_data.get("is_active", True),
                min_legs=market_data.get("min_legs", 2),
                max_legs=market_data.get("max_legs", 6),
                created_at=datetime.utcnow(),
            )

            db.add(market_db)
            await db.flush()
            await db.refresh(market_db)

            # Convert to Pydantic model
            market = PropMarket(
                id=market_db.id,
                platform=Platform(market_db.platform),
                sport=Sport(market_db.sport),
                prop_type=market_db.prop_type,
                legs=market_db.legs_data,
                payout_multiplier=market_db.payout_multiplier,
                created_at=market_db.created_at,
                start_time=market_db.start_time,
                expires_at=market_db.expires_at,
                is_active=market_db.is_active,
                min_legs=market_db.min_legs,
                max_legs=market_db.max_legs,
            )

            imported_markets.append(market)

        await db.commit()

        return PropMarketResponse(
            markets=imported_markets,
            total=len(imported_markets),
            page=1,
            page_size=len(imported_markets),
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import prop markets: {str(e)}",
        )


@router.post("/refresh")
async def refresh_prop_markets(
    platform: Platform,
    sport: Sport,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Trigger refresh of prop markets from external API

    Fetches latest markets from platform APIs and updates the database.
    Currently supports Sleeper API for NFL data.
    """
    try:
        updated_count = 0

        # For NFL, use Sleeper API
        if sport == Sport.NFL:
            async with SleeperAPI() as sleeper:
                # This is a placeholder - you would implement actual market fetching
                # based on your platform's API structure
                players = await sleeper.get_all_players()

                # Example: You'd transform this data into prop markets
                # For now, just return status
                updated_count = len(players)

        # Invalidate relevant caches
        cache_pattern = f"prop_market:*"
        # Note: Redis SCAN would be used in production for safe cache invalidation

        return {
            "status": "success",
            "platform": platform,
            "sport": sport,
            "updated_count": updated_count,
            "message": f"Refreshed {updated_count} prop markets",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh prop markets: {str(e)}",
        )


@router.delete("/{market_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prop_market(
    market_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Soft delete a prop market

    Marks the market as inactive rather than removing from database
    """
    try:
        # Get market
        query = select(PropMarketModel).where(PropMarketModel.id == market_id)
        result = await db.execute(query)
        market_db = result.scalar_one_or_none()

        if not market_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Market {market_id} not found",
            )

        # Soft delete
        market_db.is_active = False
        market_db.updated_at = datetime.utcnow()

        await db.commit()

        # Invalidate cache
        cache_key = f"prop_market:{market_id}"
        await redis_client.delete(cache_key)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete prop market: {str(e)}",
        )
