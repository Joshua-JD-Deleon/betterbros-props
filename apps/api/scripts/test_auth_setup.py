"""
Authentication Setup Validation Script

Validates that the authentication system is properly configured
and all required environment variables are set.
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def check_env_var(name: str, required: bool = True) -> bool:
    """Check if environment variable is set"""
    value = os.getenv(name)
    status = "✓" if value else "✗"
    req_str = "REQUIRED" if required else "OPTIONAL"

    if value:
        # Mask sensitive values
        if "SECRET" in name or "KEY" in name:
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"{status} {name}: {masked} ({req_str})")
        else:
            print(f"{status} {name}: {value} ({req_str})")
        return True
    else:
        print(f"{status} {name}: NOT SET ({req_str})")
        return False


def validate_auth_config():
    """Validate authentication configuration"""
    print("\n" + "=" * 60)
    print("Authentication Setup Validation")
    print("=" * 60 + "\n")

    # Check AUTH_PROVIDER
    print("1. Auth Provider Configuration:")
    print("-" * 60)
    auth_provider = os.getenv("AUTH_PROVIDER")

    if not auth_provider:
        print("✗ AUTH_PROVIDER: NOT SET (REQUIRED)")
        print("  Please set AUTH_PROVIDER to either 'clerk' or 'supabase'")
        return False

    print(f"✓ AUTH_PROVIDER: {auth_provider}")

    # Validate provider-specific configuration
    if auth_provider == "clerk":
        print("\n2. Clerk Configuration:")
        print("-" * 60)
        has_secret = check_env_var("CLERK_SECRET_KEY", required=True)
        check_env_var("CLERK_JWT_ISSUER", required=False)

        if not has_secret:
            print("\n✗ Missing required Clerk configuration")
            return False

    elif auth_provider == "supabase":
        print("\n2. Supabase Configuration:")
        print("-" * 60)
        has_url = check_env_var("SUPABASE_URL", required=True)
        has_jwt = check_env_var("SUPABASE_JWT_SECRET", required=True)
        check_env_var("SUPABASE_SERVICE_ROLE_KEY", required=False)

        if not (has_url and has_jwt):
            print("\n✗ Missing required Supabase configuration")
            return False

    else:
        print(f"\n✗ Invalid AUTH_PROVIDER: {auth_provider}")
        print("  Must be either 'clerk' or 'supabase'")
        return False

    # Check database configuration
    print("\n3. Database Configuration:")
    print("-" * 60)
    has_db = check_env_var("DATABASE_URL", required=True)

    if not has_db:
        print("\n✗ Missing required database configuration")
        return False

    # Check optional configuration
    print("\n4. Optional Configuration:")
    print("-" * 60)
    check_env_var("REDIS_URL", required=False)
    check_env_var("LOG_LEVEL", required=False)

    print("\n" + "=" * 60)
    print("✓ Authentication configuration is valid!")
    print("=" * 60 + "\n")

    # Test imports
    print("5. Testing Module Imports:")
    print("-" * 60)

    try:
        from src.config import settings
        print("✓ Config module imported successfully")
        print(f"  - AUTH_PROVIDER: {settings.AUTH_PROVIDER}")
    except Exception as e:
        print(f"✗ Failed to import config: {e}")
        return False

    try:
        from src.auth.clerk import get_clerk_provider
        print("✓ Clerk provider module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import Clerk provider: {e}")
        return False

    try:
        from src.auth.supabase import get_supabase_provider
        print("✓ Supabase provider module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import Supabase provider: {e}")
        return False

    try:
        from src.auth.deps import get_current_user
        print("✓ Auth dependencies imported successfully")
    except Exception as e:
        print(f"✗ Failed to import auth dependencies: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ All modules imported successfully!")
    print("=" * 60 + "\n")

    print("Next Steps:")
    print("-" * 60)
    print("1. Start the API server: uvicorn main:app --reload")
    print("2. Configure frontend AUTH_PROVIDER environment variable")
    print("3. Test authentication with a sign-in")
    print("4. Make an authenticated API request")
    print("\n")

    return True


if __name__ == "__main__":
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenv not installed, using system environment only")

    success = validate_auth_config()
    sys.exit(0 if success else 1)
