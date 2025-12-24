from aiogram import Router, types, F
from sqlalchemy import select
from database.session import async_session
from database.models import Document
import datetime
import html

from ml.services import process_items_pipeline

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
    all_docs = await get_daily_documents(chat_id=message.chat.id)

    if not all_docs:
        await message.answer("📭 Документов за последние сутки не было.")
        return

    status_msg = await message.answer("🔎 Анализирую файлы...")

    docs_to_show = await process_items_pipeline(
        all_items=all_docs,
        item_type="doc",
        model_class=Document
    )

    if docs_to_show is None:
        await status_msg.edit_text("⚠️ Временная ошибка мозга (OpenAI). Попробуй через минуту.")
        return


    if not docs_to_show:
        await status_msg.edit_text("🤷‍♂️ Файлы были, но ничего важного (мемы или стикеры).")
        return

    text = "<b>📂 Важные документы за сутки:</b>\n\n"

    chat_id_str = str(message.chat.id)
    link_prefix = None

    if message.chat.username:
        link_prefix = f"https://t.me/{message.chat.username}"
    elif chat_id_str.startswith("-100"):
        clean_id = chat_id_str[4:]
        link_prefix = f"https://t.me/c/{clean_id}"

    for doc in docs_to_show:
        display_name = doc.about or doc.document_name or "Документ"
        safe_name = html.escape(display_name)

        if link_prefix:
            url = f"{link_prefix}/{doc.message_id}"
            item = f"📄 <a href='{url}'><b>{safe_name}</b></a>"
        else:
            item = f"📄 <b>{safe_name}</b>"

        text += item + "\n\n"

    await status_msg.edit_text(text, disable_web_page_preview=True, parse_mode="HTML")
