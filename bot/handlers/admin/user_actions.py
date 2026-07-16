from decimal import Decimal, InvalidOperation
from contextlib import suppress

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_keyboards import (
    get_back_to_admin_keyboard,
    get_users_management_keyboard,
    get_user_action_keyboard,
)
from bot.states.admin import AdminStates
from bot.utils import format_balance

from database.repositories.admin_repositories import (
    ban_user,
    get_all_users,
    get_user_activity,
    unban_user,
    update_user_balance,
)
from database.repositories.user_repositories import get_user_by_id

router = Router()


@router.callback_query(AdminFilter(), F.data == "admin_users")
async def admin_users_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    text = "👥 <b>УПРАВЛЕНИЕ ЮЗЕРАМИ</b>\n\n" "Выбери действие:"

    await callback.message.edit_text(text, reply_markup=get_users_management_keyboard())


@router.callback_query(AdminFilter(), F.data == "admin_search_user")
async def admin_search_user_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    text = "🔍 <b>ПОИСК ЮЗЕРА</b>\n\n" "Введи ID юзера:"

    await callback.message.edit_text(text, reply_markup=get_back_to_admin_keyboard())
    await state.set_state(AdminStates.waiting_for_user_id)


@router.message(AdminFilter(), AdminStates.waiting_for_user_id)
async def process_user_search(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer(
            "❌ Некорректный ID. Введи число.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        return

    user = await get_user_by_id(session, user_id)

    if not user:
        await message.answer(
            "❌ Юзер не найден.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        await state.clear()
        return

    status = "🚫 Забанен" if user.is_banned else "✅ Активен"
    mining_status = "⛏️ Майнит" if user.is_mining else "💤 Не майнит"

    text = (
        f"👤 <b>ЮЗЕР {user.id}</b>\n\n"
        f"› Статус: {status}\n"
        f"› Майнинг: {mining_status}\n"
        f"› Баланс: <b>{format_balance(user.balance)} ⭐</b>\n"
        f"› Скорость: <b>{format_balance(user.mining_per_hour)} ⭐/час</b>\n"
        f"› Буст: {'🚀 Активен' if user.boost_active else '❌ Не активен'}\n"
    )

    await message.answer(
        text, reply_markup=get_user_action_keyboard(user_id, user.is_banned)
    )
    await state.clear()


@router.callback_query(AdminFilter(), F.data == "admin_list_users")
async def admin_list_users_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    users = await get_all_users(session, limit=20)

    if not users:
        text = "📋 <b>СПИСОК ЮЗЕРОВ</b>\n\nЮзеров пока нет."
    else:
        text = "📋 <b>СПИСОК ЮЗЕРОВ</b> (последние 20)\n\n"
        for user in users:
            status = "🚫" if user.is_banned else "✅"
            mining = "⛏️" if user.is_mining else "💤"
            text += (
                f"{status} <code>{user.id}</code> | {mining} | "
                f"<b>{format_balance(user.balance)} ⭐</b>\n"
            )

    await callback.message.edit_text(text, reply_markup=get_back_to_admin_keyboard())


@router.callback_query(AdminFilter(), F.data.startswith("admin_ban:"))
async def admin_ban_user_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    user_id = int(callback.data.split(":")[1])

    user = await ban_user(session, user_id)

    if not user:
        await callback.answer("❌ Юзер не найден.", show_alert=True)
        return

    await callback.answer("✅ Юзер заблокирован.", show_alert=True)

    text = (
        f"👤 <b>ЮЗЕР {user.id}</b>\n\n"
        f"› Статус: 🚫 Забанен\n"
        f"› Майнинг: {'⛏️ Майнит' if user.is_mining else '💤 Не майнит'}\n"
        f"› Баланс: <b>{format_balance(user.balance)} ⭐</b>\n"
        f"› Скорость: <b>{format_balance(user.mining_per_hour)} ⭐/час</b>\n"
        f"› Буст: {'🚀 Активен' if user.boost_active else '❌ Не активен'}\n"
    )

    await callback.message.edit_text(
        text, reply_markup=get_user_action_keyboard(user_id, True)
    )


@router.callback_query(AdminFilter(), F.data.startswith("admin_unban:"))
async def admin_unban_user_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    user_id = int(callback.data.split(":")[1])

    user = await unban_user(session, user_id)

    if not user:
        await callback.answer("❌ Юзер не найден.", show_alert=True)
        return

    await callback.answer("✅ Юзер разблокирован.", show_alert=True)

    text = (
        f"👤 <b>ЮЗЕР {user.id}</b>\n\n"
        f"› Статус: ✅ Активен\n"
        f"› Майнинг: {'⛏️ Майнит' if user.is_mining else '💤 Не майнит'}\n"
        f"› Баланс: <b>{format_balance(user.balance)} ⭐</b>\n"
        f"› Скорость: <b>{format_balance(user.mining_per_hour)} ⭐/час</b>\n"
        f"› Буст: {'🚀 Активен' if user.boost_active else '❌ Не активен'}\n"
    )

    await callback.message.edit_text(
        text, reply_markup=get_user_action_keyboard(user_id, False)
    )


@router.callback_query(AdminFilter(), F.data.startswith("admin_change_balance:"))
async def admin_change_balance_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    user_id = int(callback.data.split(":")[1])
    await state.update_data(target_user_id=user_id)

    text = (
        "💰 <b>ИЗМЕНЕНИЕ БАЛАНСА</b>\n\n"
        f"ID юзера: <code>{user_id}</code>\n\n"
        "Введи новый баланс:"
    )

    await callback.message.edit_text(text, reply_markup=get_back_to_admin_keyboard())
    await state.set_state(AdminStates.waiting_for_new_balance)


@router.message(AdminFilter(), AdminStates.waiting_for_new_balance)
async def process_new_balance(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    try:
        new_balance = Decimal(message.text.strip())
    except (InvalidOperation, ValueError):
        await message.answer(
            "❌ Некорректный баланс. Введи число.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        return

    if new_balance < 0:
        await message.answer(
            "❌ Баланс не может быть отрицательным.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        return

    data = await state.get_data()
    user_id = data.get("target_user_id")

    user = await update_user_balance(session, user_id, new_balance)

    if not user:
        await message.answer(
            "❌ Юзер не найден.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        await state.clear()
        return

    text = (
        f"✅ <b>БАЛАНС ОБНОВЛЕН</b>\n\n"
        f"ID юзера: <code>{user_id}</code>\n"
        f"Новый баланс: <b>{format_balance(new_balance)} ⭐</b>"
    )

    await message.answer(
        text, reply_markup=get_user_action_keyboard(user_id, user.is_banned)
    )
    await state.clear()


@router.callback_query(AdminFilter(), F.data.startswith("admin_user_activity:"))
async def admin_user_activity_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    user_id = int(callback.data.split(":")[1])

    activity = await get_user_activity(session, user_id)

    if not activity or not activity.get("user"):
        await callback.answer("❌ Юзер не найден.", show_alert=True)
        return

    user = activity["user"]
    withdraws = activity.get("withdraws", [])

    text = (
        f"📊 <b>АКТИВНОСТЬ ЮЗЕРА {user_id}</b>\n\n"
        f"› Последняя активность: {user.last_activity_at.strftime('%Y-%m-%d %H:%M') if user.last_activity_at else 'Никогда'}\n"
        f"› Майнинг начат: {user.mining_started_at.strftime('%Y-%m-%d %H:%M') if user.mining_started_at else 'Нет'}\n\n"
    )

    if withdraws:
        text += "<b>Последние выводы:</b>\n"
        for w in withdraws[:5]:
            text += (
                f"› {format_balance(w.amount)} ⭐ | {w.status} | "
                f"{w.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            )
    else:
        text += "Выводов нет."

    with suppress(Exception):
        await callback.message.edit_text(
            text, reply_markup=get_user_action_keyboard(user_id, user.is_banned)
        )
