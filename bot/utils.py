import logging
from typing import Any, AsyncGenerator, Tuple, Optional
from contextlib import asynccontextmanager
from decimal import Decimal, InvalidOperation

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

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


async def safe_callback_answer(
    callback: CallbackQuery,
    **kwargs: Any,
) -> None:
    try:
        await callback.answer(**kwargs)
    except TelegramBadRequest as error:
        if "query is too old" not in str(error).lower():
            raise


async def safe_delete_callback_message(callback: CallbackQuery) -> None:
    if callback.message is None:
        return

    try:
        await callback.message.delete()
    except AttributeError:
        try:
            await callback.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
            )
        except Exception:
            pass
    except Exception:
        pass


def format_speed(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "0.00"


def get_boost_status_line(boost_active: bool) -> str:
    return "› 🚀 Буст x2 <b>активирован</b>\n\n" if boost_active else ""


def validate_withdraw_amount(
    text: str,
    total_balance: Decimal,
    min_amount: Decimal = Decimal("50"),
) -> Tuple[Optional[Decimal], Optional[str]]:
    try:
        amount = Decimal(text.strip().replace(",", "."))
    except (InvalidOperation, ValueError, AttributeError):
        return None, "❌ Неверный формат суммы. Введи число (например: 10 или 10.5)"

    if amount < min_amount:
        return None, f"❌ Минимальная сумма для вывода — {min_amount}⭐"

    if amount > total_balance:
        return (
            None,
            f"❌ Недостаточно средств. Доступно: {format_balance(total_balance)} ⭐",
        )

    return amount, None


def normalize_username(raw: str) -> str | None:
    text = raw.strip()
    try:
        if text.startswith("@"):
            text = text[1:]

        if not (3 <= len(text) <= 32):
            return None
        if not all(c.isalnum() or c == "_" for c in text):
            return None
        if not text[0].isalpha():
            return None
    except Exception:
        return None

    return text
