from aiogram import Router, types, F
from sqlalchemy import select
from database.session import async_session
from database.models import Link
import datetime
import html

from ml.services import process_items_pipeline

router = Router()


async def get_daily_links(chat_id: int) -> list[Link]:
    """
    Достаем ссылки за последние 24 часа.
    """
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    
    async with async_session() as session:
        query = select(Link).where(
            Link.chat_id == chat_id,
            Link.created_at >= yesterday
        ).order_by(Link.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()


@router.message(F.text == "/links")
async def get_links_handler(message: types.Message):
    all_links = await get_daily_links(chat_id=message.chat.id)

    if not all_links:
        await message.answer("📭 Ссылок за последние сутки не было.")
        return

    status_msg = await message.answer("🔎 Проверяю ссылки...")

    links_to_show = await process_items_pipeline(
        all_items=all_links,
        item_type="link",
        model_class=Link
    )

    if links_to_show is None:
        await status_msg.edit_text("⚠️ Временная ошибка Gemini. Попробуй через минуту.")
        return

    if not links_to_show:
        await status_msg.edit_text("🤷‍♂️ Ссылки за сутки были, но ничего важного (мемы, спам или оффтоп).")
        return
    
    text = "<b>🔗 Важные ссылки за 24 часа:</b>\n\n"
    for link in links_to_show:
        about = html.escape(link.about or link.context or "Ссылка")
        text += f"🔹 <b>{about}</b>\n   └ {link.url}\n\n"

    await status_msg.edit_text(text, disable_web_page_preview=True, parse_mode="HTML")
