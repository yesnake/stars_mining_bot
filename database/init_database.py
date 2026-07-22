from sqlalchemy.ext.asyncio import AsyncEngine

from database import Base

from database.models import *


async def init_database(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)