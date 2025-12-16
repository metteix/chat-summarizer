from aiogram import Router, types, F
from sqlalchemy import select
from database.session import async_session
from database.models import Mention
import datetime

router = Router()

# --- 1. ЗАГЛУШКА ПОД ML (НЕЙРОСЕТЬ) ---

async def ml_filter_important_mentions(mentions: list[Mention]) -> list[Mention]:
    """
    Функция-фильтр.
    Сейчас: Возвращает список как есть.
    В будущем: Отправит список в GPT, и GPT вернет только важные (где зовут по делу).
    """
    # TODO: СЮДА ПОДКЛЮЧИТЬ НЕЙРОНКУ
    # Например: return await ask_gpt_to_filter(mentions)
    
    # Пока просто возвращаем всё, но можно отфильтровать, например, теги @all
    filtered = [m for m in mentions if m.mention.lower() != "@all"]
    return filtered

async def get_daily_mentions(chat_id: int) -> list[Mention]:
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    
    async with async_session() as session:
        query = select(Mention).where(
            Mention.chat_id == chat_id,
            Mention.created_at >= yesterday
        ).order_by(Mention.created_at.desc())
        
        result = await session.execute(query)
        raw_mentions = result.scalars().all()
        
        important_mentions = await ml_filter_important_mentions(raw_mentions)
        return important_mentions

@router.message(F.text == "/mentions")
async def get_mentions_handler(message: types.Message):
    mentions = await get_daily_mentions(chat_id=message.chat.id)
    
    if not mentions:
        await message.answer("🔕 Важных упоминаний за сутки не найдено.")
        return
    
    grouped_mentions = {}

    clean_chat_id = str(message.chat.id).replace("-100", "")
    
    for m in mentions:
        tag = m.mention

        link = f"https://t.me/c/{clean_chat_id}/{m.message_id}"
        
        if tag not in grouped_mentions:
            grouped_mentions[tag] = []

        grouped_mentions[tag].append(link)

    text = "<b>🔔 Упоминания за 24 часа:</b>\n\n"

    for tag, links in grouped_mentions.items():
        text += f"<b>{tag}</b>\n"

        for i, link in enumerate(links, 1):
            text += f"🔗 <a href='{link}'>Сообщение {i}</a>\n"

        text += "\n"

    await message.answer(text, disable_web_page_preview=True)
