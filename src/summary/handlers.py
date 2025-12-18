import html
import datetime
from aiogram import Router, F, types
from database.session import async_session
from database.models import Chat, Task, Document, Link, Mention, Hashtag
from database.crud import get_chat_settings
from src.settings.handlers import SettingsStates

router = Router()


# --- 1. ML-заглушка: пока просто возвращаем список как есть ---
async def ml_filter_important(items: list):
    """
    Заглушка фильтра для будущей нейросети.
    Пока возвращаем список без изменений.
    """
    return items


# --- 2. Получение данных за последние 24 часа ---
async def get_daily_items(chat_id: int):
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

    async with async_session() as session:
        # Задачи
        tasks = (await session.execute(
            Task.__table__.select().where(Task.chat_id == chat_id, Task.created_at >= yesterday)
        )).scalars().all()

        # Документы
        documents = (await session.execute(
            Document.__table__.select().where(Document.chat_id == chat_id, Document.created_at >= yesterday)
        )).scalars().all()

        # Ссылки
        links = (await session.execute(
            Link.__table__.select().where(Link.chat_id == chat_id, Link.created_at >= yesterday)
        )).scalars().all()

        # Упоминания
        mentions = (await session.execute(
            Mention.__table__.select().where(Mention.chat_id == chat_id, Mention.created_at >= yesterday)
        )).scalars().all()

        # Хештеги
        hashtags = (await session.execute(
            Hashtag.__table__.select().where(Hashtag.chat_id == chat_id, Hashtag.created_at >= yesterday)
        )).scalars().all()

    return tasks, documents, links, mentions, hashtags


# --- 3. Формирование текста Summary с учётом настроек ---
async def format_summary(chat_id: int) -> str:
    chat_settings: Chat = await get_chat_settings(chat_id)
    if not chat_settings or not chat_settings.is_active:
        return "⚠️ Бот не активен в этом чате. Включите его командой /on"

    tasks, documents, links, mentions, hashtags = await get_daily_items(chat_id)

    # ML-фильтр (пока без изменений)
    tasks = await ml_filter_important(tasks)
    documents = await ml_filter_important(documents)
    links = await ml_filter_important(links)
    mentions = await ml_filter_important(mentions)
    hashtags = await ml_filter_important(hashtags)

    text_parts = []
    header = '📊 Сводка важного за сегодняшний день 📝\n\n'
    text_parts.append(header)
    if chat_settings.include_tasks and tasks:
        task_text = "📋 <b>Задачи за последние сутки:</b>\n"
        for t in tasks:
            task_text += f"▫️ {html.escape(t.task_name or 'Без описания')}\n"
        text_parts.append(task_text)

    if chat_settings.include_docs and documents:
        doc_text = "📂 <b>Документы за последние сутки:</b>\n"
        for d in documents:
            doc_text += f"▫️ {html.escape(d.document_name or 'Без названия')}\n"
        text_parts.append(doc_text)

    if chat_settings.include_links and links:
        link_text = "🔗 <b>Ссылки за последние сутки:</b>\n"
        for l in links:
            link_text += f"▫️ {l.url}\n"
        text_parts.append(link_text)

    if chat_settings.include_mentions and mentions:
        mention_text = "🔔 <b>Упоминания за сутки:</b>\n"
        for m in mentions:
            mention_text += f"▫️ {m.mention}\n"
        text_parts.append(mention_text)

    if chat_settings.include_hashtags and hashtags:
        hashtag_text = "#️⃣ <b>Хештеги за сутки:</b>\n"
        for h in hashtags:
            hashtag_text += f"▫️ {h.hashtag}\n"
        text_parts.append(hashtag_text)

    if len(text_parts) == 1:
        return "✅ Нет данных для сводки за последние сутки."


    return "\n\n".join(text_parts)


# --- 4. Команда /summary ---
@router.message(F.text == "/summary")
async def summary_handler(message: types.Message):
    text = await format_summary(message.chat.id)
    await message.answer(text, disable_web_page_preview=True)
