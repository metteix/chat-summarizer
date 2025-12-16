from aiogram import Router, types, F
from sqlalchemy import select
from database.session import async_session
from database.models import Task
import datetime
import html

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
    tasks_to_display = await get_daily_tasks(chat_id=message.chat.id)
    
    if tasks_to_display:
        text = "<b>📋 Актуальные задачи за сутки:</b>\n\n"
        for task in tasks_to_display:
            # Получаем текст и экранируем спецсимволы (<, >, &)
            raw_content = task.task_name or "Без описания"
            safe_content = html.escape(raw_content)
            text += f"▫️ {safe_content}\n"
            
        await message.answer(text)
    else:
        await message.answer("✅ Задач за последние 24 часа не найдено.")
