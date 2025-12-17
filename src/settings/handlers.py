import re
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.enums import ChatMemberStatus
from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound


from .keyboards import (
    get_main_settings_kb,
    get_mode_settings_kb,
    get_summary_fields_kb,
    SUMMARY_FIELDS_CONFIG
)

router = Router()


# === FSM для ввода времени ===
class SettingsStates(StatesGroup):
    waiting_for_time = State()


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (Работа с БД) ===

async def get_or_create_settings(chat_id: int) -> ChatSettings:
    """Получает настройки чата или создает дефолтные, если их нет."""
    async with async_session() as session:
        query = select(ChatSettings).where(ChatSettings.chat_id == chat_id)
        result = await session.execute(query)
        settings = result.scalar_one_or_none()

        if not settings:
            # Создаем настройки по умолчанию (все включено, режим ручной)
            settings = ChatSettings(chat_id=chat_id)
            session.add(settings)
            await session.commit()
            # Нужно обновить объект, чтобы получить ID и дефолтные значения
            await session.refresh(settings)

        return settings


async def update_settings_field(chat_id: int, **kwargs):
    """Обновляет одно или несколько полей настроек."""
    async with async_session() as session:
        stmt = update(ChatSettings).where(ChatSettings.chat_id == chat_id).values(**kwargs)
        await session.execute(stmt)
        await session.commit()


async def is_user_admin(chat: types.Chat, user_id: int, bot: Bot) -> bool:
    if chat.type == 'private':
        return True
    member = await bot.get_chat_member(chat.id, user_id)
    return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]


# === ЛОГИКА ОТОБРАЖЕНИЯ ===

def format_status_text(chat_title: str, settings: ChatSettings) -> str:
    mode_str = "🤖 Автоматический" if settings.is_auto_summary else "🖐 Ручной"
    time_str = f" (в {settings.summary_time})" if settings.is_auto_summary else ""

    # Собираем список включенных полей
    active_names = []
    if settings.include_tasks: active_names.append(SUMMARY_FIELDS_CONFIG["tasks"])
    if settings.include_links: active_names.append(SUMMARY_FIELDS_CONFIG["links"])
    if settings.include_docs: active_names.append(SUMMARY_FIELDS_CONFIG["files"])
    if settings.include_mentions: active_names.append(SUMMARY_FIELDS_CONFIG["tags"])
    if settings.include_hashtags: active_names.append(SUMMARY_FIELDS_CONFIG["hashtags"])

    fields_str = ", ".join(active_names) if active_names else "Ничего (пустая сводка)"

    return (
        f"⚙️ <b>Настройки для чата:</b> {chat_title}\n\n"
        f"<b>Режим:</b> {mode_str}{time_str}\n"
        f"<b>Состав Summary:</b> {fields_str}"
    )


# === ХЭНДЛЕРЫ ===

@router.message(Command("/settings"))
async def cmd_settings(message: types.Message, bot: Bot):
    if not await is_user_admin(message.chat, message.from_user.id, bot):
        await message.reply("⛔️ Настройку бота может осуществлять только админ.")
        return

    settings = await get_or_create_settings(message.chat.id)
    text = format_status_text(message.chat.title or "Chat", settings)

    await message.answer(text, reply_markup=get_main_settings_kb())


@router.callback_query(F.data.startswith(("settings_", "set_mode_", "toggle_field_")))
async def settings_callback_router(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    # Проверка прав (на случай, если кликает не админ)
    if not await is_user_admin(callback.message.chat, callback.from_user.id, bot):
        await callback.answer("Недостаточно прав!(наорал)", show_alert=True)
        return

    chat_id = callback.message.chat.id
    action = callback.data

    # Получаем актуальные настройки перед действием
    settings = await get_or_create_settings(chat_id)

    # 1. ГЛАВНОЕ МЕНЮ
    if action == "settings_home":
        await state.clear()
        text = format_status_text(callback.message.chat.title, settings)
        # try-except на случай, если сообщение не изменилось
        try:
            await callback.message.edit_text(text, reply_markup=get_main_settings_kb())
        except:
            pass
        await callback.answer()

    # 2. МЕНЮ РЕЖИМА (АВТО/РУЧНОЙ)
    elif action == "settings_mode_menu":
        await callback.message.edit_text(
            f"Текущий режим: {'Авто' if settings.is_auto_summary else 'Ручной'}\n"
            "Выберите действие:",
            reply_markup=get_mode_settings_kb(settings)
        )
        await callback.answer()

    elif action == "set_mode_manual":
        await update_settings_field(chat_id, is_auto_summary=False)
        # Возвращаемся в главное меню и показываем обновление
        new_settings = await get_or_create_settings(chat_id)
        text = format_status_text(callback.message.chat.title, new_settings)
        await callback.message.edit_text(text, reply_markup=get_main_settings_kb())
        await callback.answer("Включен ручной режим")

    elif action in ["set_mode_auto_init", "set_mode_auto_change"]:
        await callback.message.edit_text(
            f"⌨️ Введите время отправки сводки в формате ЧЧ:ММ (МСК).\n"
            f"Текущее: {settings.summary_time}"
        )
        await state.set_state(SettingsStates.waiting_for_time)
        await callback.answer()

    # 3. МЕНЮ СОСТАВА (FIELDS)
    elif action == "settings_summary_menu":
        await callback.message.edit_text(
            "Выберите, какие данные включать в ежедневную сводку:",
            reply_markup=get_summary_fields_kb(settings)
        )
        await callback.answer()

    elif action.startswith("toggle_field_"):
        field_code = action.replace("toggle_field_", "")

        # Маппинг кода кнопки в название колонки БД
        field_map = {
            "tasks": "include_tasks",
            "links": "include_links",
            "files": "include_docs",
            "tags": "include_mentions",
            "hashtags": "include_hashtags"
        }

        db_col = field_map.get(field_code)
        if db_col:
            # Получаем текущее значение через getattr
            current_val = getattr(settings, db_col)
            # Инвертируем и сохраняем
            await update_settings_field(chat_id, **{db_col: not current_val})

            # Обновляем клавиатуру, чтобы показать новую галочку
            new_settings = await get_or_create_settings(chat_id)
            await callback.message.edit_reply_markup(
                reply_markup=get_summary_fields_kb(new_settings)
            )

        await callback.answer()


# === FSM: ОБРАБОТКА ВВОДА ВРЕМЕНИ ===

@router.message(SettingsStates.waiting_for_time)
async def process_time_input(message: types.Message, state: FSMContext):
    if re.match(r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", message.text):
        # Сохраняем время и включаем авто-режим
        await update_settings_field(
            message.chat.id,
            summary_time=message.text,
            is_auto_summary=True
        )

        await message.answer(f"✅ Время {message.text} установлено! Авто-сводка включена.")
        await state.clear()

        # Показываем обновленное главное меню
        settings = await get_or_create_settings(message.chat.id)
        text = format_status_text(message.chat.title or "Chat", settings)
        await message.answer(text, reply_markup=get_main_settings_kb())
    else:
        await message.reply("⚠️ Неверный формат. Пожалуйста, введите время в формате 09:00 или 23:30.")