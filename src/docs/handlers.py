from aiogram import Router, types, F
from sqlalchemy import select
from database.session import async_session
from database.models import Document
import datetime
import html

router = Router()


async def get_daily_documents(chat_id: int) -> list[Document]:
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

    async with async_session() as session:
        query = select(Document).where(
            Document.chat_id == chat_id,
            Document.created_at >= yesterday
        )
        result = await session.execute(query)
        return result.scalars().all()


@router.message(F.text == "/docs")
async def get_documents_handler(message: types.Message):
    docs_to_display = await get_daily_documents(chat_id=message.chat.id)

    if docs_to_display:
        text = "</b>📂 Документы за последние сутки:</b>\n\n"
        for doc in docs_to_display:
            # Получаем текст и экранируем спецсимволы (<, >, &)
            raw_name = doc.document_name or "Без названия"
            safe_name = html.escape(raw_name)
            if doc.context:
                safe_context = html.escape(doc.context)
                # Вывод: Имя файла + описание на следующей строке
                text += f"📄 <b>{safe_name}</b>\n└ <i>{safe_context}</i>\n\n"
            else:
                # Вывод: Только имя файла
                text += f"📄 {safe_name}\n"
        await message.answer(text)
    else:
        await message.answer("✅ Документов за последние 24 часа не найдено.")

@router.message()
async def echo_all(message: types.Message):
    pass