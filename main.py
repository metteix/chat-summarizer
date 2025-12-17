import asyncio
import logging
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties

from configs.config import BOT_TOKEN
from src.entry.handlers import router as entry_router
from src.tasks.handlers import router as tasks_router
from src.links.handlers import router as links_router
from src.catch.handlers import router as catch_router
from src.mentions.handlers import router as mentios_router
from src.docs.handlers import router as docs_router
from src.hashtags.handlers import router as hashtags_router

from database import init_db
from database.session import async_session
from middlewares.middleware import CollectorMiddleware

class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_pool):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(self, handler, event, data):
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)

async def main() -> None:
    await init_db()

    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(entry_router)
    dp.include_router(tasks_router)
    dp.include_router(links_router)
    dp.include_router(mentios_router)
    dp.include_router(docs_router)
    dp.include_router(hashtags_router)
    dp.include_router(catch_router)

    dp.message.outer_middleware(DbSessionMiddleware(async_session))
    dp.message.outer_middleware(CollectorMiddleware())

    dp.edited_message.outer_middleware(DbSessionMiddleware(async_session))
    dp.edited_message.outer_middleware(CollectorMiddleware())

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")