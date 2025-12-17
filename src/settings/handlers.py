import re
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ChatMemberStatus
from database.crud import get_chat_settings, update_chat_settings


from .keyboards import (
    get_main_settings_kb,
    get_mode_settings_kb,
    get_summary_fields_kb,
    SUMMARY_FIELDS_Config
)

router = Router()


class SettingsStates(StatesGroup):
    waiting_for_time = State()


# === ПЕРЕВОДЧИК (MAPPING) ===
# Слева: Твои ключи из клавиатуры
# Справа: Названия колонок в таблице Chats (models.py)
FIELD_MAPPING = {
    "tasks": "include_tasks",
    "links": "include_links",
    "files": "include_docs",  # Кнопка 'files' -> колонка 'include_docs'
    "tags": "include_mentions",  # Кнопка 'tags' -> колонка 'include_mentions' (предполагаю)

    # ВНИМАНИЕ: Убедись, что в models.py в классе Chat есть 'include_hashtags'
    # Если нет — добавь в БД или закомментируй эту строку
    "hashtags": "include_hashtags"
}


async def is_user_admin(chat: types.Chat, user_id: int, bot: Bot) -> bool:
    if chat.type == 'private':
        return True
    member = await bot.get_chat_member(chat.id, user_id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]


async def get_status_text(chat_id: int, title: str):
    chat = await get_chat_settings(chat_id)
    mode_str = "Авто" if chat.is_auto_summary else "Ручной"
    time_str = f"({chat.summary_time})" if chat.is_auto_summary else ""

    # Собираем красивые названия включенных полей
    active_names = []
    # Проверяем базу и добавляем названия из конфига
    if chat.include_tasks: active_names.append(SUMMARY_FIELDS_Config["tasks"])
    if chat.include_links: active_names.append(SUMMARY_FIELDS_Config["links"])
    if chat.include_docs: active_names.append(SUMMARY_FIELDS_Config["files"])
    if chat.include_mentions: active_names.append(SUMMARY_FIELDS_Config["tags"])
    if chat.include_mentions: active_names.append(SUMMARY_FIELDS_Config["hashtags"])

    fields_str = ", ".join(active_names) if active_names else "Ничего"

    return (
        f"⚙️ **Настройки для чата:** {title}\n\n"
        f"**Режим:** {mode_str} {time_str}\n"
        f"**Состав Summary:** {fields_str}"
    )

@router.message(Command("settings"))
async def cmd_settings(message: types.Message, bot: Bot):
    if not await is_user_admin(message.chat, message.from_user.id, bot):
        await message.reply("Настройку бота может осуществлять только админ.")
        return
    text = await get_status_text(message.chat.id, message.chat.title or "Chat")
    await message.answer(text, reply_markup=get_main_settings_kb(), parse_mode="Markdown")

@router.callback_query(F.data.startswith(("settings_", "set_mode_", "toggle_field_")))
async def settings_callback_router(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    if not await is_user_admin(callback.message.chat, callback.from_user.id, bot):
        await callback.answer("Недостаточно прав!", show_alert=True)
        return
    chat_id = callback.message.chat.id
    data = callback.data
    chat_settings = await get_chat_settings(chat_id)
    if data == "settings_home":
        await state.clear()
        text = await get_status_text(chat_id, callback.message.chat.title)
        try:
            await callback.message.edit_text(text, reply_markup=get_main_settings_kb(), parse_mode="Markdown")
        except:
            await callback.answer()
    elif data == "settings_mode_menu":
        cur_mode = "auto" if chat_settings.is_auto_summary else "manual"
        await callback.message.edit_text(
            "Выберите режим работы:",
            reply_markup=get_mode_settings_kb(cur_mode)
        )
        await callback.answer()

    elif data == "set_mode_manual":
        await update_chat_settings(chat_id, is_auto_summary=False)
        text = await get_status_text(chat_id, callback.message.chat.title)
        await callback.message.edit_text(text, reply_markup=get_main_settings_kb(), parse_mode="Markdown")
        await callback.answer("Включен ручной режим")

    elif data in ["set_mode_auto_init", "set_mode_auto_change"]:  #вот тут не пон говорим ли мы текущее если до этого у нас была только автоматическая настройка
        await callback.message.edit_text(
            f"Введите время (ЧЧ:ММ). Текущее: {chat_settings.summary_time}"
        )
        await state.set_state(SettingsStates.waiting_for_time)
        await callback.answer()

        # --- SUMMARY FIELDS MENU ---
    elif data == "settings_summary_menu":
        # Формируем список ключей ДЛЯ КЛАВИАТУРЫ (tasks, files, tags...)
        active_list_kb = []
        if chat_settings.include_tasks: active_list_kb.append("tasks")
        if chat_settings.include_links: active_list_kb.append("links")
        if chat_settings.include_docs: active_list_kb.append("files")
        if chat_settings.include_mentions: active_list_kb.append("tags")
        if chat_settings.include_mentions: active_list_kb.append("hashtags")

        await callback.message.edit_text(
            "Выберите, что включать в сводку:",
            reply_markup=get_summary_fields_kb(active_list_kb)
        )
        await callback.answer()

    elif data.startswith("toggle_field_"):
        field_code = data.replace("toggle_field_", "")  # Например: "files"

        # Переводим "files" -> "include_docs"
        db_column = FIELD_MAPPING.get(field_code)

        if db_column:
            # Получаем текущее значение из БД (True/False)
            # getattr позволяет взять поле по имени строки
            try:
                current_val = getattr(chat_settings, db_column)

                # Записываем обратное значение
                await update_chat_settings(chat_id, **{db_column: not current_val})

                # Обновляем клавиатуру (чтобы галочка переключилась)
                # Нужно заново считать данные
                new_settings = await get_chat_settings(chat_id)

                new_active_list = []
                if new_settings.include_tasks: new_active_list.append("tasks")
                if new_settings.include_links: new_active_list.append("links")
                if new_settings.include_docs: new_active_list.append("files")
                if new_settings.include_mentions: new_active_list.append("tags")
                if new_settings.include_mentions: new_active_list.append("hashtags")

                await callback.message.edit_reply_markup(
                    reply_markup=get_summary_fields_kb(new_active_list)
                )
            except AttributeError:
                await callback.answer(f"Ошибка: поле {db_column} не найдено в БД", show_alert=True)

        await callback.answer()

#мб стоит его потом в другой файл дропнуть
@router.message(SettingsStates.waiting_for_time)
async def process_time_input(message: types.Message, state: FSMContext):
    if re.match(r"^\d{1,2}:\d{2}$", message.text):
        await update_chat_settings(
            message.chat.id,
            is_auto_summary=True,
            summary_time=message.text
        )
        await message.answer(f"✅ Время {message.text} установлено!")
        await state.clear()

        text = await get_status_text(message.chat.id, message.chat.title)
        await message.answer(text, reply_markup=get_main_settings_kb(), parse_mode="Markdown")
    else:
        await message.reply("Формат: 09:00")