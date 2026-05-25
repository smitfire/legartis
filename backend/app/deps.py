from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            # Roll back uncommitted work so the connection isn't poisoned for the pool.
            await session.rollback()
            raise


DbSession = Annotated[AsyncSession, Depends(get_db)]
