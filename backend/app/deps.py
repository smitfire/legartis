"""FastAPI dependency wiring for the request-scoped database session."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a session for the lifetime of one request.

    On any unhandled exception the session is rolled back before being
    returned to the pool, so a half-finished transaction can't poison the
    next caller that checks out the connection.
    """
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            # Roll back uncommitted work so the connection isn't poisoned for the pool.
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]
