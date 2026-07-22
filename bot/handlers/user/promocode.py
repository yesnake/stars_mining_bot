from decimal import Decimal

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.services.botohub import get_botohub_tasks
from bot.utils import (
    format_speed,
    get_boost_status_line,
    safe_callback_answer,
    safe_delete_callback_message,
    format_balance,
)
from bot.keyboards.user_keyboards import (
    get_mining_keyboard,
    get_promocode_task_keyboard,
    get_start_miner_keyboard,
)

from database.repositories.user_repositories import (
    award_promocode,
    get_or_create_user,
    get_promocode_by_code,
    get_referrals_count,
    get_total_balance,
    has_user_used_promocode,
    mark_user_activity,
)

router = Router()


@router.callback_query(F.data.startswith("use_promocode:"))
async def use_promocode_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    answered = False

    async def answer_once(text: str | None = None, *, show_alert: bool = False) -> None:
        nonlocal answered
        if answered:
            return
        answered = True
        if text is None:
            await safe_callback_answer(callback)
        else:
            await safe_callback_answer(callback, text=text, show_alert=show_alert)

    parts = callback.data.split(":", 1)
    if len(parts) != 2:
        await answer_once("❌ Неверный промокод", show_alert=True)
        return

    code = parts[1]
    promocode = await get_promocode_by_code(session, code)
    if promocode is None:
        await answer_once("❌ Промокод не найден", show_alert=True)
        return

    user_id = callback.from_user.id

    used = await has_user_used_promocode(session, promocode.id, user_id)
    if used:
        await answer_once("❌ Вы уже использовали этот промокод", show_alert=True)
        return

    await get_or_create_user(session, user_id)
    await mark_user_activity(session, user_id)

    try:
        response = await get_botohub_tasks(user_id)
        tasks = response.get("tasks")
        completed = response.get("completed")
        skip = response.get("skip")

        if skip:
            completed = True

        if not completed:
            await answer_once()
            await safe_delete_callback_message(callback)
            keyboard = get_promocode_task_keyboard(code, user_id, tasks)
            await callback.message.answer(
                "❗<b>Подпишись на эти каналы, чтобы получить промокод:</b>\n\n",
                reply_markup=keyboard,
            )
            return

        ok = await award_promocode(session, promocode, user_id)
        if not ok:
            await answer_once("❌ Этот промокод уже исчерпан", show_alert=True)
            return

        await answer_once()
        await safe_delete_callback_message(callback)
        await callback.message.answer(
            f"✅ Ты успешно получил {format_balance(promocode.stars)} ⭐!"
        )
    except Exception:
        await answer_once(
            "⚠️ Не удалось активировать промокод. Попробуй позже", show_alert=True
        )


@router.callback_query(F.data.startswith("check_promocode_tasks:"))
async def check_promocode_tasks_handler(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    answered = False

    async def answer_once(text: str | None = None, *, show_alert: bool = False) -> None:
        nonlocal answered
        if answered:
            return
        answered = True
        if text is None:
            await safe_callback_answer(callback)
        else:
            await safe_callback_answer(callback, text=text, show_alert=show_alert)

    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        await answer_once("❌ Неверный формат проверки", show_alert=True)
        return

    code = parts[1]
    try:
        user_id = int(parts[2])
    except Exception:
        user_id = callback.from_user.id

    user = await get_or_create_user(session, user_id)
    await mark_user_activity(session, user_id)

    promocode = await get_promocode_by_code(session, code)
    if promocode is None:
        await answer_once("❌ Промокод не найден", show_alert=True)
        return

    used = await has_user_used_promocode(session, promocode.id, user_id)
    if used:
        await answer_once("❌ Вы уже использовали этот промокод", show_alert=True)
        return

    try:
        response = await get_botohub_tasks(user_id)
        tasks = response.get("tasks")
        completed = response.get("completed")
        skip = response.get("skip")

        if skip:
            completed = True

        if not completed:
            await answer_once()
            await safe_delete_callback_message(callback)
            keyboard = get_promocode_task_keyboard(code, user_id, tasks)
            await callback.message.answer(
                "❗<b>Подпишись на эти каналы, чтобы получить промокод:</b>\n\n",
                reply_markup=keyboard,
            )
            return

        ok = await award_promocode(
            session,
            promocode.id,
            user_id,
            promocode.stars,
        )
        if not ok:
            await answer_once("❌ Этот промокод уже исчерпан", show_alert=True)
            return

        await answer_once()
        await safe_delete_callback_message(callback)
        await callback.message.answer(
            f"✅ Ты успешно получил {format_balance(promocode.stars)} ⭐!"
        )
    except Exception:
        await answer_once(
            "⚠️ Не удалось активировать промокод. Попробуй позже", show_alert=True
        )
        return

    me = await callback.bot.get_me()
    boost_line = get_boost_status_line(user.boost_active)
    total_balance = await get_total_balance(session, user_id)
    active_referrals_count = await get_referrals_count(session, user_id)

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
        await callback.message.answer(
            text, reply_markup=get_mining_keyboard(me.username, user_id)
        )
    elif not user.is_mining:
        text = (
            "❌ <b>ГЕНЕРАТОР ОСТАНОВЛЕН</b>\n\n"
            f"› 💰 Баланс: <b>{format_balance(total_balance)} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{format_speed(user.mining_per_hour)} ⭐/час</b>\n"
            f"› 👥 Активных рефералов: <b>{active_referrals_count}</b>\n\n"
            "<blockquote>⚠️ Пока генератор выключен, ⭐ не начисляются.</blockquote>"
            f"<b>⬇️Нажми на кнопку ниже, чтобы запустить генератор!</b>\n\n"
        )
        await callback.message.answer(text, reply_markup=get_start_miner_keyboard())
