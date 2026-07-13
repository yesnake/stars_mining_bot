import asyncio
import sys
import logging
from sqlalchemy import text

from config_reader import config
from database.base import Base
from sqlalchemy.ext.asyncio import create_async_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_database_connection():
    logger.info("Checking database connection...")
    try:
        engine = create_async_engine(config.DB_URL.get_secret_value())
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        logger.info("✓ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


async def check_configuration():
    logger.info("Checking configuration...")
    try:
        bot_token = config.BOT_TOKEN.get_secret_value()
        db_url = config.DB_URL.get_secret_value()
        botohub_token = config.BOTOHUB_TOKEN.get_secret_value()

        if not bot_token or not db_url or not botohub_token:
            logger.error("✗ Configuration incomplete")
            return False

        logger.info("✓ Configuration valid")
        return True
    except Exception as e:
        logger.error(f"✗ Configuration check failed: {e}")
        return False


async def main():
    logger.info("Starting health checks...")

    checks = [
        await check_configuration(),
        await check_database_connection(),
    ]

    if all(checks):
        logger.info("✓ All health checks passed")
        return 0
    else:
        logger.error("✗ Some health checks failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
