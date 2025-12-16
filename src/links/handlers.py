from aiogram import Router, types, F
from sqlalchemy import select
from database.session import async_session
from database.models import Link
import datetime
import html

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
    links_to_display = await get_daily_links(chat_id=message.chat.id)
    
    if links_to_display:
        text = "<b>🔗 Ссылки за последние 24 часа:</b>\n\n"
        
        for link in links_to_display:
            url = link.url
            raw_context = link.context or ""

            if len(raw_context) > 100:
                raw_context = raw_context[:100] + "..."

            safe_context = html.escape(raw_context)

            if raw_context and raw_context.strip() != url.strip():
                text += f"🔹 {url}\n   └ <i>{safe_context}</i>\n\n"
            else:
                text += f"🔹 {url}\n\n"

        await message.answer(text, disable_web_page_preview=True)
    
    else:
        await message.answer("📭 Ссылок за последние сутки не было.")
