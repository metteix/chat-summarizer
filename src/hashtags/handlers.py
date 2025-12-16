from aiogram import Router, types, F
from sqlalchemy import select
from database.session import async_session
from database.models import Hashtag
import datetime

router = Router()


# --- 1. ЗАГЛУШКА ПОД ML (НЕЙРОСЕТЬ) ---

async def ml_filter_important_hashtags(hashtags: list[Hashtag]) -> list[Hashtag]:
    """
    Функция-фильтр.
    Сейчас: Возвращает список как есть.
    В будущем: Отправит список в GPT, и GPT вернет только важные (где зовут по делу).
    """
    # TODO: СЮДА ПОДКЛЮЧИТЬ НЕЙРОНКУ
    # Например: return await ask_gpt_to_filter(mentions)

    # Пока просто возвращаем всё, но можно отфильтровать, например, теги @all
    filtered = [m for m in hashtags if m.hashtag.lower() != "@all"]
    return filtered


async def get_daily_hashtags(chat_id: int) -> list[Hashtag]:
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

    async with async_session() as session:
        query = select(Hashtag).where(
            Hashtag.chat_id == chat_id,
            Hashtag.created_at >= yesterday
        ).order_by(Hashtag.created_at.desc())

        result = await session.execute(query)
        raw_mentions = result.scalars().all()

        important_hashtags = await ml_filter_important_hashtags(raw_mentions)
        return important_hashtags


@router.message(F.text == "/hashtags")
async def get_mentions_handler(message: types.Message):
    hashtags = await get_daily_hashtags(chat_id=message.chat.id)

    if not hashtags:
        await message.answer("#️⃣ Важных хэштегов за сутки не найдено.")
        return

    grouped_mentions = {}

    clean_chat_id = str(message.chat.id).replace("-100", "")

    for m in hashtags:
        htag = m.hashtag

        link = f"https://t.me/c/{clean_chat_id}/{m.message_id}"

        if htag not in grouped_mentions:
            grouped_mentions[htag] = []

        grouped_mentions[htag].append(link)

    text = "<b>️#️⃣ Упоминания за 24 часа:</b>\n\n"

    for htag, links in grouped_mentions.items():
        text += f"<b>{htag}</b>\n"

        for i, link in enumerate(links, 1):
            text += f"🔗 <a href='{link}'>Сообщение {i}</a>\n"

        text += "\n"

    await message.answer(text, disable_web_page_preview=True)
