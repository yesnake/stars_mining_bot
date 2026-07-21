from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.user_repositories import (
    mark_user_activity,
    get_or_create_user,
)
from bot.services.botohub import send_task_boost_status
from bot.utils import safe_callback_answer, safe_delete_callback_message

router = Router()


@router.callback_query(F.data == "boost_miner")
async def boost_miner_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:

    await state.clear()

    user_id = callback.from_user.id

    user = await get_or_create_user(session, user_id)
    await mark_user_activity(session, user_id)

    if not user.is_mining:
        await safe_callback_answer(
            callback, text="🚀 Сначала запусти генератор!", show_alert=True
        )
        return

    if user.boost_active:
        await safe_callback_answer(
            callback, text="⚡ У тебя уже активирован буст!", show_alert=True
        )
        return

    await send_task_boost_status(session, callback, user_id)


@router.callback_query(F.data.startswith("check_boost_tasks:"))
async def check_boost_tasks_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:

    await state.clear()

    user_id = callback.from_user.id
    user = await get_or_create_user(session, user_id)
    await mark_user_activity(session, user_id)

    await safe_delete_callback_message(callback)

    await send_task_boost_status(session, callback, user_id)
