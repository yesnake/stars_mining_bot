import json
from decimal import Decimal, InvalidOperation

from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_keyboards import get_back_to_admin_keyboard
from bot.keyboards.admin_keyboards import get_promocode_broadcast_markup
from bot.states.admin import AdminStates
from bot.utils import format_balance

from database.repositories.admin_repositories import (
    create_promocode,
    get_all_active_user_ids,
)

router = Router()


@router.callback_query(AdminFilter(), F.data == "admin_create_promocode")
async def admin_create_promocode_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    text = (
        "🎟️ <b>СОЗДАНИЕ ПРОМОКОДА</b>\n\n"
        "Отправь код промокода (например: SUMMER2026)."
    )

    await callback.message.edit_text(text, reply_markup=get_back_to_admin_keyboard())
    await state.set_state(AdminStates.waiting_for_promocode_code)


@router.message(AdminFilter(), AdminStates.waiting_for_promocode_code)
async def process_promocode_code(message: Message, state: FSMContext) -> None:
    code = (message.text or "").strip()
    if not code:
        await message.answer(
            "❌ Код не может быть пустым.", reply_markup=get_back_to_admin_keyboard()
        )
        return

    await state.update_data(promocode_code=code)
    await message.answer(
        "🎟️ Введите количество активаций (число).",
        reply_markup=get_back_to_admin_keyboard(),
    )
    await state.set_state(AdminStates.waiting_for_promocode_activations)


@router.message(AdminFilter(), AdminStates.waiting_for_promocode_activations)
async def process_promocode_activations(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    try:
        activations = int(text)
    except (ValueError, TypeError):
        await message.answer(
            "❌ Неверный формат. Введите целое число активаций.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        return

    if activations <= 0:
        await message.answer(
            "❌ Количество активаций должно быть больше 0.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        return

    await state.update_data(promocode_activations=activations)
    await message.answer(
        "🎟️ Введите количество звезд, которое даёт промокод (например: 5 или 1.5).",
        reply_markup=get_back_to_admin_keyboard(),
    )
    await state.set_state(AdminStates.waiting_for_promocode_amount)


@router.message(AdminFilter(), AdminStates.waiting_for_promocode_amount)
async def process_promocode_amount(
    message: Message, session: AsyncSession, state: FSMContext
) -> None:
    data = await state.get_data()
    code = data.get("promocode_code")
    activations = data.get("promocode_activations")

    text = (message.text or "").strip()
    try:
        amount = Decimal(text.replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        await message.answer(
            "❌ Неверный формат. Введите число (например: 5 или 1.5).",
            reply_markup=get_back_to_admin_keyboard(),
        )
        return

    if amount <= 0:
        await message.answer(
            "❌ Количество звезд должно быть больше 0.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        return

    promocode = await create_promocode(session, code, activations, amount)
    if promocode is None:
        await message.answer(
            "❌ Промокод с таким кодом уже существует.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        await state.clear()
        return

    await state.clear()

    status_message = await message.answer(
        "📢 <b>РАССЫЛКА ПРОМОКОДА...</b>\n\n" "Отправлено: 0\n" "Ошибок: 0",
        reply_markup=get_back_to_admin_keyboard(),
    )

    user_ids = await get_all_active_user_ids(session)

    sent_count = 0
    failed_count = 0

    keyboard = get_promocode_broadcast_markup(code)

    broadcast_text = (
        f"🎁 <b>ПРОМОКОД НА {activations * amount}⭐: {code}</b>\n\n"
        f"🚀 Всего активаций: {activations}\n"
        f"⭐ Звезд за активацию: {format_balance(amount)}\n\n"
        "❤️ Нажми кнопку ниже, чтобы получить награду."
    )

    for i, user_id in enumerate(user_ids):
        try:
            await message.bot.send_message(
                user_id, broadcast_text, reply_markup=keyboard
            )
            sent_count += 1
        except Exception:
            failed_count += 1

        if (i + 1) % 50 == 0:
            await status_message.edit_text(
                f"📢 <b>РАССЫЛКА В ПРОЦЕССЕ...</b>\n\n"
                f"Отправлено: {sent_count}\n"
                f"Ошибок: {failed_count}",
                reply_markup=get_back_to_admin_keyboard(),
            )

    await status_message.edit_text(
        f"✅ <b>РАССЫЛКА ПРОМОКОДА ЗАВЕРШЕНА</b>\n\n"
        f"Отправлено: {sent_count}\n"
        f"Ошибок: {failed_count}",
        reply_markup=get_back_to_admin_keyboard(),
    )
