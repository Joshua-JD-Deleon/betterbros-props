"""
Supabase Authentication Provider

Handles JWT verification and user info extraction for Supabase.
Uses symmetric JWT secret for verification (HS256 algorithm).
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from src.config import settings

logger = logging.getLogger(__name__)


class SupabaseAuthProvider:
    """
    Supabase authentication provider using JWT secret for verification
    """

    def __init__(self):
        self.jwt_secret = settings.SUPABASE_JWT_SECRET
        self.supabase_url = settings.SUPABASE_URL

        if not self.jwt_secret:
            logger.warning("Supabase JWT secret not configured")

        # Expected issuer format: https://<project-ref>.supabase.co/auth/v1
        self.expected_issuer = f"{self.supabase_url}/auth/v1" if self.supabase_url else None

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Supabase JWT token using JWT secret

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            ValueError: If token is invalid or expired
        """
        if not self.jwt_secret:
            raise ValueError("Supabase JWT secret not configured")

        try:
            # Decode and verify token with HS256 (symmetric key)
            decoded = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": True,
                },
                audience="authenticated",  # Supabase uses 'authenticated' audience
            )

            # Verify issuer
            if self.expected_issuer and decoded.get("iss") != self.expected_issuer:
                # Also accept issuer without /auth/v1 suffix (some Supabase versions)
                alt_issuer = self.supabase_url
                if decoded.get("iss") != alt_issuer:
                    raise ValueError(f"Invalid issuer: {decoded.get('iss')}")

            # Verify token is not expired
            exp = decoded.get("exp")
            if exp:
                exp_datetime = datetime.fromtimestamp(exp)
                if datetime.utcnow() > exp_datetime:
                    raise ValueError("Token has expired")

            logger.info(f"Successfully verified Supabase token for user: {decoded.get('sub')}")
            return decoded

        except ExpiredSignatureError:
            logger.warning("Supabase token has expired")
            raise ValueError("Token has expired")
        except InvalidTokenError as e:
            logger.error(f"Invalid Supabase token: {e}")
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Error verifying Supabase token: {e}", exc_info=True)
            raise ValueError(f"Token verification failed: {str(e)}")

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Extract user information from verified Supabase token

        Args:
            token: JWT token string

        Returns:
            Dictionary with user information
        """
        decoded = await self.verify_token(token)

        # Extract user information from Supabase token
        # Supabase tokens contain: sub (user_id), email, user_metadata, app_metadata
        user_metadata = decoded.get("user_metadata", {})
        app_metadata = decoded.get("app_metadata", {})

        user_info = {
            "user_id": decoded.get("sub"),
            "email": decoded.get("email"),
            "name": user_metadata.get("name") or user_metadata.get("full_name", ""),
            "first_name": user_metadata.get("first_name"),
            "last_name": user_metadata.get("last_name"),
            "email_verified": decoded.get("email_verified", False),
            "phone": decoded.get("phone"),
            "phone_verified": decoded.get("phone_verified", False),
            "avatar_url": user_metadata.get("avatar_url"),
            "created_at": decoded.get("iat"),  # issued at timestamp
            "role": decoded.get("role"),  # Supabase role
            "metadata": user_metadata,
            "app_metadata": app_metadata,
            # Provider info
            "provider": app_metadata.get("provider"),
            "providers": app_metadata.get("providers", []),
        }

        # Log successful extraction
        logger.debug(f"Extracted user info from Supabase token: {user_info.get('user_id')}")

        return user_info

    async def validate_session(self, token: str) -> bool:
        """
        Validate if a session token is still active

        Args:
            token: JWT token string

        Returns:
            True if session is valid, False otherwise
        """
        try:
            await self.verify_token(token)
            return True
        except ValueError:
            return False

    def extract_token_expiry(self, token: str) -> Optional[datetime]:
        """
        Extract expiration time from token without full verification

        Args:
            token: JWT token string

        Returns:
            Expiration datetime or None
        """
        try:
            # Decode without verification to get expiry
            decoded = jwt.decode(
                token,
                options={"verify_signature": False},
            )
            exp = decoded.get("exp")
            if exp:
                return datetime.fromtimestamp(exp)
            return None
        except Exception as e:
            logger.error(f"Error extracting token expiry: {e}")
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh an access token using a refresh token
        Note: This should typically be handled by the client-side Supabase client

        Args:
            refresh_token: Refresh token string

        Returns:
            New token data or None if refresh fails
        """
        # This is typically handled by the Supabase client library
        # on the frontend. Backend just validates access tokens.
        logger.warning("Token refresh should be handled by client-side Supabase SDK")
        return None


# Singleton instance
_supabase_provider: Optional[SupabaseAuthProvider] = None


def get_supabase_provider() -> SupabaseAuthProvider:
    """
    Get singleton Supabase authentication provider instance
    """
    global _supabase_provider
    if _supabase_provider is None:
        _supabase_provider = SupabaseAuthProvider()
    return _supabase_provider
