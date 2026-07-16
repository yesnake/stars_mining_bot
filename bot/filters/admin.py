from __future__ import annotations

from typing import Any

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from config_reader import config


def is_admin(user_id: int) -> bool:
    return user_id == config.ADMIN_ID


class AdminFilter(BaseFilter):
    def __init__(self, admin_id: int | None = None) -> None:
        self.admin_id = admin_id or config.ADMIN_ID

    async def __call__(
        self, event: Message | CallbackQuery, *args: Any, **kwargs: Any
    ) -> bool:
        user = getattr(event, "from_user", None)
        return bool(user and user.id == self.admin_id)
