from contextlib import suppress

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user_keyboards import get_mining_keyboard, get_start_miner_keyboard
from bot.utils import format_balance, format_speed, get_boost_status_line

from database.repositories.user_repositories import (
    check_referral,
    create_referral,
    get_or_create_user,
    get_referrals_count,
    get_total_balance,
    get_user_by_id,
    mark_user_activity,
)

router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await state.clear()

    user_id = message.from_user.id

    is_new_user = await get_user_by_id(session, user_id) is None
    user = await get_or_create_user(session, user_id)
    await mark_user_activity(session, user_id)

    if is_new_user and command.args:
        with suppress(ValueError):
            option, value = command.args.split("_", 1)

            if option == "r":
                referrer_id = int(value)

                if referrer_id != user.id:
                    referrer = await get_user_by_id(session, referrer_id)

                    if referrer:
                        referral = await check_referral(
                            session,
                            user.id,
                            referrer_id,
                        )

                        if referral is None:
                            await create_referral(
                                session,
                                user.id,
                                referrer_id,
                            )

    active_referrals_count = await get_referrals_count(session, user.id)

    total_balance = await get_total_balance(session, user.id)
    me = await message.bot.get_me()

    boost_line = get_boost_status_line(user.boost_active)

    if user.is_mining:
        text = (
            "🟢 <b>ГЕНЕРАТОР РАБОТАЕТ</b>\n\n"
            f"› 💰 Баланс: <b>{format_balance(total_balance)} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{format_speed(user.mining_per_hour)} ⭐/час</b>\n"
            f"› 👥 Активных рефералов: <b>{active_referrals_count}</b>\n"
            f"{boost_line}"
            f"<blockquote>🔗 Твоя реф. ссылка: <code>https://t.me/{me.username}?start=r_{message.from_user.id}</code>\n\n"
            "🎁 Ты будешь получать +0.1⭐/час за каждого друга с активным генератором</blockquote>"
        )
        await message.answer(text, reply_markup=get_mining_keyboard(me.username, user_id))
    else:
        text = (
            "❌ <b>ГЕНЕРАТОР ОСТАНОВЛЕН</b>\n\n"
            f"› 💰 Баланс: <b>{format_balance(total_balance)} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{format_speed(user.mining_per_hour)} ⭐/час</b>\n"
            f"› 👥 Активных рефералов: <b>{active_referrals_count}</b>\n\n"
            "<blockquote>⚠️ Пока генератор выключен, ⭐ не начисляются.</blockquote>"
            f"<b>⬇️Нажми на кнопку ниже, чтобы запустить генератор!</b>\n\n"
        )
        await message.answer(text, reply_markup=get_start_miner_keyboard())
