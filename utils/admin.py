from aiogram import types, Bot
from aiogram.enums import ChatMemberStatus

async def is_user_admin(chat: types.Chat, user_id: int, bot: Bot) -> bool:
    if chat.type == 'private':
        return True
    member = await bot.get_chat_member(chat.id, user_id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
