from aiogram import Router, types
from aiogram.filters import Command
import html
from database.crud import get_daily_data, get_chat_settings

router = Router()

@router.message(Command("summary"))
async def cmd_summary(message: types.Message):
    settings = await get_chat_settings(message.chat.id)

    if not settings:
        await message.answer("❌ Бот не активирован в этом чате. Напишите /on")
        return

    data = await get_daily_data(message.chat.id)

    if not any(data.values()):
        await message.answer("📭 За последние 24 часа важных данных не найдено.")
        return

    report = [f"<b>📊 СВОДКА ЗА 24 ЧАСА</b>\n"]

    chat_username = message.chat.username
    clean_id = str(message.chat.id).replace("-100", "")
    
    def get_link(msg_id):
        if chat_username:
            return f"https://t.me/{chat_username}/{msg_id}"
        return f"https://t.me/c/{clean_id}/{msg_id}"

    if settings.include_tasks and data["tasks"]:
        report.append("📝 <b>Задачи:</b>")
        for t in data["tasks"]:
            report.append(f"▫️ {html.escape(t.task_name)}")
        report.append("")

    if settings.include_links and data["links"]:
        report.append("🔗 <b>Важные ссылки:</b>")
        for l in data["links"]:
            desc = l.context if l.context and len(l.context) < 50 else "Ссылка"
            report.append(f"🔹 <a href='{l.url}'>{html.escape(desc)}</a>")
        report.append("")

    if settings.include_docs and data["documents"]:
        report.append("📂 <b>Файлы:</b>")
        for d in data["documents"]:
            link = get_link(d.message_id)
            report.append(f"📄 <a href='{link}'>{html.escape(d.document_name)}</a>")
        report.append("")

    if settings.include_mentions and data["mentions"]:
        m_map = {}
        for m in data["mentions"]:
            if m.mention not in m_map: m_map[m.mention] = []
            m_map[m.mention].append(get_link(m.message_id))
        
        report.append("🔔 <b>Упоминания:</b>")
        for user, links in m_map.items():
            links_str = ", ".join([f"<a href='{url}'>{i}</a>" for i, url in enumerate(links, 1)])
            report.append(f"👤 {user}: {links_str}")
        report.append("")

    if settings.include_hashtags and data["hashtags"]:
        tags = list(set([h.hashtag for h in data["hashtags"]]))
        report.append(f"#️⃣ <b>Темы:</b> {', '.join(tags)}")

    if len(report) <= 1:
        await message.answer("⚠️ Все категории сводки отключены в настройках /settings.")
        return

    final_text = "\n".join(report)
    await message.answer(final_text, disable_web_page_preview=True)
