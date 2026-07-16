from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_keyboards import (
    get_admin_main_keyboard,
    get_back_to_admin_keyboard,
)

router = Router()


@router.message(AdminFilter(), Command("admin"))
async def admin_panel_command(
    message: Message,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await state.clear()

    text = "👨‍💼 <b>АДМИН ПАНЕЛЬ</b>\n\n" "Выбери действие:"

    await message.answer(text, reply_markup=get_admin_main_keyboard())


@router.callback_query(AdminFilter(), F.data == "admin_panel")
async def admin_panel_callback(
    callback: CallbackQuery,
    session: AsyncSession,
    state: FSMContext,
) -> None:
    await state.clear()

    text = "👨‍💼 <b>АДМИН ПАНЕЛЬ</b>\n\nВыбери действие:"

    await callback.message.edit_text(text, reply_markup=get_admin_main_keyboard())
