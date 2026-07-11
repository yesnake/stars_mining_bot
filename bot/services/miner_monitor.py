import asyncio
import logging
from contextlib import suppress

from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot.keyboards.user_keyboards import get_start_miner_keyboard
from database.repositories.user_repositories import get_referrals_count, stop_expired_miners

logger = logging.getLogger(__name__)


class MinerMonitor:
    def __init__(self, bot: Bot, sessionmaker: async_sessionmaker):
        self.bot = bot
        self.sessionmaker = sessionmaker
        self._task = None

    async def _monitor_loop(self) -> None:
        while True:
            try:
                async with self.sessionmaker() as session:
                    expired_users = await stop_expired_miners(session)

                    for user in expired_users:
                        with suppress(Exception):
                            active_referrals_count = await get_referrals_count(session, user.id)
                            text = (
                                "🔴 <b>ГЕНЕРАТОР ОСТАНОВЛЕН</b>\n\n"
                                f"› 💰 Баланс: <b>{user.balance} ⭐</b>\n"
                                f"› ⚡ Скорость: <b>{user.mining_per_hour} ⭐/час</b>\n"
                                f"› 👥 Активных рефералов: <b>{active_referrals_count}</b>\n\n"
                                f"<b>Нажми на кнопку ниже, чтобы запустить генератор!</b>\n\n"
                                "<blockquote>⚠️ Пока генератор выключен, ⭐ не начисляются.</blockquote>"
                            )
                            await self.bot.send_message(user.id, text, reply_markup=get_start_miner_keyboard())
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
