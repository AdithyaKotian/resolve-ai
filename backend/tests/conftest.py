from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database import Base


@pytest.fixture()
def test_engine() -> Generator[
    Engine,
    None,
    None,
]:
    """Provide a shared in-memory engine per test."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=engine)

    yield engine

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session_factory(
    test_engine: Engine,
) -> sessionmaker:
    """Provide a session factory for graph nodes."""

    return sessionmaker(
        bind=test_engine,
        class_=Session,
        expire_on_commit=False,
    )


@pytest.fixture()
def db_session(
    db_session_factory: sessionmaker,
) -> Generator[Session, None, None]:
    """Provide one isolated database session."""

    with db_session_factory() as database_session:
        yield database_session