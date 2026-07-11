from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update

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


async def get_referrals_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(Referral).where(Referral.user_id == user_id, Referral.is_active == True)
    )
    referrals = result.scalars().all()
    return len(referrals)


async def get_referral_by_referred_user_id(
    session: AsyncSession, user_id: int
) -> Referral | None:
    result = await session.execute(
        select(Referral).where(Referral.referral_id == user_id)
    )
    return result.scalar_one_or_none()


async def increase_mining_speed(
    session: AsyncSession, user_id: int, amount: float
) -> None:
    user = await get_or_create_user(session, user_id)
    user.mining_per_hour += Decimal(str(amount))

    try:
        await session.flush()
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()


async def decrease_mining_speed(
    session: AsyncSession, user_id: int, amount: float
) -> None:
    user = await get_or_create_user(session, user_id)
    user.mining_per_hour -= Decimal(str(amount))

    try:
        await session.flush()
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()


async def start_miner(session: AsyncSession, user_id: int) -> None:
    user = await get_or_create_user(session, user_id)
    user.is_mining = True
    user.mining_started_at = datetime.utcnow()

    referral = await get_referral_by_referred_user_id(session, user_id)
    if referral and not referral.is_active:
        referrer = await get_or_create_user(session, referral.user_id)
        await increase_mining_speed(session, referrer.id, 0.1)
        referral.is_active = True

    try:
        await session.flush()
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()


async def stop_miner(session: AsyncSession, user_id: int) -> bool:
    user = await get_or_create_user(session, user_id)

    if not user.is_mining:
        return False

    user.is_mining = False
    user.mining_started_at = None

    referral = await get_referral_by_referred_user_id(session, user_id)
    if referral and referral.is_active:
        referrer = await get_or_create_user(session, referral.user_id)
        await decrease_mining_speed(session, referrer.id, 0.1)
        referral.is_active = False

    try:
        await session.flush()
        await session.commit()
        await session.refresh(user)
    except IntegrityError:
        await session.rollback()
        return False

    return True


async def stop_expired_miners(session: AsyncSession):
    threshold = datetime.utcnow() - timedelta(minutes=1)

    result = await session.execute(
        select(User).where(
            User.is_mining.is_(True),
            User.mining_started_at.is_not(None),
            User.mining_started_at <= threshold,
        )
    )

    expired_users = result.scalars().all()

    if expired_users:
        for user in expired_users:
            referral = await get_referral_by_referred_user_id(session, user.id)
            if referral and referral.is_active:
                referrer = await get_or_create_user(session, referral.user_id)
                referrer.mining_per_hour -= Decimal("0.1")
                referral.is_active = False

        await session.execute(
            update(User)
            .where(User.id.in_([user.id for user in expired_users]))
            .values(
                is_mining=False,
                mining_started_at=None,
            )
        )

        await session.commit()

    return expired_users
