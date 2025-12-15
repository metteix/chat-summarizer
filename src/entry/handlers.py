from aiogram import Router, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.state import default_state

router = Router()

@router.message(CommandStart(), StateFilter(default_state))
async def cmd_start(message: types.Message):
    await message.answer(
        """Привет! 👋

        Я помогаю не потерять важные упоминания, поручения и документы из переписки, 
        чтобы пользователь всегда был в курсе всех учебных событий и дедлайнов. 
        Чтобы узнать больше о полезных функциях бота, нажмите /help.:""",
    )
