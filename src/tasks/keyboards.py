from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

SUMMARY_FIELDS_Config = {"tasks": "Задания", "links": "Ссылки", "hashtags": "Хэштеги", "tags": "Тэги", "files": "Файлы"}

def get_main_task_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Настройка режима", callback_data="settings_mode_menu")
    builder.button(text="Настройкт Summary", callback_data="settings_summary_menu")
    builder.adjust(1)
    return builder.as_markup()

def get_mode_settings_kb(cur_mode:str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if cur_mode == 'manual':  # Если до этого устанавливали ручной режим
        builder.button(text="Включить авто режим", callback_data="set_mode_auto_init")
    else: #Если ранее был установлен авоматический режим
        builder.button(text="Изменить время", callback_data="set_mode_auto_change")
        builder.button(text="Переключить на ручной", callback_data="set_mode_manual")
    builder.button(text="Вернуться в главное меню", callback_data="settings_home")
    builder.adjust(1)
    return builder.as_markup()

def get_summary_fields_kb(active_fields:list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, lable in SUMMARY_FIELDS_Config.items():
        status = "✅" if code in active_fields else "❌"
        text = f"{status} {lable}"
        builder.button(text=text, callback_data=f"toggle_field_{code}")
    builder.adjust(1)
    builder.button(text="OK", callback_data="settings_home")
    return builder.as_markup()