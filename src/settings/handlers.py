import re
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database.crud import get_chat_settings, update_settings_field, activate_chat
from src.settings.states import SettingsStates
from src.settings.keyboards import (
    get_main_settings_kb,
    get_mode_settings_kb,
    get_summary_fields_kb
)
from src.settings.utils import format_status_text
from utils.admin import is_user_admin

router = Router()

@router.message(Command("settings"))
async def cmd_settings(message: types.Message, bot: Bot):
    if not await is_user_admin(message.chat, message.from_user.id, bot):
        await message.reply("⛔️ Настройку бота может осуществлять только админ.")
        return
    
    chat = await get_chat_settings(message.chat.id)
    if not chat:
        chat = await activate_chat(message.chat)

    text = format_status_text(message.chat.title or "Чат", chat)
    await message.answer(text, reply_markup=get_main_settings_kb())


@router.callback_query(F.data.startswith(("settings_", "set_mode_", "toggle_field_", "delete_message")))
async def settings_callback_router(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    if callback.data == "delete_message":
        await callback.message.delete()
        return

    if not await is_user_admin(callback.message.chat, callback.from_user.id, bot):
        await callback.answer("Только админ!", show_alert=True)
        return

    chat_id = callback.message.chat.id
    action = callback.data

    chat = await get_chat_settings(chat_id)
    if not chat:
        await callback.answer("Чат не найден в БД. Напишите /on", show_alert=True)
        return

    if action == "settings_home":
        await state.clear()
        text = format_status_text(callback.message.chat.title, chat)
        try:
            await callback.message.edit_text(text, reply_markup=get_main_settings_kb())
        except: pass
        await callback.answer()

    elif action == "settings_mode_menu":
        await callback.message.edit_text(
            f"Текущий режим: {'Авто' if chat.is_auto_summary else 'Ручной'}",
            reply_markup=get_mode_settings_kb(chat)
        )
        await callback.answer()

    elif action == "set_mode_manual":
        await update_settings_field(chat_id, is_auto_summary=False)
        chat = await get_chat_settings(chat_id) 
        text = format_status_text(callback.message.chat.title, chat)
        await callback.message.edit_text(text, reply_markup=get_main_settings_kb())
        await callback.answer("Включен ручной режим")

    elif action in ["set_mode_auto_init", "set_mode_auto_change"]:
        await callback.message.edit_text(
            f"⌨️ Введите время сводки (МСК) в формате ЧЧ:ММ.\n"
            f"Например: <b>09:00</b> или <b>18:30</b>"
        )
        await state.set_state(SettingsStates.waiting_for_time)
        await callback.answer()

    elif action == "settings_summary_menu":
        await callback.message.edit_text(
            "Выберите данные для сводки:",
            reply_markup=get_summary_fields_kb(chat)
        )
        await callback.answer()

    elif action.startswith("toggle_field_"):
        field_code = action.replace("toggle_field_", "")
        field_map = {
            "tasks": "include_tasks", "links": "include_links",
            "files": "include_docs", "tags": "include_mentions",
            "hashtags": "include_hashtags"
        }
        
        db_col = field_map.get(field_code)
        if db_col:
            current_val = getattr(chat, db_col)
            await update_settings_field(chat_id, **{db_col: not current_val})
            
            chat = await get_chat_settings(chat_id)
            await callback.message.edit_reply_markup(
                reply_markup=get_summary_fields_kb(chat)
            )
        await callback.answer()


@router.message(SettingsStates.waiting_for_time)
async def process_time_input(message: types.Message, state: FSMContext):
    time_regex = r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$"
    
    if re.match(time_regex, message.text):
        await update_settings_field(
            message.chat.id,
            summary_time=message.text,
            is_auto_summary=True
        )
        await message.answer(f"✅ Время <b>{message.text}</b> установлено! Авто-сводка включена.")
        await state.clear()

        chat = await get_chat_settings(message.chat.id)
        text = format_status_text(message.chat.title, chat)
        await message.answer(text, reply_markup=get_main_settings_kb())
    else:
        await message.answer("⚠️ Неверный формат времени!\nПопробуйте еще раз (например: 18:00) или нажмите /settings для отмены.")
