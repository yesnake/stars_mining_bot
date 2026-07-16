from decimal import Decimal, InvalidOperation

from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_keyboards import get_back_to_admin_keyboard
from bot.states.admin import AdminStates
from bot.utils import format_balance

from database.repositories.admin_repositories import (
    create_broadcast,
    update_broadcast_stats,
    get_all_active_user_ids,
)

router = Router()


@router.callback_query(AdminFilter(), F.data == "admin_create_broadcast")
async def admin_create_broadcast_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    text = (
        "📢 <b>СОЗДАНИЕ РАССЫЛКИ</b>\n\n"
        "Отправь сообщение для рассылки.\n"
        "Можно использовать HTML-форматирование.\n"
        "Можно отправить текст, фото, видео или документ.\n\n"
    )

    await callback.message.edit_text(text, reply_markup=get_back_to_admin_keyboard())
    await state.set_state(AdminStates.waiting_for_broadcast_content)


@router.message(AdminFilter(), AdminStates.waiting_for_broadcast_content)
async def process_broadcast_content(
    message: Message,
    state: FSMContext,
) -> None:

    broadcast_data = {}

    if message.photo:
        broadcast_data["media_type"] = "photo"
        broadcast_data["media_file_id"] = message.photo[-1].file_id
        broadcast_data["caption"] = message.caption or ""
    elif message.video:
        broadcast_data["media_type"] = "video"
        broadcast_data["media_file_id"] = message.video.file_id
        broadcast_data["caption"] = message.caption or ""
    elif message.document:
        broadcast_data["media_type"] = "document"
        broadcast_data["media_file_id"] = message.document.file_id
        broadcast_data["caption"] = message.caption or ""
    elif message.text:
        broadcast_data["text"] = message.text
    else:
        await message.answer(
            "❌ Неподдерживаемый тип сообщения.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        return

    await state.update_data(**broadcast_data)

    text = (
        "📢 <b>СОЗДАНИЕ РАССЫЛКИ</b>\n\n"
        "Хочешь добавить кнопку к сообщению?\n\n"
        "Отправь текст и URL через символ | (например: Перейти|https://t.me/bot)\n"
        "Или отправь - для пропуска."
    )

    await message.answer(text, reply_markup=get_back_to_admin_keyboard())
    await state.set_state(AdminStates.waiting_for_broadcast_button)


@router.message(AdminFilter(), AdminStates.waiting_for_broadcast_button)
async def process_broadcast_button(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    data = await state.get_data()

    button_text = None
    button_url = None

    if message.text and message.text.strip() != "-":
        parts = message.text.split("|")
        if len(parts) == 2:
            button_text = parts[0].strip()
            button_url = parts[1].strip()

            if not button_url.startswith("http"):
                await message.answer(
                    "❌ URL должен начинаться с http:// или https://",
                    reply_markup=get_back_to_admin_keyboard(),
                )
                return
        else:
            await message.answer(
                "❌ Неправильный формат. Используй: Текст|URL",
                reply_markup=get_back_to_admin_keyboard(),
            )
            return

    broadcast = await create_broadcast(
        session,
        text=data.get("text"),
        media_type=data.get("media_type"),
        media_file_id=data.get("media_file_id"),
        caption=data.get("caption"),
        button_text=button_text,
        button_url=button_url,
    )

    await state.clear()

    status_message = await message.answer(
        "📢 <b>ЗАПУСК РАССЫЛКИ...</b>\n\n" "Отправлено: 0\n" "Ошибок: 0",
        reply_markup=get_back_to_admin_keyboard(),
    )

    user_ids = await get_all_active_user_ids(session)

    sent_count = 0
    failed_count = 0

    keyboard = None
    if button_text and button_url:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=button_text, url=button_url)]]
        )

    for i, user_id in enumerate(user_ids):
        try:
            if data.get("media_type") == "photo":
                await message.bot.send_photo(
                    user_id,
                    photo=data.get("media_file_id"),
                    caption=data.get("caption"),
                    reply_markup=keyboard,
                )
            elif data.get("media_type") == "video":
                await message.bot.send_video(
                    user_id,
                    video=data.get("media_file_id"),
                    caption=data.get("caption"),
                    reply_markup=keyboard,
                )
            elif data.get("media_type") == "document":
                await message.bot.send_document(
                    user_id,
                    document=data.get("media_file_id"),
                    caption=data.get("caption"),
                    reply_markup=keyboard,
                )
            else:
                await message.bot.send_message(
                    user_id,
                    text=data.get("text"),
                    reply_markup=keyboard,
                )

            sent_count += 1

        except Exception:
            failed_count += 1

        if (i + 1) % 50 == 0:
            await status_message.edit_text(
                f"📢 <b>РАССЫЛКА В ПРОЦЕССЕ...</b>\n\n"
                f"Отправлено: {sent_count}\n"
                f"Ошибок: {failed_count}",
                reply_markup=get_back_to_admin_keyboard(),
            )

    await update_broadcast_stats(session, broadcast.id, sent_count, failed_count)

    await status_message.edit_text(
        f"✅ <b>РАССЫЛКА ЗАВЕРШЕНА</b>\n\n"
        f"Отправлено: {sent_count}\n"
        f"Ошибок: {failed_count}",
        reply_markup=get_back_to_admin_keyboard(),
    )
