import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


# ============================================================================
# Database Configuration
# ============================================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://payguard:payguard@localhost:5432/payguard",
)


# ============================================================================
# SQLAlchemy Engine
# ============================================================================

engine = create_engine(
    DATABASE_URL,
    future=True,
    pool_pre_ping=True,
)


# ============================================================================
# Session Factory
# ============================================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


# ============================================================================
# Declarative Base
# ============================================================================

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy database models.

    Domain/API models remain defined separately in app.models.
    SQLAlchemy models will inherit from this class and represent the
    PostgreSQL persistence schema.
    """

    pass


# ============================================================================
# Database Session Dependency
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    Provide a database session for an application operation.

    The session is committed by the caller when the operation succeeds.
    If an exception occurs before the caller finishes the operation,
    the session is rolled back and then closed.

    This function is designed to be used as a FastAPI dependency once
    PostgreSQL-backed repositories are introduced.
    """

    db = SessionLocal()

    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()