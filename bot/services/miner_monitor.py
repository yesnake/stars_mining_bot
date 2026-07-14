import asyncio
import logging
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.keyboards.user_keyboards import (
    get_start_miner_keyboard,
    get_activate_boost_keyboard,
)
from bot.utils import format_balance, format_speed
from database.repositories.user_repositories import (
    get_inactive_users_for_warning,
    get_referrals_count,
    get_total_balance,
    mark_miner_warning_sent,
    stop_expired_miners,
    get_expired_boosts,
    deactivate_boost,
)

logger = logging.getLogger(__name__)


class MinerMonitor:
    def __init__(self, bot: Bot, sessionmaker: async_sessionmaker):
        self.bot = bot
        self.sessionmaker = sessionmaker
        self._task = None

    async def _utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    async def _notify_inactive_users(self, session) -> None:
        cutoff = (await self._utc_now()) - timedelta(hours=10)
        inactive_users = await get_inactive_users_for_warning(session, cutoff)

        for user in inactive_users:
            with suppress(Exception):
                total_balance = await get_total_balance(session, user.id)
                text = (
                    "⚠️ <b>ГЕНЕРАТОР ДАВНО НЕ РАБОТАЛ</b>\n\n"
                    f"› 💰 Баланс: <b>{format_balance(total_balance)} ⭐</b>\n\n"
                    "<b>Запусти генератор, чтобы получать ⭐</b>"
                )
                await self.bot.send_message(
                    user.id, text, reply_markup=get_start_miner_keyboard()
                )
                await mark_miner_warning_sent(session, user.id)

    async def _monitor_loop(self) -> None:
        while True:
            try:
                async with self.sessionmaker() as session:
                    expired_users = await stop_expired_miners(session)

                    for user in expired_users:
                        with suppress(Exception):
                            active_referrals_count = await get_referrals_count(
                                session, user.id
                            )
                            total_balance = await get_total_balance(session, user.id)
                            text = (
                                "❌ <b>ГЕНЕРАТОР ОСТАНОВЛЕН</b>\n\n"
                                f"› 💰 Баланс: <b>{format_balance(total_balance)} ⭐</b>\n"
                                f"› ⚡ Скорость: <b>{format_speed(user.mining_per_hour)} ⭐/час</b>\n"
                                f"› 👥 Активных рефералов: <b>{active_referrals_count}</b>\n\n"
                                "<blockquote>⚠️ Пока генератор выключен, ⭐ не начисляются.</blockquote>"
                                f"<b>⬇️Нажми на кнопку ниже, чтобы запустить генератор!</b>\n\n"
                            )
                            await self.bot.send_message(
                                user.id, text, reply_markup=get_start_miner_keyboard()
                            )

                    expired_boosts = await get_expired_boosts(session)

                    for user in expired_boosts:
                        with suppress(Exception):
                            await deactivate_boost(session, user.id)

                            active_referrals_count = await get_referrals_count(
                                session, user.id
                            )
                            total_balance = await get_total_balance(session, user.id)

                            text = (
                                "⏰ <b>БУСТ ЗАКОНЧИЛСЯ</b>\n\n"
                                "<blockquote>❗ Твоя скорость майнинга вернулась к обычной</blockquote>"
                            )
                            await self.bot.send_message(
                                user.id,
                                text,
                                reply_markup=get_activate_boost_keyboard(),
                            )

                    await self._notify_inactive_users(session)
            except Exception as e:
                logger.exception("Failed to stop expired miners: %s", e)

            await asyncio.sleep(60)

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._monitor_loop())
            logger.info("Miner monitor started")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
            logger.info("Miner monitor stopped")
