import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from configs.config import BOT_TOKEN

async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(
        token=BOT_TOKEN
    )
    
    dp = Dispatcher(storage=MemoryStorage()) 

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    asyncio.run(main())

