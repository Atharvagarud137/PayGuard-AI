
import os
from logging.config import fileConfig
from urllib.parse import urlsplit

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.database import Base
from app.database_models import (
    AuditEventDB,
    CardDB,
    IdempotencyRecordDB,
    TransactionDB,
    TransactionEventDB,
    ScenarioDefinitionDB,
    ScenarioRunDB,
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

# Importing the models ensures their tables are registered with Base.metadata
# before Alembic performs migration autogeneration.
target_metadata = Base.metadata


# ============================================================================
# Database URL
# ============================================================================

def get_database_url() -> str:
    """
    Return the dedicated migration-owner connection URL.

    Alembic must never silently fall back to the application's runtime
    DATABASE_URL. Configure PAYGUARD_MIGRATION_DATABASE_URL explicitly.
    """
    database_url = os.getenv("PAYGUARD_MIGRATION_DATABASE_URL")

    if database_url is None or not database_url.strip():
        raise RuntimeError(
            "PAYGUARD_MIGRATION_DATABASE_URL must be explicitly configured "
            "for Alembic migrations."
        )

    database_url = database_url.strip()
    parsed_url = urlsplit(database_url)

    if parsed_url.scheme != "postgresql+psycopg":
        raise RuntimeError(
            "Alembic requires a PostgreSQL URL using the "
            "postgresql+psycopg driver."
        )

    if not parsed_url.hostname or not parsed_url.path.strip("/"):
        raise RuntimeError(
            "The database URL must specify a database host and database name."
        )

    return database_url


# ============================================================================
# Offline Migrations
# ============================================================================

def run_migrations_offline() -> None:
    """
    Generate migration SQL without creating a database connection.

    The generated SQL can be reviewed before execution against PostgreSQL.
    """
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================================
# Online Migrations
# ============================================================================

def run_migrations_online() -> None:
    """Run migrations using an active SQLAlchemy database connection."""
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

    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                compare_type=True,
                compare_server_default=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


# ============================================================================
# Migration Entry Point
# ============================================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
