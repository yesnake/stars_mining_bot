import logging
from os.path import join, dirname

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Config(BaseSettings):
    BOT_TOKEN: SecretStr
    DB_URL: SecretStr
    BOTOHUB_TOKEN: SecretStr
    ADMIN_ID: int
    WITHDRAW_CHANNEL_ID: int

    model_config = SettingsConfigDict(
        env_file=join(dirname(__file__), ".env"), env_file_encoding="utf-8"
    )

    @field_validator("BOT_TOKEN", "DB_URL", "BOTOHUB_TOKEN")
    @classmethod
    def validate_not_empty(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value().strip():
            raise ValueError("Configuration value cannot be empty")
        return v


def load_config() -> Config:
    try:
        config = Config()
        logger.info("Configuration loaded successfully")
        return config
    except Exception as e:
        logger.critical(f"Failed to load configuration: {e}")
        raise


config = load_config()
