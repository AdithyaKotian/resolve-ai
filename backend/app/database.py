from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATA_DIR, settings


DATA_DIR.mkdir(parents=True, exist_ok=True)

sqlite_connect_arguments = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=sqlite_connect_arguments,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class inherited by all SQLAlchemy database models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """Provide one database session and always close it afterward."""

    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()


def check_database_connection() -> None:
    """Execute a small query to confirm that the database is reachable."""

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

def init_database() -> None:
    """Create all database tables that do not already exist."""

    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)