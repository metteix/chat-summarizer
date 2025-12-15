from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
# Импортируем твою модель
from database.models import Document 

router = Router()

@router.message(Command("docs"))
async def get_all_docs(message: Message, session: AsyncSession):
    # 1. Делаем запрос в базу
    # Сортируем по дате (свежие сверху) и берем, например, последние 20, чтобы не порвать сообщение
    query = select(Document).order_by(Document.created_at.desc()).limit(20)
    
    # Выполняем запрос
    result = await session.execute(query)
    documents = result.scalars().all()

    # 2. Если документов нет
    if not documents:
        await message.answer("📂 В базе данных пока нет сохраненных документов.")
        return

    # 3. Формируем красивый текст ответа
    response_text = "📂 **Список последних документов:**\n\n"
    
    for doc in documents:
        # doc.document_name - имя файла
        # doc.created_at - дата
        date_str = doc.created_at.strftime("%d.%m %H:%M")
    
        chat_id_str = str(message.chat.id).replace("-100", "")
        link = f"https://t.me/c/{chat_id_str}/{doc.message_id}"
    
        response_text += f"📄 [{doc.document_name}]({link}) ({date_str})\n"

    # 4. Отправляем ответ
    await message.answer(response_text, parse_mode="Markdown")