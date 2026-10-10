"""SQLAlchemy engine and transactional session helpers."""

from contextlib import contextmanager
import os
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from Backend.db.models import Base


DB_GENERATION: int = 0
_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def db_generation() -> int:
    """Return the generation of the current database engine."""
    return DB_GENERATION


def get_database_url() -> str:
    """Return the configured database URL or the local workspace default."""
    default_path = Path(__file__).resolve().parents[2] / "Data" / "workspace" / "onboarding.db"
    return os.environ.get("DATABASE_URL", f"sqlite:///{default_path}")


def init_db(url: str | None = None, create_tables: bool = False) -> None:
    """Initialize a database engine and optionally create the mapped tables."""
    global DB_GENERATION, _engine, _session_factory

    if _engine is not None:
        _engine.dispose()

    database_url = url or get_database_url()
    engine_options: dict = {}
    if database_url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
        if database_url == "sqlite://" or ":memory:" in database_url:
            engine_options["poolclass"] = StaticPool
        elif database_url.startswith("sqlite:///"):
            Path(database_url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)

    _engine = create_engine(database_url, **engine_options)
    _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)
    DB_GENERATION += 1
    if create_tables:
        Base.metadata.create_all(_engine)


def get_engine() -> Engine:
    """Return the initialized SQLAlchemy engine."""
    if _engine is None:
        init_db()
    assert _engine is not None
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the initialized SQLAlchemy session factory."""
    if _session_factory is None:
        init_db()
    assert _session_factory is not None
    return _session_factory


@contextmanager
def session_scope() -> Iterator[Session]:
    """Provide a committing transactional session."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
