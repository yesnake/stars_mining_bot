from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.botohub import send_task_status

from database.repositories.user_repositories import get_or_create_user

router = Router()


@router.callback_query(F.data.startswith("start_miner:"))
async def start_miner(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.clear()

    user_id = callback.from_user.id

    is_new_user = callback.data.split(":")[1] == "True"
    user = await get_or_create_user(session, user_id)

    await callback.message.delete()

    if is_new_user:
        text = (
            "🟢 <b>ГЕНЕРАТОР РАБОТАЕТ</b>\n\n"
            f"› 💰 Баланс: <b>{user.balance} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{user.mining_per_hour} ⭐/час</b>\n"
            f"› 👥 Рефералов: <b>{user.balance}</b>\n\n"
            "<blockquote>🚀 Генератор создает ⭐ прямо сейчас!</blockquote>"
        )
        await callback.message.answer(text)
    else:
        await send_task_status(session, callback, user_id)


@router.callback_query(F.data.startswith("check_tasks:"))
async def check_tasks(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.clear()

    user_id = callback.from_user.id
    user = await get_or_create_user(session, user_id)

    await callback.message.delete()

    await send_task_status(session, callback, user_id)
