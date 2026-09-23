"""
Database Engine and Session Configuration
Provides the SQLAlchemy Base model and the get_db dependency.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# SQLite requires check_same_thread=False for multi-threaded FastAPI workers
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields an independent database session per request,
    ensuring proper transaction boundaries and cleanup on completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
