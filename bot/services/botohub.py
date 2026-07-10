import aiohttp

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
