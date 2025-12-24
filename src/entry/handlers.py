from aiogram import Router, types
from aiogram.filters import Command
from database.crud import activate_chat, deactivate_chat

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот-саммарайзер.\n"
        "Чтобы начать сбор данных в этом чате, напиши /on\n"
        "Чтобы остановить — /off\n"
        "Настройки — /settings"
    )

@router.message(Command("on"))
async def cmd_on(message: types.Message):
    await activate_chat(message.chat)
    await message.answer("✅ <b>Бот активирован!</b>\nЯ начал собирать ссылки, задачи и файлы.")

@router.message(Command("off"))
async def cmd_off(message: types.Message):
    await deactivate_chat(message.chat.id)
    await message.answer("🛑 <b>Бот остановлен.</b>\nСбор данных прекращен.")
