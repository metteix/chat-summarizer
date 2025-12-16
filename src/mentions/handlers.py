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
        ).order_by(Document.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()


@router.message(F.text == "/docs")
async def get_documents_handler(message: types.Message):
    docs_to_display = await get_daily_documents(chat_id=message.chat.id)

    if docs_to_display:
        text = "<b>📂 Документы за последние сутки:</b>\n\n"

        clean_chat_id = str(message.chat.id).replace("-100", "")
        
        for doc in docs_to_display:
            raw_name = doc.document_name or "Без названия"
            safe_name = html.escape(raw_name)

            msg_link = f"https://t.me/c/{clean_chat_id}/{doc.message_id}"

            item_text = f"📄 <a href='{msg_link}'><b>{safe_name}</b></a>"

            if doc.context:
                safe_context = html.escape(doc.context[:100] + "..." if len(doc.context) > 100 else doc.context)
                item_text += f"\n└ <i>{safe_context}</i>"
            
            text += item_text + "\n\n"

        await message.answer(text, disable_web_page_preview=True)
    else:
        await message.answer("✅ Документов за последние 24 часа не найдено.")
