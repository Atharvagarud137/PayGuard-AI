
import os
from typing import Generator
from urllib.parse import urlsplit

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# ============================================================================
# Database Configuration
# ============================================================================

DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://payguard:payguard@localhost:5432/payguard"
)


def _get_database_url() -> str:
    """
    Read and validate the database URL.

    DATABASE_URL should be supplied through the environment for deployments.
    The default is intended only for local development.
    """
    database_url = os.getenv(
        "DATABASE_URL",
        DEFAULT_DATABASE_URL,
    ).strip()

    if not database_url:
        raise RuntimeError("DATABASE_URL must not be empty")

    parsed_url = urlsplit(database_url)

    if parsed_url.scheme != "postgresql+psycopg":
        raise RuntimeError(
            "DATABASE_URL must use the postgresql+psycopg driver"
        )

    if not parsed_url.hostname or not parsed_url.path.strip("/"):
        raise RuntimeError(
            "DATABASE_URL must specify a database host and database name"
        )

    return database_url


DATABASE_URL = _get_database_url()


# ============================================================================
# SQLAlchemy Engine
# ============================================================================

engine: Engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
)


# ============================================================================
# Session Factory
# ============================================================================

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ============================================================================
# Declarative Base
# ============================================================================

class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy persistence models.

    Domain and API models remain defined separately in app.models.
    Database models inherit from this class and represent the
    PostgreSQL persistence schema.
    """


# ============================================================================
# Database Session Dependency
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Provide a request-scoped SQLAlchemy session.

    The caller owns the transaction boundary and must commit successful
    operations explicitly. If an exception escapes the request operation,
    this dependency rolls back the current transaction before closing
    the session.

    Sessions are always closed to return pooled connections safely.
    """
    db = SessionLocal()

    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
