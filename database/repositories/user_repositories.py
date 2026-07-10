from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from database import User, Referral


async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
) -> User | None:
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


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def check_referral(
    session: AsyncSession, user_id: int, referrer_id: int
) -> Referral | None:
    result = await session.execute(
        select(Referral).where(
            Referral.user_id == referrer_id,
            Referral.referral_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_referral(
    session: AsyncSession, user_id: int, referrer_id: int
) -> None:
    referral = Referral(user_id=referrer_id, referral_id=user_id)
    session.add(referral)

    try:
        await session.flush()
        await session.commit()
        await session.refresh(referral)
    except IntegrityError:
        await session.rollback()
