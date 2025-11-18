from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.core.config import get_settings

settings = get_settings()

# Create engine; SQLite requires check_same_thread False for single-threaded apps when used across threads.
engine = create_engine(
    str(settings.DATABASE_URL),
    connect_args={"check_same_thread": False} if str(settings.DATABASE_URL).startswith("sqlite") else {},
    future=True,
)

# Enable foreign keys for SQLite
if str(settings.DATABASE_URL).startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


# PUBLIC_INTERFACE
@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
