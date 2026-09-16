import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.database import Base
from app.database_models import (
    AuditEventDB,
    CardDB,
    IdempotencyRecordDB,
    TransactionDB,
    TransactionEventDB,
)


# ============================================================================
# Alembic Configuration
# ============================================================================

config = context.config


# ============================================================================
# Logging
# ============================================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ============================================================================
# SQLAlchemy Metadata
# ============================================================================

# Importing the database models above ensures that every SQLAlchemy model
# is registered with Base.metadata before Alembic performs autogeneration.

target_metadata = Base.metadata


# ============================================================================
# Database URL
# ============================================================================

def get_database_url() -> str:
    """
    Return the database URL used by Alembic.

    DATABASE_URL takes precedence so Alembic uses the same database
    configuration as the application.

    If DATABASE_URL is not defined, the value from alembic.ini is used.
    """
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return database_url

    configured_url = config.get_main_option(
        "sqlalchemy.url"
    )

    if configured_url:
        return configured_url

    raise RuntimeError(
        "Database URL is not configured. Set DATABASE_URL or define "
        "sqlalchemy.url in alembic.ini."
    )


# ============================================================================
# Offline Migrations
# ============================================================================

def run_migrations_offline() -> None:
    """
    Run migrations without creating a database connection.

    This mode generates SQL statements that can be inspected or executed
    separately.
    """
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================================
# Online Migrations
# ============================================================================

def run_migrations_online() -> None:
    """
    Run migrations using an active SQLAlchemy database connection.
    """
    configuration = config.get_section(
        config.config_ini_section,
    )

    if configuration is None:
        configuration = {}

    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================================
# Migration Entry Point
# ============================================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()