from aiogram import Router, types, F
from sqlalchemy import select
from database.session import async_session
from database.models import Mention
import datetime
import html

from ml.services import process_items_pipeline

router = Router()


async def get_daily_mentions(chat_id: int) -> list[Mention]:
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

    async with async_session() as session:
        query = select(Mention).where(
            Mention.chat_id == chat_id,
            Mention.created_at >= yesterday
        ).order_by(Mention.created_at.desc())

        result = await session.execute(query)
        return result.scalars().all()


@router.message(F.text == "/mentions")
async def get_mentions_handler(message: types.Message):
    all_mentions = await get_daily_mentions(chat_id=message.chat.id)

    if not all_mentions:
        await message.answer("🔕 Упоминаний за сутки не найдено.")
        return

    status_msg = await message.answer("🔎 Проверяю, кого звали по делу...")

    mentions_to_show = await process_items_pipeline(
        all_items=all_mentions,
        item_type="mention",
        model_class=Mention
    )

    # 3. Обработка ошибки
    if mentions_to_show is None:
        await status_msg.edit_text("⚠️ Временная ошибка мозга (OpenAI). Попробуй через минуту.")
        return

    if not mentions_to_show:
        await status_msg.edit_text("🤷‍♂️ Упоминания были, но ничего важного (просто флуд).")
        return

    # --- ЛОГИКА ГРУППИРОВКИ И ВЫВОДА ---
    grouped_mentions = {}
    clean_chat_id = str(message.chat.id).replace("-100", "")

    for m in mentions_to_show:
        tag = m.mention
        url = f"https://t.me/c/{clean_chat_id}/{m.message_id}"

        # Берем описание или контекст
        raw_label = m.about or m.context or "Сообщение"
        safe_label = html.escape(raw_label)

        if tag not in grouped_mentions:
            grouped_mentions[tag] = []

        # Сохраняем пару
        grouped_mentions[tag].append((url, safe_label))

    text = "<b>🔔 Важные упоминания за 24 часа:</b>\n\n"

    for tag, items in grouped_mentions.items():
        text += f"<b>{tag}</b>\n"
        for url, label in items:
            text += f"🔹 <a href='{url}'>{label}</a>\n"
        text += "\n"

    await status_msg.edit_text(text, disable_web_page_preview=True, parse_mode="HTML")
