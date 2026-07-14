from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user_keyboards import get_mining_keyboard, get_start_miner_keyboard
from bot.services.botohub import send_task_status, send_task_boost_status
from bot.utils import format_balance, format_speed, get_boost_status_line

from database.repositories.user_repositories import (
    get_or_create_user,
    get_referrals_count,
    get_total_balance,
    mark_user_activity,
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
    await mark_user_activity(session, user_id)

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
    await mark_user_activity(session, user_id)

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
    await mark_user_activity(session, user_id)

    await callback.message.delete()

    active_referrals_count = await get_referrals_count(session, user.id)
    total_balance = await get_total_balance(session, user.id)
    me = await callback.bot.get_me()

    boost_line = get_boost_status_line(user.boost_active)

    if user.is_mining:
        text = (
            "🟢 <b>ГЕНЕРАТОР РАБОТАЕТ</b>\n\n"
            f"› 💰 Баланс: <b>{format_balance(total_balance)} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{format_speed(user.mining_per_hour)} ⭐/час</b>\n"
            f"› 👥 Активных рефералов: <b>{active_referrals_count}</b>\n"
            f"{boost_line}"
            f"<blockquote>🔗 Твоя реф. ссылка: <code>https://t.me/{me.username}?start=r_{callback.from_user.id}</code>\n\n"
            "🎁 Ты будешь получать +0.1⭐/час за каждого друга с активным генератором</blockquote>"
        )
        await callback.message.answer(text, reply_markup=get_mining_keyboard(me.username, user_id))
    else:
        text = (
            "❌ <b>ГЕНЕРАТОР ОСТАНОВЛЕН</b>\n\n"
            f"› 💰 Баланс: <b>{format_balance(total_balance)} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{format_speed(user.mining_per_hour)} ⭐/час</b>\n"
            f"› 👥 Активных рефералов: <b>{active_referrals_count}</b>\n\n"
            "<blockquote>⚠️ Пока генератор выключен, ⭐ не начисляются.</blockquote>"
            f"<b>⬇️Нажми на кнопку ниже, чтобы запустить генератор!</b>\n\n"
        )
        await callback.message.answer(text, reply_markup=get_start_miner_keyboard())


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
        await callback.answer("🚀 Сначала запусти генератор!", show_alert=True)
        return

    if user.boost_active:
        await callback.answer("⚡ У тебя уже активирован буст!", show_alert=True)
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

    await callback.message.delete()

    await send_task_boost_status(session, callback, user_id)
