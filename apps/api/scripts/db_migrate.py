#!/usr/bin/env python3
"""
Database migration script for BetterBros Props

This script provides convenient commands for managing database migrations:
- init: Initialize the database (run migrations)
- upgrade: Upgrade to latest migration
- downgrade: Downgrade one migration
- reset: Reset database (drop all tables and re-migrate)
- status: Show current migration status

Usage:
    python scripts/db_migrate.py init
    python scripts/db_migrate.py upgrade
    python scripts/db_migrate.py downgrade
    python scripts/db_migrate.py reset
    python scripts/db_migrate.py status
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic import command
from sqlalchemy import text

from src.config import settings
from src.db import engine, Base, init_db, close_db


def get_alembic_config() -> Config:
    """Get Alembic configuration"""
    # Get path to alembic.ini
    alembic_ini = Path(__file__).parent.parent / "alembic.ini"

    config = Config(str(alembic_ini))
    config.set_main_option("sqlalchemy.url", settings.database_url_sync)

    return config


async def check_connection():
    """Check if database connection is working"""
    print("Checking database connection...")
    try:
        await init_db()
        print("✓ Database connection successful")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
    finally:
        await close_db()


async def create_database():
    """Create database if it doesn't exist"""
    print("Ensuring database exists...")
    # This would require connecting to postgres database first
    # For now, assume database exists
    print("✓ Database exists")


def run_migrations():
    """Run all pending migrations"""
    print("Running migrations...")
    try:
        config = get_alembic_config()
        command.upgrade(config, "head")
        print("✓ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False


def downgrade_migration():
    """Downgrade one migration"""
    print("Downgrading migration...")
    try:
        config = get_alembic_config()
        command.downgrade(config, "-1")
        print("✓ Downgrade completed successfully")
        return True
    except Exception as e:
        print(f"✗ Downgrade failed: {e}")
        return False


def show_current_revision():
    """Show current database revision"""
    print("Current migration status:")
    try:
        config = get_alembic_config()
        command.current(config)
        return True
    except Exception as e:
        print(f"✗ Failed to get status: {e}")
        return False


def show_history():
    """Show migration history"""
    print("Migration history:")
    try:
        config = get_alembic_config()
        command.history(config)
        return True
    except Exception as e:
        print(f"✗ Failed to get history: {e}")
        return False


async def drop_all_tables():
    """Drop all tables from database"""
    print("Dropping all tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("✓ All tables dropped")
        return True
    except Exception as e:
        print(f"✗ Failed to drop tables: {e}")
        return False


async def reset_database():
    """Reset database (drop all tables and re-migrate)"""
    print("\n=== RESETTING DATABASE ===")
    print("WARNING: This will delete all data!")
    response = input("Are you sure? (yes/no): ")

    if response.lower() != "yes":
        print("Reset cancelled")
        return False

    # Drop all tables
    if not await drop_all_tables():
        return False

    # Run migrations
    if not run_migrations():
        return False

    print("\n✓ Database reset complete!")
    return True


async def init_database():
    """Initialize database (check connection and run migrations)"""
    print("\n=== INITIALIZING DATABASE ===")

    # Check connection
    if not await check_connection():
        return False

    # Run migrations
    if not run_migrations():
        return False

    print("\n✓ Database initialization complete!")
    return True


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    try:
        if command == "init":
            success = await init_database()
        elif command == "upgrade":
            success = run_migrations()
        elif command == "downgrade":
            success = downgrade_migration()
        elif command == "reset":
            success = await reset_database()
        elif command == "status":
            success = show_current_revision()
        elif command == "history":
            success = show_history()
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            success = False

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\nOperation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
