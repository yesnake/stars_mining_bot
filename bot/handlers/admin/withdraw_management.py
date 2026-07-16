from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_keyboards import get_withdraw_decision_keyboard
from bot.utils import format_balance

from database.repositories.user_repositories import (
    approve_withdraw,
    reject_withdraw,
    get_pending_withdraws,
)

router = Router()


@router.callback_query(AdminFilter(), F.data == "admin_withdraws")
async def admin_withdraws_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    withdraws = await get_pending_withdraws(session)

    if not withdraws:
        await callback.answer("📋 Нет ожидающих заявок на вывод.", show_alert=True)
        return

    text = "💸 <b>ОЖИДАЮЩИЕ ВЫВОДЫ</b>\n\n" f"Всего заявок: {len(withdraws)}"

    await callback.message.edit_text(text)


@router.callback_query(AdminFilter(), F.data.startswith("admin_approve_withdraw:"))
async def admin_approve_withdraw_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    withdraw_id = int(callback.data.split(":")[1])

    withdraw = await approve_withdraw(session, withdraw_id)

    if not withdraw:
        await callback.answer(
            "❌ Заявка не найдена или уже обработана.", show_alert=True
        )
        return

    await callback.answer("✅ Заявка одобрена.", show_alert=True)

    try:
        await callback.bot.send_message(
            withdraw.user_id,
            f"✅ <b>ЗАЯВКА ОДОБРЕНА</b>\n\n"
            f"› 💰 Сумма: <b>{format_balance(withdraw.amount)} ⭐</b>\n"
            f"› 🆔 Номер заявки: <code>{withdraw.id}</code>\n\n"
            "Средства отправлены!",
        )
    except Exception:
        pass

    await callback.message.edit_text(
        f"✅ <b>ЗАЯВКА #{withdraw.id} ОДОБРЕНА</b>\n\n"
        f"› ID юзера: <code>{withdraw.user_id}</code>\n"
        f"› Username: @{withdraw.username}\n"
        f"› Сумма: <b>{format_balance(withdraw.amount)} ⭐</b>\n"
        f"› Статус: Завершена"
    )


@router.callback_query(AdminFilter(), F.data.startswith("admin_reject_withdraw:"))
async def admin_reject_withdraw_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    withdraw_id = int(callback.data.split(":")[1])

    withdraw = await reject_withdraw(session, withdraw_id)

    if not withdraw:
        await callback.answer(
            "❌ Заявка не найдена или уже обработана.", show_alert=True
        )
        return

    await callback.answer("❌ Заявка отклонена. Средства возвращены.", show_alert=True)

    try:
        await callback.bot.send_message(
            withdraw.user_id,
            f"❌ <b>ЗАЯВКА ОТКЛОНЕНА</b>\n\n"
            f"› 💰 Сумма: <b>{format_balance(withdraw.amount)} ⭐</b>\n"
            f"› 🆔 Номер заявки: <code>{withdraw.id}</code>\n\n"
            "Средства возвращены на твой баланс.",
        )
    except Exception:
        pass

    await callback.message.edit_text(
        f"❌ <b>ЗАЯВКА #{withdraw.id} ОТКЛОНЕНА</b>\n\n"
        f"› ID юзера: <code>{withdraw.user_id}</code>\n"
        f"› Username: @{withdraw.username}\n"
        f"› Сумма: <b>{format_balance(withdraw.amount)} ⭐</b>\n"
        f"› Статус: Отклонена\n"
        f"› Средства возвращены юзеру"
    )
