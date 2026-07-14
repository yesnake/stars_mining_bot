import logging
from typing import Any

from aiogram.types import ErrorEvent

logger = logging.getLogger(__name__)


async def error_handler(event: ErrorEvent) -> Any:
    logger.error(
        f"Update {event.update.update_id} caused error: {event.exception}",
        exc_info=event.exception
    )
    return True
