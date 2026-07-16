from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Update, Message, CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.user_repositories import get_user_by_id


class BanCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any],
    ) -> Any:
        session: AsyncSession = data.get("session")

        user_id = None
        if event.message:
            user_id = event.message.from_user.id
        elif event.callback_query:
            user_id = event.callback_query.from_user.id

        if user_id and session:
            user = await get_user_by_id(session, user_id)
            if user and user.is_banned:
                if event.callback_query:
                    await event.callback_query.answer(
                        "🚫 Ты заблокирован и не можешь использовать бота.",
                        show_alert=True
                    )
                elif event.message:
                    await event.message.answer(
                        "🚫 Ты заблокирован и не можешь использовать бота."
                    )
                return

        return await handler(event, data)
