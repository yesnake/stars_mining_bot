import aiohttp

from aiogram.types import CallbackQuery

from bot.keyboards.user_keyboards import get_mining_keyboard, get_task_keyboard
from bot.utils import format_balance, format_speed

from database.repositories.user_repositories import (
    start_miner,
    get_or_create_user,
    get_referrals_count,
    get_total_balance
)

from sqlalchemy.ext.asyncio import AsyncSession

from config_reader import config

BOTOHUB_API_URL = "https://botohub.me/get-tasks"


async def get_botohub_tasks(chat_id: int) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Auth": config.BOTOHUB_TOKEN.get_secret_value(),
    }

    payload = {
        "chat_id": chat_id,
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.post(
                BOTOHUB_API_URL, json=payload, headers=headers
            ) as response:
                if response.status != 200:
                    return {"tasks": [], "completed": True, "skip": True}

                data = await response.json()
                return data
    except Exception:
        return {"tasks": [], "completed": True, "skip": True}


async def send_task_status(
    session: AsyncSession, callback: CallbackQuery, user_id: int
) -> bool:
    user = await get_or_create_user(session, user_id)

    response = await get_botohub_tasks(user_id)
    tasks = response.get("tasks")
    completed = response.get("completed")
    skip = response.get("skip")

    active_referrals_count = await get_referrals_count(session, user.id)
    total_balance = await get_total_balance(session, user.id)

    if skip or not tasks:
        text = (
            "🟢 <b>ГЕНЕРАТОР РАБОТАЕТ</b>\n\n"
            f"› 💰 Баланс: <b>{format_balance(total_balance)} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{format_speed(user.mining_per_hour)} ⭐/час</b>\n"
            f"› 👥 Рефералов: <b>{active_referrals_count}</b>\n\n"
            "<blockquote>🚀 Генератор создает ⭐ прямо сейчас!</blockquote>"
        )
        await callback.message.answer(text, reply_markup=get_mining_keyboard())
        await start_miner(session, user_id)
        return True
    elif not completed:
        text = (
            "‼️<b>ПОСЛЕ ПОДПИСКИ НА ЭТИ КАНАЛЫ ТЫ БУДЕШЬ ПОЛУЧАТЬ 1⭐/ЧАС НИЧЕГО НЕ ДЕЛАЯ:</b>\n\n"
            "<blockquote>❤️ Не у всех есть такая уникальная возможность!</blockquote>"
        )
        await callback.message.answer(
            text,
            reply_markup=get_task_keyboard(tasks, user_id),
        )
        return False
    else:
        text = (
            "🟢 <b>ГЕНЕРАТОР РАБОТАЕТ</b>\n\n"
            f"› 💰 Баланс: <b>{format_balance(total_balance)} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{format_speed(user.mining_per_hour)} ⭐/час</b>\n"
            f"› 👥 Рефералов: <b>{active_referrals_count}</b>\n\n"
            "<blockquote>🚀 Генератор создает ⭐ прямо сейчас!</blockquote>"
        )
        await callback.message.answer(text, reply_markup=get_mining_keyboard())
        await start_miner(session, user_id)
        return True
