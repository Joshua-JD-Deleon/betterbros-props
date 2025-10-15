"""
Clerk Authentication Provider

Handles JWT verification and user info extraction for Clerk.
Uses JWKS (JSON Web Key Set) for signature verification.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import httpx
import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError

from src.config import settings

logger = logging.getLogger(__name__)


class ClerkAuthProvider:
    """
    Clerk authentication provider using JWKS for JWT verification
    """

    def __init__(self):
        self.clerk_secret = settings.CLERK_SECRET_KEY
        self.jwks_url = "https://api.clerk.com/v1/jwks"
        self.issuer = settings.CLERK_JWT_ISSUER

        # Cache for JWKS client
        self._jwks_client: Optional[PyJWKClient] = None
        self._jwks_cache_time: Optional[datetime] = None
        self._jwks_cache_ttl = timedelta(hours=1)

    @property
    def jwks_client(self) -> PyJWKClient:
        """
        Get or create JWKS client with caching
        """
        now = datetime.utcnow()

        # Create new client if cache expired or doesn't exist
        if (self._jwks_client is None or
            self._jwks_cache_time is None or
            now - self._jwks_cache_time > self._jwks_cache_ttl):

            logger.info("Creating new JWKS client for Clerk")
            self._jwks_client = PyJWKClient(
                self.jwks_url,
                cache_keys=True,
                max_cached_keys=10,
                cache_jwk_set=True,
                lifespan=3600,  # 1 hour
            )
            self._jwks_cache_time = now

        return self._jwks_client

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify Clerk JWT token using JWKS

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)

            # Decode and verify token
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": False,  # Clerk doesn't always set audience
                },
            )

            # Verify issuer if configured
            if self.issuer and decoded.get("iss") != self.issuer:
                raise ValueError(f"Invalid issuer: {decoded.get('iss')}")

            # Verify token is not expired
            exp = decoded.get("exp")
            if exp:
                exp_datetime = datetime.fromtimestamp(exp)
                if datetime.utcnow() > exp_datetime:
                    raise ValueError("Token has expired")

            logger.info(f"Successfully verified Clerk token for user: {decoded.get('sub')}")
            return decoded

        except ExpiredSignatureError:
            logger.warning("Clerk token has expired")
            raise ValueError("Token has expired")
        except InvalidTokenError as e:
            logger.error(f"Invalid Clerk token: {e}")
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error(f"Error verifying Clerk token: {e}", exc_info=True)
            raise ValueError(f"Token verification failed: {str(e)}")

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Extract user information from verified Clerk token

        Args:
            token: JWT token string

        Returns:
            Dictionary with user information
        """
        decoded = await self.verify_token(token)

        # Extract user information from Clerk token
        # Clerk tokens contain: sub (user_id), email, name, etc.
        user_info = {
            "user_id": decoded.get("sub"),
            "email": decoded.get("email"),
            "name": decoded.get("name") or decoded.get("first_name", ""),
            "first_name": decoded.get("first_name"),
            "last_name": decoded.get("last_name"),
            "email_verified": decoded.get("email_verified", False),
            "image_url": decoded.get("image_url"),
            "created_at": decoded.get("iat"),  # issued at timestamp
            "metadata": decoded.get("public_metadata", {}),
        }

        # Log successful extraction
        logger.debug(f"Extracted user info from Clerk token: {user_info.get('user_id')}")

        return user_info

    async def fetch_user_from_api(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user details from Clerk API (optional, for additional info)

        Args:
            user_id: Clerk user ID

        Returns:
            User details or None if fetch fails
        """
        if not self.clerk_secret:
            logger.warning("Clerk secret key not configured, cannot fetch user from API")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.clerk.com/v1/users/{user_id}",
                    headers={
                        "Authorization": f"Bearer {self.clerk_secret}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(
                        f"Failed to fetch user from Clerk API: {response.status_code}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Error fetching user from Clerk API: {e}")
            return None

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


# Singleton instance
_clerk_provider: Optional[ClerkAuthProvider] = None


def get_clerk_provider() -> ClerkAuthProvider:
    """
    Get singleton Clerk authentication provider instance
    """
    global _clerk_provider
    if _clerk_provider is None:
        _clerk_provider = ClerkAuthProvider()
    return _clerk_provider
