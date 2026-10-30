"""Database engine, session and base class (SQLAlchemy 2.0)."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""


connect_args = {}
# SQLite fallback makes local/dev bring-up effortless without Postgres.
if settings.get_database_url().startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.get_database_url(),
    pool_pre_ping=True,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()