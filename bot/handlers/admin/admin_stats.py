from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_keyboards import get_back_to_admin_keyboard
from bot.utils import format_balance
from database.repositories.admin_repositories import get_bot_stats

router = Router()


@router.callback_query(AdminFilter(), F.data == "admin_stats")
async def admin_stats_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    stats = await get_bot_stats(session)

    text = (
        "📊 <b>СТАТИСТИКА БОТА</b>\n\n"
        f"👥 Всего юзеров: <b>{stats['total_users']}</b>\n"
        f"⛏️ Активных майнеров: <b>{stats['active_miners']}</b>\n"
        f"💰 Общий баланс: <b>{format_balance(stats['total_balance'])} ⭐</b>\n"
        f"⏳ Ожидающих выводов: <b>{stats['pending_withdraws']}</b>\n"
        f"✅ Выведено всего: <b>{format_balance(stats['total_withdrawn'])} ⭐</b>\n"
        f"🚫 Заблокированных: <b>{stats['banned_users']}</b>\n"
    )

    await callback.message.edit_text(text, reply_markup=get_back_to_admin_keyboard())
