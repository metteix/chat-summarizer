import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.utils import executor
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio

from configs.congig import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

scheduler = AsyncIOScheduler()

# Старт бота и планировщика
async def on_start():
    scheduler.start()
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(on_start())
