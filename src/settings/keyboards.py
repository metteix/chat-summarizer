from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import ChatSettings

# Конфиг для отображения названий кнопок и соответствия кодов
SUMMARY_FIELDS_CONFIG = {
    "tasks": "Задания",
    "links": "Ссылки",
    "hashtags": "Хэштеги",
    "tags": "Тэги (Mentions)",
    "files": "Файлы"
}


def get_main_settings_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⚙️ Настройка режима", callback_data="settings_mode_menu")
    builder.button(text="📝 Состав Summary", callback_data="settings_summary_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_mode_settings_kb(settings: ChatSettings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if settings.is_auto_summary:
        # Если включен авто-режим
        builder.button(text=f"⏰ Изменить время ({settings.summary_time})", callback_data="set_mode_auto_change")
        builder.button(text="⏹ Переключить на ручной", callback_data="set_mode_manual")  #поменять название и интерфейс кнопки
    else:
        # Если включен ручной режим
        builder.button(text="▶️ Включить авто режим", callback_data="set_mode_auto_init")

    builder.button(text="🔙 Назад", callback_data="settings_home")
    builder.adjust(1)
    return builder.as_markup()


def get_summary_fields_kb(settings: ChatSettings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    # Словарь соответствия: Ключ конфига -> Поле в модели ChatSettings
    mapping = {
        "tasks": settings.include_tasks,
        "links": settings.include_links,
        "files": settings.include_docs,
        "tags": settings.include_mentions,
        "hashtags": settings.include_hashtags
    }

    for code, label in SUMMARY_FIELDS_CONFIG.items():  #тут как будто какая то хуйня но я не могу это доказать
        # Получаем значение поля (True/False)
        is_active = mapping.get(code, False)
        status = "✅" if is_active else "❌"

        text = f"{status} {label}"
        builder.button(text=text, callback_data=f"toggle_field_{code}")

    builder.adjust(1)
    builder.button(text="✅ Готово / Назад", callback_data="settings_home")
    return builder.as_markup()