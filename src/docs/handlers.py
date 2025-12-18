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

        chat_id_str = str(message.chat.id)
        link_prefix = None

        if message.chat.username:
            link_prefix = f"https://t.me/{message.chat.username}"

        elif chat_id_str.startswith("-100"):
            clean_id = chat_id_str[4:]
            link_prefix = f"https://t.me/c/{clean_id}"

        for doc in docs_to_display:
            raw_name = doc.document_name or "Без названия"
            safe_name = html.escape(raw_name)

            if link_prefix:
                url = f"{link_prefix}/{doc.message_id}"
                item = f"📄 <a href='{url}'><b>{safe_name}</b></a>"
            else:
                item = f"📄 <b>{safe_name}</b>"

            if doc.context:
                safe_context = html.escape(doc.context)
                if len(safe_context) > 50:
                    safe_context = safe_context[:50] + "..."
                item += f"\n└ <i>{safe_context}</i>"

            text += item + "\n\n"

        await message.answer(text, disable_web_page_preview=True)
    else:
        await message.answer("✅ Документов за последние 24 часа не найдено.")