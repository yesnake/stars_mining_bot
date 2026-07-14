import logging
from typing import Any, AsyncGenerator
from contextlib import asynccontextmanager

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


class ErrorHandler:
    @staticmethod
    async def handle_user_error(
        bot: Bot,
        user_id: int,
        error: Exception,
        context: str = "operation",
    ) -> None:
        logger.error(
            f"Error during {context} for user {user_id}: {error}", exc_info=True
        )
        try:
            await bot.send_message(
                user_id,
                "⚠️ Произошла ошибка. Попробуйте позже или обратитесь в поддержку.",
            )
        except Exception as notify_error:
            logger.error(f"Failed to notify user {user_id}: {notify_error}")

    @staticmethod
    async def handle_critical_error(error: Exception, context: str = "system") -> None:
        logger.critical(f"Critical error in {context}: {error}", exc_info=True)


@asynccontextmanager
async def safe_session(
    sessionmaker: async_sessionmaker,
) -> AsyncGenerator[AsyncSession, None]:
    session = sessionmaker()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


def format_balance(value: Any) -> str:
    try:
        return f"{float(value):.4f}"
    except (ValueError, TypeError):
        return "0.0000"


def format_speed(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "0.00"


def get_boost_status_line(boost_active: bool) -> str:
    return "› 🚀 Буст x2 <b>активирован</b>\n\n" if boost_active else ""
