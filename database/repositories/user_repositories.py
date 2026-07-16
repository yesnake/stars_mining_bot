from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database import Referral, User, WithdrawRequest


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

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

    await session.refresh(user)
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

    try:
        await session.commit()
        await session.refresh(referral)
    except IntegrityError:
        await session.rollback()
        return None

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


async def get_inactive_users_for_warning(
    session: AsyncSession,
    cutoff: datetime,
) -> list[User]:
    result = await session.execute(
        select(User).where(
            User.is_mining.is_(False),
            User.last_activity_at.is_not(None),
            User.last_activity_at <= cutoff,
            User.last_miner_warning_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def increase_mining_speed(
    session: AsyncSession,
    user_id: int,
    amount: Decimal,
) -> None:
    user = await get_or_create_user(session, user_id)
    user.mining_per_hour += amount
    session.add(user)
    await session.commit()
    await session.refresh(user)


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
    session.add(user)
    await session.commit()
    await session.refresh(user)


async def get_currently_mined(user: User) -> Decimal:
    if (
        not user.is_mining
        or user.mining_started_at is None
        or user.mining_speed_snapshot is None
    ):
        return Decimal("0")

    now = _now_utc()
    mining_start = user.mining_started_at
    if mining_start.tzinfo is None:
        mining_start = mining_start.replace(tzinfo=timezone.utc)

    elapsed_seconds = (now - mining_start).total_seconds()
    if elapsed_seconds < 0:
        return Decimal("0")

    elapsed_seconds = min(elapsed_seconds, 3600)

    stars_per_second = user.mining_speed_snapshot / Decimal("3600")
    return Decimal(str(elapsed_seconds)) * stars_per_second


async def get_total_balance(session: AsyncSession, user_id: int) -> Decimal:
    user = await get_or_create_user(session, user_id)
    return user.balance + await get_currently_mined(user)


async def mark_user_activity(
    session: AsyncSession,
    user_id: int,
) -> None:
    user = await get_or_create_user(session, user_id)
    user.last_activity_at = _now_utc()
    user.last_miner_warning_at = None
    session.add(user)
    await session.commit()
    await session.refresh(user)


async def mark_miner_warning_sent(
    session: AsyncSession,
    user_id: int,
) -> None:
    user = await get_or_create_user(session, user_id)
    user.last_miner_warning_at = _now_utc()
    session.add(user)
    await session.commit()
    await session.refresh(user)


async def start_miner(
    session: AsyncSession,
    user_id: int,
) -> None:
    user = await get_or_create_user(session, user_id)

    if user.is_mining:
        return

    user.is_mining = True
    user.mining_started_at = _now_utc()
    user.mining_speed_snapshot = user.mining_per_hour
    user.last_activity_at = _now_utc()
    user.last_miner_warning_at = None

    referral = await get_referral_by_referred_user_id(session, user_id)
    if referral is not None and not referral.is_active:
        referrer = await get_or_create_user(session, referral.user_id)
        referrer.mining_per_hour += Decimal("0.1")
        referral.is_active = True

    await session.commit()


async def stop_expired_miners(
    session: AsyncSession,
) -> list[User]:
    threshold = _now_utc() - timedelta(hours=1)

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


async def activate_boost(
    session: AsyncSession,
    user_id: int,
) -> None:
    user = await get_or_create_user(session, user_id)

    user.mining_per_hour *= Decimal("2")
    user.boost_active = True
    user.boost_expires_at = _now_utc() + timedelta(hours=1)

    if user.is_mining and user.mining_speed_snapshot is not None:
        user.mining_speed_snapshot *= Decimal("2")

    session.add(user)
    await session.commit()
    await session.refresh(user)


async def get_expired_boosts(
    session: AsyncSession,
) -> list[User]:
    now = _now_utc()

    result = await session.execute(
        select(User).where(
            User.boost_active.is_(True),
            User.boost_expires_at.is_not(None),
            User.boost_expires_at <= now,
        )
    )

    return list(result.scalars().all())


async def deactivate_boost(
    session: AsyncSession,
    user_id: int,
) -> None:
    user = await get_or_create_user(session, user_id)

    user.mining_per_hour /= Decimal("2")
    user.boost_active = False
    user.boost_expires_at = None

    if user.is_mining and user.mining_speed_snapshot is not None:
        user.mining_speed_snapshot /= Decimal("2")

    session.add(user)
    await session.commit()
    await session.refresh(user)

async def create_withdraw_request(
    session: AsyncSession,
    user_id: int,
    amount: Decimal,
    username: str,
) -> WithdrawRequest | None:
    user = await session.get(User, user_id)
    if user is None:
        return None

    currently_mined = await get_currently_mined(user)
    total_balance = user.balance + currently_mined

    if amount > total_balance:
        return None

    if user.is_mining and currently_mined > Decimal("0"):
        user.balance += currently_mined
        user.mining_started_at = _now_utc()

    user.balance -= amount

    withdraw_request = WithdrawRequest(
        user_id=user_id,
        username=username,
        amount=amount,
        status="pending",
    )

    session.add(user)
    session.add(withdraw_request)

    await session.commit()
    await session.refresh(withdraw_request)

    return withdraw_request


async def get_pending_withdraws(
    session: AsyncSession,
) -> list[WithdrawRequest]:
    result = await session.execute(
        select(WithdrawRequest).where(
            WithdrawRequest.status == "pending",
        )
    )
    return list(result.scalars().all())


async def get_user_withdraws(
    session: AsyncSession,
    user_id: int,
) -> list[WithdrawRequest]:
    result = await session.execute(
        select(WithdrawRequest)
        .where(WithdrawRequest.user_id == user_id)
        .order_by(WithdrawRequest.created_at.desc())
    )
    return list(result.scalars().all())


async def approve_withdraw(
    session: AsyncSession,
    withdraw_id: int,
) -> WithdrawRequest | None:
    withdraw_request = await session.get(WithdrawRequest, withdraw_id)
    if withdraw_request is None or withdraw_request.status != "pending":
        return None

    withdraw_request.status = "completed"
    withdraw_request.processed_at = _now_utc()

    session.add(withdraw_request)
    await session.commit()
    await session.refresh(withdraw_request)

    return withdraw_request


async def reject_withdraw(
    session: AsyncSession,
    withdraw_id: int,
) -> WithdrawRequest | None:
    withdraw_request = await session.get(WithdrawRequest, withdraw_id)
    if withdraw_request is None or withdraw_request.status != "pending":
        return None

    user = await session.get(User, withdraw_request.user_id)
    if user is not None:
        user.balance += withdraw_request.amount
        session.add(user)

    withdraw_request.status = "rejected"
    withdraw_request.processed_at = _now_utc()

    session.add(withdraw_request)
    await session.commit()
    await session.refresh(withdraw_request)

    return withdraw_request
