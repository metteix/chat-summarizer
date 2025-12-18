from database.models import Chat
from src.settings.keyboards import SUMMARY_FIELDS_CONFIG

def format_status_text(chat_title: str, chat: Chat) -> str:
    status_icon = "🟢" if chat.is_active else "🔴"
    status_text = "Включен" if chat.is_active else "Выключен (напиши /on)"
    
    mode_str = "🤖 Автоматический" if chat.is_auto_summary else "🖐 Ручной"
    time_str = f" (в {chat.summary_time})" if chat.is_auto_summary else ""

    active_names = []
    if chat.include_tasks: active_names.append(SUMMARY_FIELDS_CONFIG["tasks"])
    if chat.include_links: active_names.append(SUMMARY_FIELDS_CONFIG["links"])
    if chat.include_docs: active_names.append(SUMMARY_FIELDS_CONFIG["files"])
    if chat.include_mentions: active_names.append(SUMMARY_FIELDS_CONFIG["tags"])
    if chat.include_hashtags: active_names.append(SUMMARY_FIELDS_CONFIG["hashtags"])

    fields_str = ", ".join(active_names) if active_names else "Ничего (пустая сводка)"

    return (
        f"⚙️ <b>Настройки:</b> {chat_title}\n"
        f"Статус бота: {status_icon} {status_text}\n\n"
        f"<b>Режим:</b> {mode_str}{time_str}\n"
        f"<b>Состав Summary:</b> {fields_str}"
    )
