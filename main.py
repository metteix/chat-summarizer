import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from configs.config import BOT_TOKEN

from src.entry.handlers import router as entry_router

from database import init_db

async def main() -> None:

    await init_db()
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(
        token=BOT_TOKEN
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(
        entry_router,
        )
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('bot stopped')
