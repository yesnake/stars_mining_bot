from decimal import Decimal, InvalidOperation

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user_keyboards import (
    get_back_to_miner_keyboard,
)
from bot.states.withdraw import WithdrawStates
from bot.utils import (
    format_balance,
    validate_withdraw_amount,
    normalize_username,
)

from database.repositories.user_repositories import (
    get_or_create_user,
    get_total_balance,
    mark_user_activity,
    create_withdraw_request,
)

from config_reader import config

router = Router()


@router.callback_query(F.data == "withdraw")
async def withdraw_handler(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await callback.answer()

    await state.clear()

    user_id = callback.from_user.id

    await get_or_create_user(session, user_id)
    await mark_user_activity(session, user_id)

    total_balance = await get_total_balance(session, user_id)

    text = (
        "💸 <b>ВЫВОД СРЕДСТВ</b>\n\n"
        f"› 💰 Доступно для вывода: <b>{format_balance(total_balance)} ⭐</b>\n\n"
        "<blockquote>Введи сумму, которую хочешь вывести (минимум 50⭐)</blockquote>"
    )

    await callback.message.edit_text(text, reply_markup=get_back_to_miner_keyboard())
    await state.set_state(WithdrawStates.waiting_for_amount)


@router.message(WithdrawStates.waiting_for_amount)
async def process_withdraw_amount(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    user_id = message.from_user.id

    await get_or_create_user(session, user_id)
    await mark_user_activity(session, user_id)

    total_balance = await get_total_balance(session, user_id)

    amount, error = validate_withdraw_amount(
        message.text,
        total_balance,
    )

    if error:
        await message.answer(
            error,
            reply_markup=get_back_to_miner_keyboard(),
        )
        return

    await state.update_data(withdraw_amount=str(amount))
    await state.set_state(WithdrawStates.waiting_for_username)

    text = (
        "💸 <b>ВЫВОД СРЕДСТВ</b>\n\n"
        f"› 💰 Сумма: <b>{format_balance(amount)} ⭐</b>\n\n"
        "<blockquote>Введи username получателя (например, @username)</blockquote>"
    )
    await message.answer(text, reply_markup=get_back_to_miner_keyboard())


@router.message(WithdrawStates.waiting_for_username)
async def process_withdraw_username(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    user_id = message.from_user.id
    await mark_user_activity(session, user_id)

    data = await state.get_data()
    raw_amount = data.get("withdraw_amount")

    if raw_amount is None:
        await state.clear()
        await message.answer(
            "❌ Сессия вывода истекла. Начни заново.",
            reply_markup=get_back_to_miner_keyboard(),
        )
        return

    username = normalize_username(message.text or "")
    if username is None:
        await message.answer(
            "❌ Некорректный username. Введи username получателя без пробелов "
            "(например, @username).",
            reply_markup=get_back_to_miner_keyboard(),
        )
        return

    try:
        amount = Decimal(raw_amount)
    except InvalidOperation:
        await state.clear()
        await message.answer(
            "❌ Ошибка при обработке суммы. Попробуй заново.",
            reply_markup=get_back_to_miner_keyboard(),
        )
        return

    withdraw_request = await create_withdraw_request(session, user_id, amount, username)

    if withdraw_request is None:
        await state.clear()
        await message.answer(
            "❌ Ошибка при создании заявки на вывод. Попробуй позже.",
            reply_markup=get_back_to_miner_keyboard(),
        )
        return

    await state.clear()

    text = (
        "✅ <b>ЗАЯВКА СОЗДАНА</b>\n\n"
        f"› 💰 Сумма вывода: <b>{format_balance(amount)} ⭐</b>\n"
        f"› 🆔 Номер заявки: <code>{withdraw_request.id}</code>\n"
        f"› 👤 Таргет username: @{username}\n\n"
        "<blockquote>⏳ Заявка будет обработана в течение 24 часов.\n"
        "Средства списаны с баланса.</blockquote>"
    )
    await message.answer(text, reply_markup=get_back_to_miner_keyboard())

    from bot.keyboards.admin_keyboards import get_withdraw_decision_keyboard

    admin_text = (
        f"💸 <b>НОВАЯ ЗАЯВКА НА ВЫВОД</b>\n\n"
        f"› 🆔 ID заявки: <code>{withdraw_request.id}</code>\n"
        f"› 👤 ID юзера: <code>{user_id}</code>\n"
        f"› 👤 Username: @{username}\n"
        f"› 💰 Сумма: <b>{format_balance(amount)} ⭐</b>\n"
        f"› 📅 Дата: {withdraw_request.created_at.strftime('%Y-%m-%d %H:%M')}"
    )

    sent_message = await message.bot.send_message(
        config.WITHDRAW_CHANNEL_ID,
        admin_text,
        reply_markup=get_withdraw_decision_keyboard(withdraw_request.id)
    )

    withdraw_request.message_id = sent_message.message_id
    session.add(withdraw_request)
    await session.commit()