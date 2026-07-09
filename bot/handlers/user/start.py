from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.user_repositories import get_or_create_user

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message, session: AsyncSession) -> None:
    user_id = message.from_user.id
    user = await get_or_create_user(session, user_id)
    
    await message.answer(f"Hello, {user.id}! Welcome to the bot.")