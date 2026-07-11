from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.botohub import send_task_status

from database.repositories.user_repositories import (
    get_or_create_user,
)

router = Router()


@router.callback_query(F.data == "start_miner")
async def start_miner_handler(
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


@router.callback_query(F.data.startswith("check_tasks:"))
async def check_tasks_handler(
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
