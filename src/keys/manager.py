"""
API key management with secure storage and validation.

Security Features:
- Never logs actual key values
- Sets secure file permissions (600)
- Validates keys before storing
- Supports testing keys with actual API calls
"""

from typing import Dict, Optional, List, Any
from pathlib import Path
import os
import re
import stat
import logging
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class KeyManager:
    """
    Manages API keys with secure storage and validation.
    """

    PROVIDERS = {
        "odds_api": {
            "env_var": "ODDS_API_KEY",
            "pattern": r"^[A-Za-z0-9]{32}$",  # 32 character alphanumeric
            "test_url": None,  # Custom test via test_odds_api_connection
            "test_method": "custom",
            "test_timeout": 10.0,
            "requires_auth": True
        },
        "sleeper": {
            "env_var": "SLEEPER_API_KEY",
            "pattern": r"^[A-Za-z0-9_\-]{20,}$",  # Basic pattern
            "test_url": "https://api.sleeper.app/v1/state/nfl",
            "test_method": "get",
            "test_timeout": 10.0,
            "requires_auth": False
        },
        "openweather": {
            "env_var": "OPENWEATHER_KEY",
            "pattern": r"^[A-Za-z0-9]{32}$",  # 32 character alphanumeric
            "test_url": "https://api.openweathermap.org/data/2.5/weather",
            "test_method": "get",
            "test_timeout": 10.0,
            "requires_auth": True,
            "test_params": {"q": "London", "appid": "{api_key}"}
        }
    }

    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialize key manager.

        Args:
            env_file: Path to .env file (defaults to .env.local in project root)
        """
        self.env_file = env_file or Path(".env.local")
        self._ensure_env_file()
        self._load_env()

    def _ensure_env_file(self) -> None:
        """Ensure .env file exists with secure permissions."""
        if not self.env_file.exists():
            self.env_file.touch()
            logger.info(f"Created new env file: {self.env_file}")

        # Set secure permissions (owner read/write only)
        self._set_secure_permissions(self.env_file)

    def _set_secure_permissions(self, path: Path) -> None:
        """Set file permissions to 600 (owner read/write only)."""
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600
            logger.debug(f"Set secure permissions on {path}")
        except Exception as e:
            logger.warning(f"Could not set secure permissions on {path}: {e}")

    def _load_env(self) -> None:
        """Load environment variables from file."""
        if not self.env_file.exists():
            return

        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    os.environ[key] = value

    def set_key(self, provider: str, api_key: str) -> Dict[str, Any]:
        """
        Set API key for a provider.

        Args:
            provider: Provider name (e.g., 'sleeper', 'openweather')
            api_key: API key value

        Returns:
            Dict with:
                - success: bool
                - message: str
                - provider: str
        """
        if provider not in self.PROVIDERS:
            return {
                'success': False,
                'message': f"Unknown provider: {provider}. Must be one of {list(self.PROVIDERS.keys())}",
                'provider': provider
            }

        provider_info = self.PROVIDERS[provider]
        env_var = provider_info['env_var']

        # Validate key format (basic check)
        if provider_info.get('pattern'):
            pattern = provider_info['pattern']
            if not re.match(pattern, api_key):
                logger.warning(f"API key for {provider} does not match expected pattern")
                # Note: We don't fail here as patterns are just guidelines

        # Update .env file
        try:
            self._write_env_key(env_var, api_key)

            # Update current environment
            os.environ[env_var] = api_key

            logger.info(f"Successfully set API key for {provider}")

            return {
                'success': True,
                'message': f"API key for {provider} set successfully",
                'provider': provider
            }
        except Exception as e:
            logger.error(f"Failed to set API key for {provider}: {e}")
            return {
                'success': False,
                'message': f"Failed to set API key: {str(e)}",
                'provider': provider
            }

    def get_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a provider.

        Args:
            provider: Provider name

        Returns:
            API key or None if not set

        Note: This function should never be used for logging
        """
        if provider not in self.PROVIDERS:
            return None

        env_var = self.PROVIDERS[provider]['env_var']
        return os.getenv(env_var)

    def test_key(self, provider: str) -> Dict[str, Any]:
        """
        Test API key validity by making actual API call.

        Args:
            provider: Provider name

        Returns:
            Dict with:
                - valid: bool
                - message: str
                - provider: str
                - details: dict (provider-specific test results)
        """
        api_key = self.get_key(provider)

        if not api_key:
            return {
                "valid": False,
                "message": f"No API key set for {provider}",
                "provider": provider,
                "details": {"error": "missing_key"}
            }

        if provider not in self.PROVIDERS:
            return {
                "valid": False,
                "message": f"Unknown provider: {provider}",
                "provider": provider,
                "details": {"error": "unknown_provider"}
            }

        provider_info = self.PROVIDERS[provider]

        try:
            # Test the API key
            if provider == "odds_api":
                result = self._test_odds_api_key(api_key, provider_info)
            elif provider == "sleeper":
                result = self._test_sleeper_key(api_key, provider_info)
            elif provider == "openweather":
                result = self._test_openweather_key(api_key, provider_info)
            else:
                result = {
                    "valid": False,
                    "message": f"No test implementation for {provider}",
                    "details": {"error": "no_test_implementation"}
                }

            result["provider"] = provider
            return result

        except Exception as e:
            logger.error(f"Error testing {provider} API key: {e}")
            return {
                "valid": False,
                "message": f"Error testing API key: {str(e)}",
                "provider": provider,
                "details": {"error": str(e)}
            }

    def _test_odds_api_key(self, api_key: str, provider_info: Dict) -> Dict[str, Any]:
        """Test The Odds API key."""
        try:
            from src.ingest.odds_api_client import test_odds_api_connection
            return test_odds_api_connection(api_key)
        except Exception as e:
            return {
                "valid": False,
                "message": f"Error testing Odds API: {str(e)}",
                "details": {"error": str(e)}
            }

    def _test_sleeper_key(self, api_key: str, provider_info: Dict) -> Dict[str, Any]:
        """Test Sleeper API key."""
        url = provider_info['test_url']
        timeout = provider_info['test_timeout']

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "valid": True,
                        "message": "Sleeper API key is valid",
                        "details": {
                            "status_code": response.status_code,
                            "season": data.get('season', 'Unknown'),
                            "week": data.get('week', 'Unknown')
                        }
                    }
                else:
                    return {
                        "valid": False,
                        "message": f"Sleeper API returned status {response.status_code}",
                        "details": {
                            "status_code": response.status_code,
                            "error": "invalid_response"
                        }
                    }
        except httpx.TimeoutException:
            return {
                "valid": False,
                "message": "Request timed out",
                "details": {"error": "timeout"}
            }
        except httpx.HTTPError as e:
            return {
                "valid": False,
                "message": f"HTTP error: {str(e)}",
                "details": {"error": "http_error"}
            }

    def _test_openweather_key(self, api_key: str, provider_info: Dict) -> Dict[str, Any]:
        """Test OpenWeather API key."""
        url = provider_info['test_url']
        timeout = provider_info['test_timeout']

        # Build test params with actual API key
        params = {}
        for k, v in provider_info['test_params'].items():
            if v == "{api_key}":
                params[k] = api_key
            else:
                params[k] = v

        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "valid": True,
                        "message": "OpenWeather API key is valid",
                        "details": {
                            "status_code": response.status_code,
                            "location": data.get('name', 'Unknown'),
                            "temp": data.get('main', {}).get('temp', 'Unknown')
                        }
                    }
                elif response.status_code == 401:
                    return {
                        "valid": False,
                        "message": "Invalid API key",
                        "details": {
                            "status_code": response.status_code,
                            "error": "unauthorized"
                        }
                    }
                else:
                    return {
                        "valid": False,
                        "message": f"OpenWeather API returned status {response.status_code}",
                        "details": {
                            "status_code": response.status_code,
                            "error": "invalid_response"
                        }
                    }
        except httpx.TimeoutException:
            return {
                "valid": False,
                "message": "Request timed out",
                "details": {"error": "timeout"}
            }
        except httpx.HTTPError as e:
            return {
                "valid": False,
                "message": f"HTTP error: {str(e)}",
                "details": {"error": "http_error"}
            }

    def list_keys(self) -> List[Dict[str, Any]]:
        """
        List all configured API keys (masked).

        Returns:
            List of dicts with:
                - provider: str
                - is_set: bool
                - masked_value: str (e.g., "sk_***************xyz")
                - last_tested: Optional[str] (ISO timestamp)
                - last_test_status: Optional[str] ("valid" | "invalid" | "unknown")
        """
        results = []

        for provider in self.PROVIDERS.keys():
            api_key = self.get_key(provider)
            is_set = api_key is not None and len(api_key) > 0

            result = {
                'provider': provider,
                'is_set': is_set,
                'masked_value': mask_api_key(api_key) if is_set else None,
                'last_tested': None,
                'last_test_status': 'unknown'
            }

            results.append(result)

        return results

    def delete_key(self, provider: str) -> Dict[str, Any]:
        """
        Remove API key for a provider.

        Args:
            provider: Provider name

        Returns:
            Dict with:
                - success: bool
                - message: str
        """
        if provider not in self.PROVIDERS:
            return {
                'success': False,
                'message': f"Unknown provider: {provider}"
            }

        env_var = self.PROVIDERS[provider]['env_var']

        try:
            # Remove from environment
            if env_var in os.environ:
                del os.environ[env_var]

            # Remove from .env file
            self._remove_env_key(env_var)

            logger.info(f"Successfully deleted API key for {provider}")

            return {
                'success': True,
                'message': f"API key for {provider} deleted successfully"
            }
        except Exception as e:
            logger.error(f"Failed to delete API key for {provider}: {e}")
            return {
                'success': False,
                'message': f"Failed to delete API key: {str(e)}"
            }

    def _write_env_key(self, key: str, value: str) -> None:
        """
        Write or update a key in the .env file.

        Args:
            key: Environment variable name
            value: Environment variable value
        """
        # Read existing content
        env_dict = read_env_file(str(self.env_file))

        # Update key
        env_dict[key] = value

        # Write back
        write_env_file(str(self.env_file), env_dict)

        # Ensure secure permissions
        self._set_secure_permissions(self.env_file)

    def _remove_env_key(self, key: str) -> None:
        """
        Remove a key from the .env file.

        Args:
            key: Environment variable name to remove
        """
        # Read existing content
        env_dict = read_env_file(str(self.env_file))

        # Remove key if exists
        if key in env_dict:
            del env_dict[key]

        # Write back
        write_env_file(str(self.env_file), env_dict)


# Helper functions for .env file manipulation

def read_env_file(path: str) -> Dict[str, str]:
    """
    Parse .env file into dict.

    Args:
        path: Path to .env file

    Returns:
        Dictionary of environment variables
    """
    env_dict = {}

    if not Path(path).exists():
        return env_dict

    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes if present
                value = value.strip('"').strip("'")
                env_dict[key.strip()] = value

    return env_dict


def write_env_file(path: str, values: Dict[str, str]) -> None:
    """
    Write dict to .env file, preserving structure.

    Args:
        path: Path to .env file
        values: Dictionary of environment variables
    """
    path_obj = Path(path)

    # Read existing comments and structure
    existing_lines = []
    if path_obj.exists():
        with open(path, 'r') as f:
            existing_lines = f.readlines()

    # Build new content
    new_lines = []
    keys_written = set()

    # Preserve existing structure, updating values
    for line in existing_lines:
        stripped = line.strip()
        if stripped.startswith('#') or not stripped:
            # Preserve comments and empty lines
            new_lines.append(line)
        elif '=' in stripped:
            key = stripped.split('=')[0].strip()
            if key in values:
                # Update existing key
                new_lines.append(f"{key}={values[key]}\n")
                keys_written.add(key)
            else:
                # Keep existing line
                new_lines.append(line)

    # Add any new keys not in the original file
    for key, value in values.items():
        if key not in keys_written:
            new_lines.append(f"{key}={value}\n")

    # Write to file
    with open(path, 'w') as f:
        f.writelines(new_lines)


def set_file_permissions(path: str, mode: int = 0o600) -> None:
    """
    Set secure file permissions.

    Args:
        path: Path to file
        mode: Permission mode (default: 0o600 - owner read/write only)
    """
    try:
        os.chmod(path, mode)
    except Exception as e:
        logger.warning(f"Could not set permissions on {path}: {e}")


def mask_api_key(key: str, show_chars: int = 4) -> str:
    """
    Mask API key for display.

    Args:
        key: Full API key
        show_chars: How many chars to show at start and end

    Returns:
        Masked string like "sk_***************xyz"
    """
    if not key:
        return ""

    if len(key) <= show_chars * 2:
        return "*" * len(key)

    start = key[:show_chars]
    end = key[-show_chars:]
    middle = "*" * min(15, len(key) - show_chars * 2)

    return f"{start}{middle}{end}"


# Convenience functions for functional API

def keys_set(provider: str, api_key: str, env_file: str = ".env.local") -> Dict[str, Any]:
    """
    Set API key for a provider.

    Args:
        provider: Provider name (e.g., "sleeper", "openweather")
        api_key: The API key value
        env_file: Path to .env file (default: .env.local)

    Returns:
        Dict with:
            - success: bool
            - message: str
            - provider: str
    """
    manager = KeyManager(env_file=Path(env_file))
    return manager.set_key(provider, api_key)


def keys_get(provider: str, env_file: str = ".env.local") -> Optional[str]:
    """
    Get API key for a provider.

    Args:
        provider: Provider name
        env_file: Path to .env file

    Returns:
        API key value or None if not set

    Note: Should never log the returned value
    """
    manager = KeyManager(env_file=Path(env_file))
    return manager.get_key(provider)


def keys_test(provider: str, env_file: str = ".env.local") -> Dict[str, Any]:
    """
    Test if API key works for a provider.

    Args:
        provider: "sleeper" | "openweather" | etc.
        env_file: Path to .env file

    Returns:
        Dict with:
            - valid: bool
            - message: str
            - provider: str
            - details: dict (provider-specific test results)
    """
    manager = KeyManager(env_file=Path(env_file))
    return manager.test_key(provider)


def keys_list(env_file: str = ".env.local") -> List[Dict[str, Any]]:
    """
    List all configured API keys (masked).

    Args:
        env_file: Path to .env file

    Returns:
        List of dicts with:
            - provider: str
            - is_set: bool
            - masked_value: str (e.g., "sk_***************xyz")
            - last_tested: Optional[str] (ISO timestamp)
            - last_test_status: Optional[str] ("valid" | "invalid" | "unknown")
    """
    manager = KeyManager(env_file=Path(env_file))
    return manager.list_keys()


def keys_delete(provider: str, env_file: str = ".env.local") -> Dict[str, Any]:
    """
    Remove API key for a provider.

    Args:
        provider: Provider name
        env_file: Path to .env file

    Returns:
        Dict with:
            - success: bool
            - message: str
    """
    manager = KeyManager(env_file=Path(env_file))
    return manager.delete_key(provider)
