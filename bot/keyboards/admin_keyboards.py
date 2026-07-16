from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin_stats",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔗 Трекинг ссылки",
                    callback_data="admin_tracking_links",
                ),
                InlineKeyboardButton(
                    text="📢 Рассылки",
                    callback_data="admin_create_broadcast",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👥 Управление юзерами",
                    callback_data="admin_users",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💸 Заявки на вывод",
                    callback_data="admin_withdraws",
                ),
            ],
        ]
    )
    return keyboard


def get_back_to_admin_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin_panel",
                )
            ],
        ]
    )
    return keyboard


def get_withdraw_decision_keyboard(withdraw_id: int) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Одобрить",
                    callback_data=f"admin_approve_withdraw:{withdraw_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"admin_reject_withdraw:{withdraw_id}",
                )
            ],
        ]
    )
    return keyboard


def get_tracking_links_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Создать новую ссылку",
                    callback_data="admin_create_link",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Список ссылок",
                    callback_data="admin_list_links",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin_panel",
                )
            ],
        ]
    )
    return keyboard


def get_users_management_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔍 Найти юзера",
                    callback_data="admin_search_user",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 Список юзеров",
                    callback_data="admin_list_users",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin_panel",
                )
            ],
        ]
    )
    return keyboard


def get_user_action_keyboard(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    ban_button_text = "🔓 Разбанить" if is_banned else "🔒 Забанить"
    ban_callback = f"admin_unban:{user_id}" if is_banned else f"admin_ban:{user_id}"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=ban_button_text,
                    callback_data=ban_callback,
                )
            ],
            [
                InlineKeyboardButton(
                    text="💰 Изменить баланс",
                    callback_data=f"admin_change_balance:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Активность",
                    callback_data=f"admin_user_activity:{user_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin_users",
                )
            ],
        ]
    )
    return keyboard


def get_broadcast_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Создать рассылку",
                    callback_data="admin_create_broadcast",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад",
                    callback_data="admin_panel",
                )
            ],
        ]
    )
    return keyboard
