from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_keyboards import (
    get_back_to_admin_keyboard,
    get_tracking_links_keyboard,
)
from bot.states.admin import AdminStates
from database.repositories.admin_repositories import (
    create_tracking_link,
    get_tracking_links,
)

router = Router()


@router.callback_query(AdminFilter(), F.data == "admin_tracking_links")
async def admin_tracking_links_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    text = (
        "🔗 <b>ТРЕКИНГ ССЫЛКИ</b>\n\n"
        "Создавай уникальные ссылки для отслеживания источников трафика."
    )

    await callback.message.edit_text(text, reply_markup=get_tracking_links_keyboard())


@router.callback_query(AdminFilter(), F.data == "admin_create_link")
async def admin_create_link_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    text = (
        "🔗 <b>СОЗДАНИЕ ТРЕКИНГ ССЫЛКИ</b>\n\n"
        "Введи код ссылки (латиница, цифры, подчеркивания):"
    )

    await callback.message.edit_text(text, reply_markup=get_back_to_admin_keyboard())
    await state.set_state(AdminStates.waiting_for_link_code)


@router.message(AdminFilter(), AdminStates.waiting_for_link_code)
async def process_link_code(
    message: Message,
    state: FSMContext,
) -> None:
    link_code = message.text.strip()

    if not link_code or not all(c.isalnum() or c == "_" for c in link_code):
        await message.answer(
            "❌ Некорректный код. Используй только латиницу, цифры и подчеркивания.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        return

    await state.update_data(link_code=link_code)
    await state.set_state(AdminStates.waiting_for_link_name)

    await message.answer(
        "✅ Код принят.\n\nТеперь введи название ссылки:",
        reply_markup=get_back_to_admin_keyboard(),
    )


@router.message(AdminFilter(), AdminStates.waiting_for_link_name)
async def process_link_name(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    link_name = message.text.strip()

    if not link_name:
        await message.answer(
            "❌ Название не может быть пустым.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        return

    data = await state.get_data()
    link_code = data.get("link_code")

    link = await create_tracking_link(session, link_code, link_name)

    if not link:
        await message.answer(
            "❌ Ссылка с таким кодом уже существует.",
            reply_markup=get_back_to_admin_keyboard(),
        )
        await state.clear()
        return

    bot_username = (await message.bot.me()).username
    full_link = f"https://t.me/{bot_username}?start=track_{link_code}"

    text = (
        "✅ <b>ССЫЛКА СОЗДАНА</b>\n\n"
        f"› Название: <b>{link_name}</b>\n"
        f"› Код: <code>{link_code}</code>\n\n"
        f"› Ссылка:\n<code>{full_link}</code>"
    )

    await message.answer(text, reply_markup=get_back_to_admin_keyboard())
    await state.clear()


@router.callback_query(AdminFilter(), F.data == "admin_list_links")
async def admin_list_links_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    links = await get_tracking_links(session)

    if not links:
        text = "📋 <b>ТРЕКИНГ ССЫЛКИ</b>\n\nСсылок пока нет."
    else:
        text = "📋 <b>ТРЕКИНГ ССЫЛКИ</b>\n\n"
        for link in links:
            text += (
                f"<b>{link.name}</b>\n"
                f"› Код: <code>{link.link_code}</code>\n"
                f"› Старты: <b>{link.total_starts}</b>\n"
                f"› Майнеры: <b>{link.total_miners}</b>\n\n"
            )

    await callback.message.edit_text(text, reply_markup=get_back_to_admin_keyboard())
