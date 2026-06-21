from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database import Base


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Provide a new isolated in-memory database per test."""

    test_engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(bind=test_engine)

    with Session(
        test_engine,
        expire_on_commit=False,
    ) as database_session:
        yield database_session

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()