from aiogram import Router, types, F
# Импортируем готовые функции
from database.crud import add_task, get_daily_data

router = Router()


# Пример 1: Сохранение данных
@router.message(F.text.regexp(r"(?i)(таска|задача|task)"))
async def tasks_handler(message: types.Message):
    task_text = message.text
    await add_task(
        chat_id=message.chat.id,
        message_id=message.message_id,
        description=task_text
    )

    await message.answer("Таска сохранена в базу!")


# Пример 2: Получение данных
@router.message(F.text == "/tasks")
async def get_tasks_handler(message: types.Message):
    data = await get_daily_data(chat_id=message.chat.id)

    text = (
        f"Данные по актуальным заданиям:\n"
        f"{data['tasks']}"
    )
    await message.answer(text)
    await message.answer("Задания пока не выявлены")