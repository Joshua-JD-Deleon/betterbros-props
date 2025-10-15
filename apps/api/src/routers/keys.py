"""
API Keys Router
Endpoints for managing external API keys
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from src.types import (
    ApiKey,
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeySource,
    UserProfile,
)
from src.auth.deps import get_current_active_user

router = APIRouter()


@router.get("/", response_model=ApiKeyResponse)
async def list_api_keys(
    source: Optional[ApiKeySource] = None,
    current_user: UserProfile = Depends(get_current_active_user),
):
    """
    List user's API keys

    TODO: Implementation
    - Query database for user's API keys
    - Filter by source if specified
    - Never return full keys, only previews
    - Return list of keys
    """
    return ApiKeyResponse(
        keys=[],
        total=0,
    )


@router.get("/{key_id}", response_model=ApiKey)
async def get_api_key(
    key_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
):
    """
    Get API key details

    TODO: Implementation
    - Query database for key
    - Verify user ownership
    - Return key details (without full key value)
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"API key {key_id} not found (stub)",
    )


@router.post("/", response_model=ApiKey, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: ApiKeyCreate,
    current_user: UserProfile = Depends(get_current_active_user),
):
    """
    Create or update an API key

    TODO: Implementation
    - Encrypt the API key using encryption key from settings
    - Store encrypted key in database
    - Validate key by making test API call
    - Return key metadata
    """
    return ApiKey(
        id="key_stub",
        source=request.source,
        name=request.name,
        key_preview="****" + request.key[-4:] if len(request.key) >= 4 else "****",
        is_active=True,
        requests_made=0,
        created_by=current_user.user_id,
    )


@router.put("/{key_id}", response_model=ApiKey)
async def update_api_key(
    key_id: str,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: UserProfile = Depends(get_current_active_user),
):
    """
    Update API key metadata

    TODO: Implementation
    - Load key from database
    - Verify user ownership
    - Update mutable fields (name, is_active)
    - Return updated key
    """
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"API key {key_id} not found (stub)",
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
):
    """
    Delete an API key

    TODO: Implementation
    - Verify user ownership
    - Delete from database (or soft delete)
    - Clear from cache
    """
    pass


@router.post("/{key_id}/validate")
async def validate_api_key(
    key_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
):
    """
    Validate an API key by making a test call

    TODO: Implementation
    - Load and decrypt key
    - Make test API call to external service
    - Update validation status
    - Return validation result
    """
    return {
        "key_id": key_id,
        "is_valid": True,
        "validated_at": None,
        "message": "Stub implementation",
    }


@router.get("/{key_id}/usage")
async def get_api_key_usage(
    key_id: str,
    current_user: UserProfile = Depends(get_current_active_user),
):
    """
    Get usage statistics for an API key

    TODO: Implementation
    - Query usage logs for key
    - Calculate requests made, rate limits
    - Return usage statistics
    """
    return {
        "key_id": key_id,
        "usage": {
            "total_requests": 0,
            "requests_today": 0,
            "last_used_at": None,
        },
        "message": "Stub implementation",
    }
