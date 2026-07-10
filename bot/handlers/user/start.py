from contextlib import suppress

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user_keyboards import get_start_miner_keyboard

from database.repositories.user_repositories import (
    check_referral,
    create_referral,
    get_or_create_user,
    get_user_by_id,
    increase_mining_speed,
    start_miner
)

router = Router()


@router.message(CommandStart())
async def start(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await state.clear()

    user_id = message.from_user.id

    is_new_user = await get_user_by_id(session, user_id) is None
    user = await get_or_create_user(session, user_id)

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
                            created = await create_referral(
                                session,
                                user.id,
                                referrer_id,
                            )

                            if created:
                                await increase_mining_speed(
                                    session,
                                    referrer_id,
                                    0.1,
                                )

    if user.is_mining:
        text = (
            "🟢 <b>ГЕНЕРАТОР РАБОТАЕТ</b>\n\n"
            f"› 💰 Баланс: <b>{user.balance} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{user.mining_per_hour} ⭐/час</b>\n"
            f"› 👥 Рефералов: <b>{user.balance}</b>\n\n"
            "<blockquote>🚀 Генератор создает ⭐ прямо сейчас!</blockquote>"
        )
        await message.answer(text)
    else:
        text = (
            "🔴 <b>ГЕНЕРАТОР ОСТАНОВЛЕН</b>\n\n"
            f"› 💰 Баланс: <b>{user.balance} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{user.mining_per_hour} ⭐/час</b>\n"
            f"› 👥 Рефералов: <b>{user.balance}</b>\n\n"
            "<blockquote>⚠️ Пока генератор выключен, ⭐ не начисляются.</blockquote>"
        )
        await message.answer(text, reply_markup=get_start_miner_keyboard(is_new_user))