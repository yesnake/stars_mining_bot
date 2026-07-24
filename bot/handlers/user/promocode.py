from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.utils import format_balance, safe_callback_answer, safe_delete_callback_message
from bot.keyboards.user_keyboards import get_back_to_miner_keyboard
from database.repositories.user_repositories import (
    award_promocode,
    get_or_create_user,
    get_promocode_by_code,
    has_user_used_promocode,
    mark_user_activity,
)

router = Router()


async def _activate_promocode(
    callback: CallbackQuery,
    session: AsyncSession,
    code: str,
    user_id: int,
) -> None:
    answered = False

    async def answer_once(text: str | None = None, *, show_alert: bool = False) -> None:
        nonlocal answered
        if answered:
            return
        answered = True
        if text is None:
            await safe_callback_answer(callback)
        else:
            await safe_callback_answer(callback, text=text, show_alert=show_alert)

    promocode = await get_promocode_by_code(session, code)
    if promocode is None:
        await answer_once("❌ Промокод не найден", show_alert=True)
        return

    if await has_user_used_promocode(session, promocode.id, user_id):
        await answer_once("❌ Вы уже использовали этот промокод", show_alert=True)
        return

    await get_or_create_user(session, user_id)
    await mark_user_activity(session, user_id)

    try:
        ok = await award_promocode(session, promocode.id, user_id, promocode.stars)
        if not ok:
            await answer_once("❌ Этот промокод уже исчерпан", show_alert=True)
            return
    except Exception:
        await answer_once(
            "⚠️ Не удалось активировать промокод. Попробуй позже",
            show_alert=True,
        )
        return

    await answer_once()
    await safe_delete_callback_message(callback)
    await callback.message.answer(
        f"✅ Ты успешно получил {format_balance(promocode.stars)} ⭐!", reply_markup=get_back_to_miner_keyboard()
    )


@router.callback_query(F.data.startswith("use_promocode:"))
async def use_promocode_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    parts = callback.data.split(":", 1)
    if len(parts) != 2:
        await safe_callback_answer(
            callback, text="❌ Неверный промокод", show_alert=True
        )
        return

    await _activate_promocode(callback, session, parts[1], callback.from_user.id)


@router.callback_query(F.data.startswith("check_promocode_tasks:"))
async def check_promocode_tasks_handler(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        await safe_callback_answer(
            callback,
            text="❌ Неверный формат проверки",
            show_alert=True,
        )
        return

    code = parts[1]
    try:
        user_id = int(parts[2])
    except ValueError:
        user_id = callback.from_user.id

    await _activate_promocode(callback, session, code, user_id)
