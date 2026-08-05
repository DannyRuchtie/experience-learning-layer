"""SQLAlchemy engine and session management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ell.config import AppConfig

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

_engine: Engine = create_engine(
    AppConfig().database.url,
    pool_pre_ping=True,
)

_session_factory = sessionmaker(bind=_engine)


def get_engine() -> Engine:
    """Return the SQLAlchemy engine."""
    return _engine


def get_session() -> Session:
    """Return a new database session. Caller must close it."""
    return _session_factory()


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""
    pass
