import aiohttp

from aiogram.types import CallbackQuery

from bot.keyboards.user_keyboards import get_task_keyboard

from database.repositories.user_repositories import start_miner, get_or_create_user

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

    async with aiohttp.ClientSession() as session:
        async with session.post(
            BOTOHUB_API_URL, json=payload, headers=headers
        ) as response:
            data = await response.json()

            if response.status != 200:
                return {"tasks": [], "completed": True, "skip": True}

            return data


async def send_task_status(
    session: AsyncSession, callback: CallbackQuery, user_id: int
) -> bool:
    user = await get_or_create_user(session, user_id)

    response = await get_botohub_tasks(user_id)
    tasks = response.get("tasks")
    completed = response.get("completed")
    skip = response.get("skip")

    if skip or not tasks:
        text = (
            "🟢 <b>ГЕНЕРАТОР РАБОТАЕТ</b>\n\n"
            f"› 💰 Баланс: <b>{user.balance} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{user.mining_per_hour} ⭐/час</b>\n"
            f"› 👥 Рефералов: <b>{user.balance}</b>\n\n"
            "<blockquote>🚀 Генератор создает ⭐ прямо сейчас!</blockquote>"
        )
        await callback.message.answer(text)
        await start_miner(session, user_id)
        return True
    elif not completed:
        text = (
            "‼️<b>ПОСЛЕ ПОДПИСКИ НА ЭТИ КАНАЛЫ ТЫ БУДЕШЬ ПОЛУЧАТЬ 1⭐/ЧАС НИЧЕГО НЕ ДЕЛАЯ:</b>\n\n",
            "<blockquote>❤️ Не у всех есть такая уникальная возможность!</blockquote>",
        )
        await callback.message.answer(
            text,
            reply_markup=get_task_keyboard(tasks, user_id),
        )
        return False
    else:
        text = (
            "🟢 <b>ГЕНЕРАТОР РАБОТАЕТ</b>\n\n"
            f"› 💰 Баланс: <b>{user.balance} ⭐</b>\n"
            f"› ⚡ Скорость: <b>{user.mining_per_hour} ⭐/час</b>\n"
            f"› 👥 Рефералов: <b>{user.balance}</b>\n\n"
            "<blockquote>🚀 Генератор создает ⭐ прямо сейчас!</blockquote>"
        )
        await callback.message.answer(text)
        await start_miner(session, user_id)
        return True
