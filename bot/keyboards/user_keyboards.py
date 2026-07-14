from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_start_miner_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Запустить генератор",
                    callback_data="start_miner",
                    style="success",
                )
            ],
        ]
    )
    return keyboard


def get_task_keyboard(tasks: list[str], user_id: int, is_boost: bool = False) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔗 Перейти",
                url=task,
            )
        ]
        for task in tasks
    ]

    callback_data = f"check_boost_tasks:{user_id}" if is_boost else f"check_tasks:{user_id}"

    keyboard.append(
        [
            InlineKeyboardButton(
                text="✅ Проверить", callback_data=callback_data, style="success"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_mining_keyboard(bot_username: str, user_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Обновить баланс",
                    callback_data="refresh_miner",
                    style="primary",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👥 Пригласить друга",
                    url=f"https://t.me/share/url?url=https%3A%2F%2Ft.me%2F{bot_username}%3Fstart%3Dr_{user_id}&text=%D0%9F%D0%BE%D0%BB%D1%83%D1%87%D0%B0%D0%B9%201%E2%AD%90%2F%D1%87%D0%B0%D1%81%20%D0%BD%D0%B8%D1%87%D0%B5%D0%B3%D0%BE%20%D0%BD%D0%B5%20%D0%B4%D0%B5%D0%BB%D0%B0%D1%8F%21",
                    style="primary",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚀 Ускорить x2",
                    callback_data="boost_miner",
                    style="primary",
                )
            ],
        ]
    )
    return keyboard

def get_activate_boost_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Ускорить x2",
                    callback_data="boost_miner",
                    style="primary",
                )
            ],
        ]
    )
    return keyboard