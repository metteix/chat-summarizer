from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Mention, Hashtag, Document, Link, Task

class CollectorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message) or "session" not in data:
            return await handler(event, data)

        session: AsyncSession = data["session"]

        text = event.text or event.caption or ""
        chat_id = event.chat.id
        message_id = event.message_id
        #user_name = event.from_user.full_name if event.from_user else "Unknown"

        if event.document:
            new_doc = Document(
                chat_id=chat_id,
                message_id=message_id,
                document_name=event.document.file_name or "Без названия",
                file_id=event.document.file_id,
                context=text
            )
            session.add(new_doc)

        if event.entities or event.caption_entities:
            entities = event.entities or event.caption_entities
            
            for entity in entities:
                entity_value = entity.extract_from(text)

                if entity.type == "hashtag":
                    session.add(Hashtag(
                        chat_id=chat_id,
                        message_id=message_id,
                        hashtag=entity_value,
                        context=text
                    ))

                elif entity.type in ["url", "text_link"]:
                    url = entity.url if entity.type == "text_link" else entity_value
                    session.add(Link(
                        chat_id=chat_id,
                        message_id=message_id,
                        url=url,
                        context=text
                    ))

                elif entity.type in ["mention", "text_mention"]:
                    session.add(Mention(
                        chat_id=chat_id,
                        message_id=message_id,
                        mention=entity_value,
                        context=text
                    ))

        keywords = ["надо", "сделать", "дедлайн", "deadline", "task", "задание"]
        if any(word in text.lower() for word in keywords):
            if len(text) > 10:
                session.add(Task(
                    chat_id=chat_id,
                    message_id=message_id,
                    #task_name=task_name,
                    context=text
                ))

        try:
            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Ошибка при сохранении данных в Middleware: {e}")

        return await handler(event, data)
