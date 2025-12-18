from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import Chat

SUMMARY_FIELDS_CONFIG = {
    "tasks": "📝 Задачи",
    "links": "🔗 Ссылки",
    "files": "📂 Файлы",
    "tags": "🔔 Теги",
    "hashtags": "#️⃣ Хештеги"
}

def get_main_settings_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Режим работы", callback_data="settings_mode_menu")],
        [InlineKeyboardButton(text="📋 Состав сводки", callback_data="settings_summary_menu")],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="delete_message")]
    ])

def get_mode_settings_kb(chat: Chat) -> InlineKeyboardMarkup:
    auto_text = "✅ Авто" if chat.is_auto_summary else "Авто"
    manual_text = "✅ Ручной" if not chat.is_auto_summary else "Ручной"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=auto_text, callback_data="set_mode_auto_init"),
            InlineKeyboardButton(text=manual_text, callback_data="set_mode_manual")
        ],
        [
            InlineKeyboardButton(text="🕒 Изменить время", callback_data="set_mode_auto_change")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="settings_home")]
    ])

def get_summary_fields_kb(chat: Chat) -> InlineKeyboardMarkup:
    # Берем поля из chat
    buttons_map = [
        ("tasks", chat.include_tasks),
        ("links", chat.include_links),
        ("files", chat.include_docs),
        ("tags", chat.include_mentions),
        ("hashtags", chat.include_hashtags),
    ]
    
    kb = []
    for code, is_active in buttons_map:
        status = "✅" if is_active else "❌"
        text = f"{status} {SUMMARY_FIELDS_CONFIG[code]}"
        kb.append([InlineKeyboardButton(text=text, callback_data=f"toggle_field_{code}")])
    
    kb.append([InlineKeyboardButton(text="🔙 Назад", callback_data="settings_home")])
    return InlineKeyboardMarkup(inline_keyboard=kb)
