from datetime import datetime, timedelta
from sqlalchemy import select
from database.session import async_session
from database.models import Mention, Hashtag, Link, Document, Task


async def add_link(chat_id: int, message_id: int, url: str, description: str = None):
    async with async_session() as session:
        obj = Link(chat_id=chat_id, message_id=message_id, url=url, description=description)
        session.add(obj)
        await session.commit()

async def add_document(chat_id: int, message_id: int, file_name: str, file_id: str, file_type: str):
    async with async_session() as session:
        obj = Document(
            chat_id=chat_id, 
            message_id=message_id, 
            file_name=file_name, 
            file_id=file_id, 
            file_type=file_type
        )
        session.add(obj)
        await session.commit()

async def add_task(chat_id: int, message_id: int, description: str, assignee: str = None, deadline=None):
    async with async_session() as session:
        task = Task(
            chat_id=chat_id,
            message_id=message_id,
            description=description,
            assignee=assignee,
            deadline=deadline
        )
        session.add(task)
        await session.commit()

# --- 4. ПОЛУЧЕНИЕ ДАННЫХ (ДЛЯ СВОДКИ) ---

async def get_daily_data(chat_id: int):
    """
    Возвращает все данные по чату за последние 24 часа.
    Идеально для Саши (генерация сводки).
    """
    yesterday = datetime.now() - timedelta(days=1)
    
    async with async_session() as session:
        # Запросы ко всем таблицам
        tasks_q = select(Task).where(Task.chat_id == chat_id, Task.created_at >= yesterday)
        mentions_q = select(Mention).where(Mention.chat_id == chat_id, Mention.created_at >= yesterday)
        hashtags_q = select(Hashtag).where(Hashtag.chat_id == chat_id, Hashtag.created_at >= yesterday)
        links_q = select(Link).where(Link.chat_id == chat_id, Link.created_at >= yesterday)
        docs_q = select(Document).where(Document.chat_id == chat_id, Document.created_at >= yesterday)

        return {
            "tasks": (await session.execute(tasks_q)).scalars().all(),
            "mentions": (await session.execute(mentions_q)).scalars().all(),
            "hashtags": (await session.execute(hashtags_q)).scalars().all(),
            "links": (await session.execute(links_q)).scalars().all(),
            "documents": (await session.execute(docs_q)).scalars().all(),
        }