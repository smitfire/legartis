"""Async SQLAlchemy engine and session factory."""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, future=True)


@event.listens_for(engine.sync_engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_conn: object, _record: object) -> None:
    # SQLite ignores FK constraints by default; switch them on per-connection so
    # ON DELETE CASCADE works in tests. No-op on Postgres.
    module = type(dbapi_conn).__module__
    if "sqlite" in module:
        cursor = dbapi_conn.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False, autoflush=False
)
