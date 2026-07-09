from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database import User


async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
) -> User:
    user = await session.get(User, user_id)
    if user:
        return user

    user = User(id=user_id)
    session.add(user)

    try:
        await session.flush()
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()
        user = await session.get(User, user_id)

    return user
