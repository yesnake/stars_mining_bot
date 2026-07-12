from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user_keyboards import get_mining_keyboard, get_start_miner_keyboard
from bot.services.botohub import send_task_status

from database.repositories.user_repositories import (
    get_or_create_user,
    get_referrals_count,
    get_total_balance,
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


@router.callback_query(F.data == "refresh_miner")
async def refresh_miner_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.clear()

    user_id = callback.from_user.id

    user = await get_or_create_user(session, user_id)

    await callback.message.delete()

    active_referrals_count = await get_referrals_count(session, user.id)
    total_balance = await get_total_balance(session, user.id)

    if user.is_mining:
        text = (
            "🟢 <b>ГЕНЕРАТОР РАБОТАЕТ</b>\n\n"
            f"› 💰 Баланс: <b>{total_balance:.4f} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{user.mining_per_hour:.2f} ⭐/час</b>\n"
            f"› 👥 Рефералов: <b>{active_referrals_count}</b>\n\n"
            "<blockquote>🚀 Генератор создает ⭐ прямо сейчас!</blockquote>"
        )
        await callback.message.answer(text, reply_markup=get_mining_keyboard())
    else:
        text = (
            "🔴 <b>ГЕНЕРАТОР ОСТАНОВЛЕН</b>\n\n"
            f"› 💰 Баланс: <b>{total_balance:.4f} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{user.mining_per_hour:.2f} ⭐/час</b>\n"
            f"› 👥 Активных рефералов: <b>{active_referrals_count}</b>\n\n"
            f"<b>Нажми на кнопку ниже, чтобы запустить генератор!</b>\n\n"
            "<blockquote>⚠️ Пока генератор выключен, ⭐ не начисляются.</blockquote>"
        )
        await callback.message.answer(text, reply_markup=get_start_miner_keyboard())
