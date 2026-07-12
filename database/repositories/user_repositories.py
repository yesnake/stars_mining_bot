from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import Referral, User


async def get_or_create_user(
    session: AsyncSession,
    user_id: int,
) -> User:
    user = await session.get(User, user_id)
    if user is not None:
        return user

    user = User(id=user_id)
    session.add(user)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        user = await session.get(User, user_id)
        if user is None:
            raise

    return user


async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> User | None:
    return await session.get(User, user_id)


async def check_referral(
    session: AsyncSession,
    user_id: int,
    referrer_id: int,
) -> Referral | None:
    result = await session.execute(
        select(Referral).where(
            Referral.user_id == referrer_id,
            Referral.referral_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_referral(
    session: AsyncSession,
    user_id: int,
    referrer_id: int,
) -> Referral | None:
    referral = Referral(
        user_id=referrer_id,
        referral_id=user_id,
    )
    session.add(referral)

    await session.commit()

    return referral


async def get_referrals_count(
    session: AsyncSession,
    user_id: int,
) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(Referral)
        .where(
            Referral.user_id == user_id,
            Referral.is_active.is_(True),
        )
    )
    return result.scalar_one()


async def get_referral_by_referred_user_id(
    session: AsyncSession,
    user_id: int,
) -> Referral | None:
    result = await session.execute(
        select(Referral).where(
            Referral.referral_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def increase_mining_speed(
    session: AsyncSession,
    user_id: int,
    amount: Decimal,
) -> None:
    user = await get_or_create_user(session, user_id)
    user.mining_per_hour += amount
    await session.commit()


async def decrease_mining_speed(
    session: AsyncSession,
    user_id: int,
    amount: Decimal,
) -> None:
    user = await get_or_create_user(session, user_id)
    user.mining_per_hour = max(
        Decimal("0"),
        user.mining_per_hour - amount,
    )
    await session.commit()


async def get_currently_mined(user: User) -> Decimal:
    if not user.is_mining or user.mining_started_at is None or user.mining_speed_snapshot is None:
        return Decimal("0")

    elapsed_seconds = (datetime.now() - user.mining_started_at).total_seconds()
    stars_per_second = user.mining_speed_snapshot / Decimal("3600")
    return Decimal(str(elapsed_seconds)) * stars_per_second


async def get_total_balance(session: AsyncSession, user_id: int) -> Decimal:
    user = await get_or_create_user(session, user_id)
    return user.balance + await get_currently_mined(user)


async def start_miner(
    session: AsyncSession,
    user_id: int,
) -> None:
    user = await get_or_create_user(session, user_id)

    if user.is_mining:
        return

    user.is_mining = True
    user.mining_started_at = datetime.now()
    user.mining_speed_snapshot = user.mining_per_hour

    referral = await get_referral_by_referred_user_id(session, user_id)
    if referral is not None and not referral.is_active:
        referrer = await get_or_create_user(session, referral.user_id)
        referrer.mining_per_hour += Decimal("0.1")
        referral.is_active = True

    await session.commit()


async def stop_expired_miners(
    session: AsyncSession,
) -> list[User]:
    threshold = datetime.now() - timedelta(minutes=1)

    result = await session.execute(
        select(User).where(
            User.is_mining.is_(True),
            User.mining_started_at.is_not(None),
            User.mining_started_at <= threshold,
        )
    )

    expired_users = result.scalars().all()

    if not expired_users:
        return []

    expired_ids = [user.id for user in expired_users]

    result = await session.execute(
        select(Referral).where(
            Referral.referral_id.in_(expired_ids),
            Referral.is_active.is_(True),
        )
    )

    active_referrals = result.scalars().all()

    if active_referrals:
        referrer_ids = list({ref.user_id for ref in active_referrals})

        result = await session.execute(select(User).where(User.id.in_(referrer_ids)))

        referrers = {user.id: user for user in result.scalars().all()}

        for referral in active_referrals:
            referrer = referrers.get(referral.user_id)
            if referrer is not None:
                referrer.mining_per_hour = max(
                    Decimal("0"),
                    referrer.mining_per_hour - Decimal("0.1"),
                )
            referral.is_active = False

    for user in expired_users:
        mined_amount = await get_currently_mined(user)
        user.balance += mined_amount
        user.is_mining = False
        user.mining_started_at = None
        user.mining_speed_snapshot = None

    await session.commit()

    return expired_users
