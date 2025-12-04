import re
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ChatMemberStatus

# Импортируем клавиатуры (они остаются теми же)
from keyboards import (
    get_main_settings_kb,
    get_mode_settings_kb,
    get_summary_fields_kb,
    SUMMARY_FIELDS_Config
)

router = Router()

# --- Имитация БД ---
# Теперь ключом является chat_id (ID группы), а не пользователя
MOCK_DB = {}


def get_chat_config(chat_id: int):
    if chat_id not in MOCK_DB:
        MOCK_DB[chat_id] = {
            "mode": "manual",
            "time": None,
            "fields": ["tasks", "links", "hashtags", "tags"]
        }
    return MOCK_DB[chat_id]


def update_chat_config(chat_id: int, key: str, value):
    if chat_id not in MOCK_DB:
        get_chat_config(chat_id)
    MOCK_DB[chat_id][key] = value


# -------------------

class SettingsStates(StatesGroup):
    waiting_for_time = State()


# --- Помощник: Проверка на админа ---
async def is_user_admin(chat: types.Chat, user_id: int, bot: Bot) -> bool:
    # В личке всегда админ
    if chat.type == 'private':
        return True

    member = await bot.get_chat_member(chat.id, user_id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]


# --- Текстовый помощник ---
def get_status_text(chat_id: int, title: str):
    config = get_chat_config(chat_id)
    mode_str = "🖐 Ручной" if config['mode'] == 'manual' else f"⏰ Авто ({config['time']})"

    fields_names = [SUMMARY_FIELDS_Config[f] for f in config['fields'] if f in SUMMARY_FIELDS_Config]
    fields_str = ", ".join(fields_names) if fields_names else "Ничего"

    return (
        f"⚙️ **Настройки для чата:** {title}\n\n"
        f"**Режим:** {mode_str}\n"
        f"**Состав Summary:** {fields_str}"
    )


# ================= ХЭНДЛЕРЫ =================

@router.message(Command("settings"))
async def cmd_settings(message: types.Message, bot: Bot):
    # Проверяем права при вызове команды
    if not await is_user_admin(message.chat, message.from_user.id, bot):
        await message.reply("⛔ Настройки доступны только администраторам группы.")
        return

    # Используем message.chat.id (ID группы)
    text = get_status_text(message.chat.id, message.chat.title or "Private")
    await message.answer(text, reply_markup=get_main_settings_kb(), parse_mode="Markdown")


# Фильтр для всех коллбэков настроек: проверяем админа
@router.callback_query(F.data.startswith(("settings_", "set_mode_", "toggle_field_")))
async def settings_callback_router(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    # 1. Проверка прав (кто нажал кнопку?)
    if not await is_user_admin(callback.message.chat, callback.from_user.id, bot):
        await callback.answer("⛔ Только админы могут менять настройки!", show_alert=True)
        return

    # 2. Получаем ID группы (где нажали кнопку)
    chat_id = callback.message.chat.id
    data = callback.data

    # --- ЛОГИКА НАВИГАЦИИ ---

    # Главное меню
    if data == "settings_home":
        await state.clear()
        text = get_status_text(chat_id, callback.message.chat.title)
        # Важно: используем try-except, чтобы не падало, если текст не изменился
        try:
            await callback.message.edit_text(text, reply_markup=get_main_settings_kb(), parse_mode="Markdown")
        except:
            await callback.answer()

    # Меню режима
    elif data == "settings_mode_menu":
        config = get_chat_config(chat_id)
        await callback.message.edit_text(
            "Выберите режим работы бота в этой группе:",
            reply_markup=get_mode_settings_kb(config['mode'])
        )
        await callback.answer()

    # Установка ручного режима
    elif data == "set_mode_manual":
        update_chat_config(chat_id, "mode", "manual")
        await callback.answer("✅ Установлен ручной режим")
        # Перерисовываем меню режима
        await callback.message.edit_text(
            "Выберите режим работы бота в этой группе:",
            reply_markup=get_mode_settings_kb("manual")
        )

    # Старт ввода времени (Авто режим)
    elif data in ["set_mode_auto_init", "set_mode_auto_change"]:
        config = get_chat_config(chat_id)
        msg = "Введите время отправки (МСК) в формате **ЧЧ:ММ**.\nБот будет присылать отчет в этот чат."
        if config['time']:
            msg = f"Текущее время: {config['time']}.\n" + msg

        await callback.message.edit_text(msg, parse_mode="Markdown")
        await state.set_state(SettingsStates.waiting_for_time)
        await callback.answer()

    # Меню полей Summary
    elif data == "settings_summary_menu":
        config = get_chat_config(chat_id)
        await callback.message.edit_text(
            "Что включать в отчет по этой группе?",
            reply_markup=get_summary_fields_kb(config['fields'])
        )
        await callback.answer()

    # Переключение галочек
    elif data.startswith("toggle_field_"):
        field_code = data.replace("toggle_field_", "")
        config = get_chat_config(chat_id)
        current_fields = list(config['fields'])

        if field_code in current_fields:
            current_fields.remove(field_code)
        else:
            current_fields.append(field_code)

        update_chat_config(chat_id, "fields", current_fields)

        await callback.message.edit_reply_markup(
            reply_markup=get_summary_fields_kb(current_fields)
        )
        await callback.answer()


# --- Хэндлер ловли времени (Ввод текста) ---
@router.message(SettingsStates.waiting_for_time)
async def process_time_group(message: types.Message, state: FSMContext, bot: Bot):
    # Тут тоже стоит проверить админа, вдруг кто-то левый написал время пока админ ждал
    if not await is_user_admin(message.chat, message.from_user.id, bot):
        return  # Просто игнорируем сообщения не-админов в состоянии настройки

    time_input = message.text.strip()
    if not re.match(r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", time_input):
        await message.reply("❌ Неверный формат. Нужно ЧЧ:ММ (например, 10:00).")
        return

    chat_id = message.chat.id
    update_chat_config(chat_id, "mode", "auto")
    update_chat_config(chat_id, "time", time_input)

    await state.clear()
    await message.answer(f"✅ Для этого чата включен авто-режим на **{time_input}**.")

    # Можно вернуть меню настроек
    text = get_status_text(chat_id, message.chat.title)
    await message.answer(text, reply_markup=get_main_settings_kb(), parse_mode="Markdown")