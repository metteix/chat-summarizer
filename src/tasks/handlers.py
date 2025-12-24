from aiogram import Router, types, F
from sqlalchemy import select
from database.session import async_session
from database.models import Task
import datetime
import html

from ml.services import process_items_pipeline

router = Router()


async def get_daily_tasks(chat_id: int) -> list[Task]:
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

    async with async_session() as session:
        query = select(Task).where(
            Task.chat_id == chat_id,
            Task.created_at >= yesterday
        )
        result = await session.execute(query)
        return result.scalars().all()


@router.message(F.text == "/tasks")
async def get_tasks_handler(message: types.Message):
    # 1. Получаем всё
    all_tasks = await get_daily_tasks(chat_id=message.chat.id)

    if not all_tasks:
        await message.answer("✅ Задач за последние 24 часа не найдено.")
        return

    status_msg = await message.answer("🔎 Анализирую задачи и дедлайны...")

    tasks_to_show = await process_items_pipeline(
        all_items=all_tasks,
        item_type="task",
        model_class=Task
    )

    if tasks_to_show is None:
        await status_msg.edit_text("⚠️ Временная ошибка Gemini. Попробуй через минуту.")
        return

    if not tasks_to_show:
        await status_msg.edit_text("🤷‍♂️ Похоже, это были просто обсуждения, а не реальные задачи.")
        return

    text = "<b>📋 Актуальные задачи за сутки:</b>\n\n"

    chat_id_str = str(message.chat.id)
    link_prefix = None

    if message.chat.username:
        link_prefix = f"https://t.me/{message.chat.username}"
    elif chat_id_str.startswith("-100"):
        clean_id = chat_id_str[4:]
        link_prefix = f"https://t.me/c/{clean_id}"

    for task in tasks_to_show:
        raw_content = task.about or task.task_name or "Задача"
        safe_content = html.escape(raw_content)

        if link_prefix:
            url = f"{link_prefix}/{task.message_id}"
            item = f"▫️ <a href='{url}'>{safe_content}</a>"
        else:
            item = f"▫️ {safe_content}"

        text += item + "\n\n"

    await status_msg.edit_text(text, disable_web_page_preview=True, parse_mode="HTML")
