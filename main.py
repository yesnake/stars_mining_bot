import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from database import Base

from bot.middlewares import DBSessionMiddleware, error_handler
from bot.handlers import setup_routers

from config_reader import config
from bot.services.miner_monitor import MinerMonitor
from database.repositories.user_repositories import ensure_user_activity_columns

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


_engine = create_async_engine(
    config.DB_URL.get_secret_value(),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False,
)

_sessionmaker = async_sessionmaker(
    _engine,
    expire_on_commit=False,
)

bot = Bot(
    token=config.BOT_TOKEN.get_secret_value(),
    default=DefaultBotProperties(parse_mode="HTML"),
)

dp = Dispatcher()
dp.include_routers(*setup_routers())
dp.update.middleware(DBSessionMiddleware(_sessionmaker))
dp.error.register(error_handler)

miner_monitor = MinerMonitor(bot, _sessionmaker)


@dp.startup()
async def on_startup() -> None:
    logger.info("Bot starting up...")
    await bot.delete_webhook(drop_pending_updates=True)

    await ensure_user_activity_columns(_engine)
    miner_monitor.start()

    logger.info("Bot started successfully")


@dp.shutdown()
async def on_shutdown() -> None:
    logger.info("Bot shutting down...")
    await miner_monitor.stop()
    await bot.session.close()
    await _engine.dispose()
    logger.info("Bot stopped")


async def main() -> None:
    try:
        logger.info("Starting polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        await bot.session.close()
        await _engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
