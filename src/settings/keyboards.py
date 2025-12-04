from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

SUMMARY_FIELDS_Config = {
    "tasks": "Задачи",
    "tags": "Теги",
    "hashtags": "Хэштеги",
    "links": "Ссылки",
    "files": "Файлы"
}

def get_main_settings_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🕹 Настройка режима", callback_data="settings_mode_menu")
    builder.button(text="📝 Настройка Summary", callback_data="settings_summary_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_mode_settings_kb(current_mode: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if current_mode == 'manual':
        # Если сейчас ручной -> кнопка включить авто
        builder.button(text="🟢 Включить Авто-режим", callback_data="set_mode_auto_init")
    else:
        # Если сейчас авто -> кнопки изменить время и выключить
        builder.button(text="✏️ Изменить время", callback_data="set_mode_auto_change")
        builder.button(text="🖐 Переключить на Ручной", callback_data="set_mode_manual")

    builder.button(text="🔙 Назад", callback_data="settings_home")
    builder.adjust(1)
    return builder.as_markup()