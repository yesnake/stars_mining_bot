# Stars Mining Bot

Telegram bot for mining stars with referral system.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

3. Edit `.env` with your credentials:
- `BOT_TOKEN`: Your Telegram Bot token from @BotFather
- `DB_URL`: PostgreSQL connection string
- `BOTOHUB_TOKEN`: Your Botohub API token

4. Run the bot:
```bash
python main.py
```

## Features

- Mining system with hourly rewards
- Referral system with bonuses
- Integration with Botohub for tasks
- Automatic miner expiration monitoring

## Database

Uses PostgreSQL with SQLAlchemy ORM. Tables are created automatically on startup.

## Logs

Bot logs are written to `bot.log` and console.
