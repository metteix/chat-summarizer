from aiogram.fsm.state import StatesGroup, State

class SettingsStates(StatesGroup):
    waiting_for_time = State()
