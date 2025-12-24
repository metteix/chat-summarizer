from datetime import datetime, timedelta
from sqlalchemy import select, update
from aiogram import types

from database.session import async_session
from database.models import Chat, Task, Link, Document, Mention, Hashtag

async def activate_chat(message_chat: types.Chat) -> Chat:
    """
    Команда /on: Создает запись или включает is_active=True
    """
    async with async_session() as session:
        result = await session.execute(select(Chat).where(Chat.chat_id == message_chat.id))
        chat_entry = result.scalar_one_or_none()

        if not chat_entry:
            chat_entry = Chat(
                chat_id=message_chat.id,
                title=message_chat.title or message_chat.first_name,
                username=message_chat.username,
                type=message_chat.type,
                is_active=True
            )
            session.add(chat_entry)
        else:
            chat_entry.is_active = True
            chat_entry.title = message_chat.title or message_chat.first_name
            chat_entry.username = message_chat.username

        await session.commit()
        await session.refresh(chat_entry)
        return chat_entry

async def deactivate_chat(chat_id: int):
    """
    Команда /off: Ставит is_active=False
    """
    async with async_session() as session:
        await session.execute(
            update(Chat).where(Chat.chat_id == chat_id).values(is_active=False)
        )
        await session.commit()

async def get_chat_settings(chat_id: int) -> Chat:
    """
    Получаем объект чата (он же настройки)
    """
    async with async_session() as session:
        result = await session.execute(select(Chat).where(Chat.chat_id == chat_id))
        chat_entry = result.scalar_one_or_none()
        return chat_entry

async def update_settings_field(chat_id: int, **kwargs):
    """
    Обновляем любое поле в таблице Chat (время, галочки и т.д.)
    """
    async with async_session() as session:
        await session.execute(
            update(Chat).where(Chat.chat_id == chat_id).values(**kwargs)
        )
        await session.commit()

async def get_daily_data(chat_id: int):
    """
    Собирает все данные по конкретному чату за последние 24 часа.
    """
    yesterday = datetime.now() - timedelta(days=1)
    
    async with async_session() as session:
        tasks_q = await session.execute(
            select(Task).where(Task.chat_id == chat_id, Task.created_at >= yesterday)
        )
        mentions_q = await session.execute(
            select(Mention).where(Mention.chat_id == chat_id, Mention.created_at >= yesterday)
        )
        hashtags_q = await session.execute(
            select(Hashtag).where(Hashtag.chat_id == chat_id, Hashtag.created_at >= yesterday)
        )
        links_q = await session.execute(
            select(Link).where(Link.chat_id == chat_id, Link.created_at >= yesterday)
        )
        docs_q = await session.execute(
            select(Document).where(Document.chat_id == chat_id, Document.created_at >= yesterday)
        )

        return {
            "tasks": tasks_q.scalars().all(),
            "mentions": mentions_q.scalars().all(),
            "hashtags": hashtags_q.scalars().all(),
            "links": links_q.scalars().all(),
            "documents": docs_q.scalars().all(),
        }


async def save_analysis_results(model, analysis_results: list[dict]):
    """
    Сохраняет результаты анализа (is_important) для различных моделей.
    Принимает модель (например, Task, Link) и список словарей с id и is_important.
    """
    async with async_session() as session:
        for item_data in analysis_results:
            await session.execute(
                update(model)
                .where(model.id == item_data['id'])
                .values(is_important=item_data['is_important'])
            )
        await session.commit()
