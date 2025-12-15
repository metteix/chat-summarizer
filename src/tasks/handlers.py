from aiogram import Router, types, F
# Импортируем готовые функции
from database.crud import get_daily_data

router = Router()


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