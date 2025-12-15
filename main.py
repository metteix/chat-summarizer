import asyncio
import logging

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage

from configs.config import BOT_TOKEN

from src.entry.handlers import router as entry_router
from src.hashtags.handlers import router as hashtags_router
from src.tags.handlers import router as tags_router

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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(
        entry_router,
        )
    
    dp.message.middleware(DbSessionMiddleware(async_session))
    dp.message.middleware(CollectorMiddleware())
    
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
