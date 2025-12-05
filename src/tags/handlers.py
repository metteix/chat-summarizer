import logging
from typing import List, Optional, Tuple

from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state
from aiogram.utils.formatting import as_list, Bold, as_numbered_list
from sqlalchemy import select


from database import crud
from database.session import async_session
from database.models import Message, Mention

router = Router()
logger = logging.getLogger(__name__)


# ------------------------------
# 1. ML-ЗАГЛУШКА (Важность упоминания)
# ------------------------------
async def analyze_mention_importance_stub(text: str) -> bool:
    """
    Заглушка: считает упоминание важным, если в контексте есть ключевые слова.
    """
    if not text:
        return False
    t = text.lower()
    keywords = ["сроч", "важн", "нужно", "обязательно", "deadline", "сделать", "внимание"]
    return any(kw in t for kw in keywords)


# ------------------------------
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ------------------------------
def extract_mentions(message: types.Message) -> List[Tuple[str, Optional[str]]]:
    """
    Ищет упоминания (@username или text_mention).
    Возвращает список: [(кто_упомянул, кого_упомянули), ...]
    """
    text = message.text or message.caption or ""
    entities = (message.entities or []) + (message.caption_entities or [])

    # Автор сообщения
    from_user = message.from_user.username or message.from_user.first_name

    mentions_found = []

    for ent in entities:
        if ent.type == "mention":
            # Обычное упоминание @username
            username = text[ent.offset: ent.offset + ent.length]
            mentions_found.append((from_user, username))

        elif ent.type == "text_mention":
            # Упоминание без юзернейма (клибальное имя)
            if ent.user:
                name = ent.user.username or ent.user.full_name
                mentions_found.append((from_user, f"@{name}"))

    # Убираем дубликаты
    return list(set(mentions_found))


async def get_message_text(chat_id: int, message_id: int) -> str:
    """
    Получает текст сообщения из БД по ID.
    """
    async with async_session() as session:
        # Делаем правильный SQL запрос
        query = select(Message.text).where(
            Message.chat_id == chat_id,
            Message.telegram_message_id == message_id
        )
        result = await session.execute(query)
        text = result.scalar_one_or_none()
        return text or ""


# ------------------------------
# 3. ХЕНДЛЕРЫ (ОБРАБОТЧИКИ)
# ------------------------------

@router.message(Command("tag"))  # Реагирует на /tag или /tags
async def cmd_tags_summary(message: types.Message):
    """
    Сводка упоминаний за 24 часа.
    """
    chat_id = message.chat.id

    # 1. Получаем данные (упоминания)
    try:
        data = await crud.get_daily_data(chat_id)
        mentions_rows = data.get("mentions", [])
    except Exception as e:
        logger.error(f"Ошибка БД: {e}")
        await message.answer("Ошибка при получении сводки.")
        return

    if not mentions_rows:
        await message.answer("За сутки вас никто не отмечал.")
        return

    # 2. Формируем списки (важное / обычное)
    important_list = []
    regular_list = []

    for mention in mentions_rows:
        # Для каждого упоминания достаем контекст (текст сообщения)
        context_text = await get_message_text(chat_id, mention.message_id)

        # Определяем важность
        is_important = await analyze_mention_importance_stub(context_text)

        # Формируем строку: "@vasya -> @petya: текст..."
        # Примечание: в БД Mention мы храним только `mentioned_username`.
        # Кто упомянул - надо бы доставать из Message, но для простоты пока пропустим или возьмем из контекста

        # Обрезаем текст, чтобы не был слишком длинным
        snippet = (context_text[:50] + "...") if len(context_text) > 50 else context_text
        line = f"{mention.mentioned_username}: {snippet}"

        if is_important:
            important_list.append(line)
        else:
            regular_list.append(line)

    # 3. Отправляем ответ
    content = []
    if important_list:
        content.append(Bold("🔥 Важные упоминания:"))
        content.append(as_numbered_list(*important_list))
        content.append("")

    if regular_list:
        content.append(Bold("💬 Остальные:"))
        content.append(as_numbered_list(*regular_list[:10]))  # Топ-10

    if not content:
        await message.answer("Упоминания были, но тексты не найдены.")
        return

    await message.answer(**as_list(Bold("📌 Упоминания за сутки"), "", *content).as_kwargs())


@router.message(F.entities | F.caption_entities, StateFilter(default_state))
async def handle_mentions(message: types.Message):
    """
    Ловит сообщения с упоминаниями и сохраняет в БД.
    """
    mentions_list = extract_mentions(message)

    if not mentions_list:
        return

    chat_id = message.chat.id
    msg_id = message.message_id
    user = message.from_user
    text = message.text or message.caption or ""

    try:
        # 1. Сначала сохраняем само сообщение (чтобы потом найти контекст)
        # Важно: register_chat делает проверку внутри crud, можно вызывать смело
        await crud.register_chat(chat_id, message.chat.title or "Chat")

        await crud.log_message(
            chat_id=chat_id,
            message_id=msg_id,
            user_id=user.id,
            username=user.username,
            text=text
        )

        # 2. Сохраняем упоминания
        for from_who, to_whom in mentions_list:
            await crud.add_mention(chat_id=chat_id, message_id=msg_id, username=to_whom)
            logger.info(f"Сохранено упоминание: {to_whom} в чате {chat_id}")

    except Exception as e:
        logger.error(f"Ошибка сохранения упоминания: {e}")