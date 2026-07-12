from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_start_miner_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Запустить генератор",
                    callback_data=f"start_miner",
                    style="success",
                )
            ],
        ]
    )
    return keyboard


def get_task_keyboard(tasks: list[str], user_id: int) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔗 Перейти",
                url=task,
            )
        ]
        for task in tasks
    ]
    keyboard.append(
        [
            InlineKeyboardButton(
                text="✅ Проверить", callback_data=f"check_tasks:{user_id}"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_mining_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Обновить баланс",
                    callback_data=f"refresh_miner",
                    style="success",
                )
            ],
        ]
    )
    return keyboard
