from aiogram import Router, types, F
from sqlalchemy import select
from database.session import async_session
import datetime
from database.models import Task

router = Router()

async def get_daily_tasks(chat_id: int) -> list[Task]:
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

    async with async_session() as session:
        tasks = select(Task).where(
            Task.chat_id == chat_id, 
            Task.created_at >= yesterday
        )
        result = await session.execute(tasks)
        return result.scalars().all()


@router.message(F.text == "/tasks")
async def get_tasks_handler(message: types.Message):
    tasks_to_display = await get_daily_tasks(chat_id=message.chat.id)
    if tasks_to_display:
        text = f"Данные по актуальным заданиям:\n"
        
        for task in tasks_to_display:
            text += f"{task}\n"
            
        await message.answer(text)
    
    else:
        await message.answer("нет задач")
