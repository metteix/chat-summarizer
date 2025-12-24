from aiogram import Router, types, F
from sqlalchemy import select
from database.session import async_session
from database.models import Hashtag
import datetime
import html

from ml.services import process_items_pipeline

router = Router()


async def get_daily_hashtags(chat_id: int) -> list[Hashtag]:
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

    async with async_session() as session:
        query = select(Hashtag).where(
            Hashtag.chat_id == chat_id,
            Hashtag.created_at >= yesterday
        ).order_by(Hashtag.created_at.desc())

        result = await session.execute(query)
        return result.scalars().all()


@router.message(F.text == "/hashtags")
async def get_hashtags_handler(message: types.Message):
    all_hashtags = await get_daily_hashtags(chat_id=message.chat.id)

    if not all_hashtags:
        await message.answer("#️⃣ Хэштегов за сутки не найдено.")
        return

    status_msg = await message.answer("🔎 Анализирую хэштеги...")

    hashtags_to_show = await process_items_pipeline(
        all_items=all_hashtags,
        item_type="hashtag",
        model_class=Hashtag
    )

    if hashtags_to_show is None:
        await status_msg.edit_text("⚠️ Временная ошибка Gemini. Попробуй через минуту.")
        return

    if not hashtags_to_show:
        await status_msg.edit_text("🤷‍♂️ Хэштеги были, но ничего важного (оффтоп).")
        return

    grouped_mentions = {}
    clean_chat_id = str(message.chat.id).replace("-100", "")

    for m in hashtags_to_show:
        htag = m.hashtag
        url = f"https://t.me/c/{clean_chat_id}/{m.message_id}"

        raw_label = m.about or m.context or "Сообщение"
        safe_label = html.escape(raw_label)

        if htag not in grouped_mentions:
            grouped_mentions[htag] = []

        grouped_mentions[htag].append((url, safe_label))

    text = "<b>#️⃣ Важные хэштеги за 24 часа:</b>\n\n"

    for htag, items in grouped_mentions.items():
        text += f"<b>{htag}</b>\n"
        for url, label in items:
            text += f"🔹 <a href='{url}'>{label}</a>\n"
        text += "\n"

    await status_msg.edit_text(text, disable_web_page_preview=True, parse_mode="HTML")
