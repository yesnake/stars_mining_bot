from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    waiting_for_link_code = State()
    waiting_for_link_name = State()
    waiting_for_user_id = State()
    waiting_for_new_balance = State()
    waiting_for_broadcast_target = State()
    waiting_for_broadcast_content = State()
    waiting_for_broadcast_media = State()
    waiting_for_broadcast_button = State()
