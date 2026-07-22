from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, func, and_, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import (
    User,
    WithdrawRequest,
    TrackingLink,
    TrackingEvent,
    Broadcast,
    PromoCode,
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def get_bot_stats(session: AsyncSession) -> dict:
    total_users = await session.scalar(select(func.count()).select_from(User))

    active_miners = await session.scalar(
        select(func.count()).select_from(User).where(User.is_mining.is_(True))
    )

    total_balance = await session.scalar(
        select(func.sum(User.balance)).select_from(User)
    ) or Decimal("0")

    pending_withdraws = await session.scalar(
        select(func.count())
        .select_from(WithdrawRequest)
        .where(WithdrawRequest.status == "pending")
    )

    total_withdrawn = await session.scalar(
        select(func.sum(WithdrawRequest.amount))
        .select_from(WithdrawRequest)
        .where(WithdrawRequest.status == "completed")
    ) or Decimal("0")

    banned_users = await session.scalar(
        select(func.count()).select_from(User).where(User.is_banned.is_(True))
    )

    return {
        "total_users": total_users or 0,
        "active_miners": active_miners or 0,
        "total_balance": total_balance,
        "pending_withdraws": pending_withdraws or 0,
        "total_withdrawn": total_withdrawn,
        "banned_users": banned_users or 0,
    }


async def create_tracking_link(
    session: AsyncSession,
    link_code: str,
    name: str,
) -> TrackingLink | None:
    existing = await session.scalar(
        select(TrackingLink).where(TrackingLink.link_code == link_code)
    )

    if existing:
        return None

    link = TrackingLink(link_code=link_code, name=name)
    session.add(link)
    await session.commit()
    await session.refresh(link)

    return link


async def get_tracking_links(session: AsyncSession) -> list[TrackingLink]:
    result = await session.execute(
        select(TrackingLink).order_by(desc(TrackingLink.created_at))
    )
    return list(result.scalars().all())


async def get_tracking_link_by_code(
    session: AsyncSession,
    link_code: str,
) -> TrackingLink | None:
    return await session.scalar(
        select(TrackingLink).where(TrackingLink.link_code == link_code)
    )


async def track_event(
    session: AsyncSession,
    link_id: int,
    user_id: int,
    event_type: str,
) -> None:
    event = TrackingEvent(
        link_id=link_id,
        user_id=user_id,
        event_type=event_type,
    )
    session.add(event)

    link = await session.get(TrackingLink, link_id)
    if link:
        if event_type == "start":
            link.total_starts += 1
        elif event_type == "miner":
            link.total_miners += 1
        session.add(link)

    await session.commit()


async def get_all_users(
    session: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[User]:
    result = await session.execute(
        select(User).order_by(desc(User.last_activity_at)).limit(limit).offset(offset)
    )
    return list(result.scalars().all())


async def search_users(
    session: AsyncSession,
    user_id: int | None = None,
    is_banned: bool | None = None,
    is_mining: bool | None = None,
) -> list[User]:
    query = select(User)

    filters = []
    if user_id is not None:
        filters.append(User.id == user_id)
    if is_banned is not None:
        filters.append(User.is_banned.is_(is_banned))
    if is_mining is not None:
        filters.append(User.is_mining.is_(is_mining))

    if filters:
        query = query.where(and_(*filters))

    query = query.order_by(desc(User.last_activity_at)).limit(50)

    result = await session.execute(query)
    return list(result.scalars().all())


async def ban_user(session: AsyncSession, user_id: int) -> User | None:
    user = await session.get(User, user_id)
    if not user:
        return None

    user.is_banned = True
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def unban_user(session: AsyncSession, user_id: int) -> User | None:
    user = await session.get(User, user_id)
    if not user:
        return None

    user.is_banned = False
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def update_user_balance(
    session: AsyncSession,
    user_id: int,
    new_balance: Decimal,
) -> User | None:
    user = await session.get(User, user_id)
    if not user:
        return None

    user.balance = new_balance
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def get_user_activity(
    session: AsyncSession,
    user_id: int,
) -> dict:
    user = await session.get(User, user_id)
    if not user:
        return {}

    withdraws = await session.execute(
        select(WithdrawRequest)
        .where(WithdrawRequest.user_id == user_id)
        .order_by(desc(WithdrawRequest.created_at))
        .limit(10)
    )

    tracking_events = await session.execute(
        select(TrackingEvent)
        .where(TrackingEvent.user_id == user_id)
        .order_by(desc(TrackingEvent.created_at))
        .limit(10)
    )

    return {
        "user": user,
        "withdraws": list(withdraws.scalars().all()),
        "tracking_events": list(tracking_events.scalars().all()),
    }


async def create_broadcast(
    session: AsyncSession,
    text: str | None = None,
    media_type: str | None = None,
    media_file_id: str | None = None,
    caption: str | None = None,
    button_text: str | None = None,
    button_url: str | None = None,
    target_group: str = "all",
) -> Broadcast:
    broadcast = Broadcast(
        text=text,
        media_type=media_type,
        media_file_id=media_file_id,
        caption=caption,
        button_text=button_text,
        button_url=button_url,
        target_group=target_group,
    )
    session.add(broadcast)
    await session.commit()
    await session.refresh(broadcast)

    return broadcast


async def update_broadcast_stats(
    session: AsyncSession,
    broadcast_id: int,
    sent_count: int,
    failed_count: int,
) -> None:
    broadcast = await session.get(Broadcast, broadcast_id)
    if broadcast:
        broadcast.sent_count = sent_count
        broadcast.failed_count = failed_count
        broadcast.status = "completed"
        session.add(broadcast)
        await session.commit()


async def get_all_active_user_ids(session: AsyncSession) -> list[int]:
    result = await session.execute(select(User.id).where(User.is_banned.is_(False)))
    return list(result.scalars().all())


async def get_users_with_miner_on(session: AsyncSession) -> list[int]:
    result = await session.execute(
        select(User.id).where(
            User.is_banned.is_(False),
            User.is_mining.is_(True),
        )
    )
    return list(result.scalars().all())


async def get_users_with_miner_off(session: AsyncSession) -> list[int]:
    result = await session.execute(
        select(User.id).where(
            User.is_banned.is_(False),
            User.is_mining.is_(False),
        )
    )
    return list(result.scalars().all())


async def create_promocode(
    session: AsyncSession,
    code: str,
    activations: int,
    stars: Decimal,
) -> PromoCode | None:
    existing = await session.scalar(select(PromoCode).where(PromoCode.code == code))
    if existing:
        return None

    promocode = PromoCode(code=code, activations_left=activations, stars=stars)
    session.add(promocode)
    await session.commit()
    await session.refresh(promocode)
    return promocode
