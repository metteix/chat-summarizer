from sqlalchemy import select, update
from aiogram import types
from database.session import async_session
from database.models import Chat

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
