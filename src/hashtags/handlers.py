import logging
from collections import Counter
from typing import List

from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.utils.formatting import Bold, as_list, as_numbered_list

from database import crud

router = Router()
logger = logging.getLogger(__name__)


# --- 1. ML ЗАГЛУШКА ---

async def analyze_hashtag_importance(tag: str) -> bool:
    """
    Заглушка ML-модуля.
    """
    if not tag:
        return False

    t = tag.lower()
    keywords = ["важн", "срочн", "dead", "дедлайн", "экзам", "контрольн"]

    for kw in keywords:
        if kw in t:
            return True
    return False


# --- 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

def extract_hashtags(message: types.Message) -> List[str]:
    """
    Извлекает уникальные хэштеги из текста и подписи.
    """
    text = message.text or message.caption or ""
    entities = (message.entities or []) + (message.caption_entities or [])

    tags = []
    for ent in entities:
        try:
            if getattr(ent, "type", None) == "hashtag":
                offset = getattr(ent, "offset", None)
                length = getattr(ent, "length", None)
                if offset is None or length is None:
                    continue
                tag_value = text[offset: offset + length]
                # защита от пустых строк
                if tag_value:
                    tags.append(tag_value)
        except Exception:
            # логируем стектрейс, но не ломаем обработку
            logger.exception("Ошибка при извлечении entity для хэштега")

    # дедупликация по нижнему регистру, сохраняем порядок
    seen = set()
    deduped = []
    for t in tags:
        key = t.lower()
        if key not in seen:
            deduped.append(t)
            seen.add(key)
    return deduped


# --- 3. ХЕНДЛЕРЫ ---

@router.message(Command("hashtags"))
async def cmd_hashtags_summary(message: types.Message):
    """
    Отправляет сводку важных хэштегов за последние 24 часа.
    Использует db_crud.get_daily_data для получения данных по конкретному чату.
    """
    chat_id = message.chat.id

    # 1. Получаем данные из БД
    try:
        data = await crud.get_daily_data(chat_id)
        hashtag_objs = data.get("hashtags", [])
    except Exception:
        logger.exception("Ошибка получения данных БД для хэштегов")
        await message.answer("⚠️ Ошибка при получении сводки.")
        return

    if not hashtag_objs:
        await message.answer("📭 За последние 24 часа хэштегов не найдено.")
        return

    # 2. Считаем частоту хэштегов
    tags_list = [h.hashtag for h in hashtag_objs if getattr(h, "hashtag", None)]
    counter = Counter(tags_list)

    # 3. Фильтруем через ML-заглушку и формируем списки
    important_items = []
    regular_items = []

    # Если тегов очень много, можно ограничить проверку ML только топ-N в будущем
    for tag, count in counter.most_common():
        try:
            is_important = await analyze_hashtag_importance(tag)
        except Exception:
            logger.exception("Ошибка при анализе важности тега %s", tag)
            is_important = False

        line = f"{tag} ({count})"

        if is_important:
            important_items.append(line)
        else:
            regular_items.append(line)

    # 4. Формируем красивый ответ
    content = []

    if important_items:
        content.append(Bold("🔥 Важные темы:"))
        content.append(as_numbered_list(*important_items))
        content.append("\n")  # пустая строка

    if not content:
        await message.answer("Странно, теги есть, но список пуст.")
        return

    response = as_list(
        Bold("📊 Сводка хэштегов за 24 часа"),
        "",
        *content
    )

    # as_kwargs возвращает dict с text и parse_mode и т.д.
    try:
        await message.answer(**response.as_kwargs())
    except Exception:
        logger.exception("Ошибка при отправке сводки в чат %s", chat_id)


@router.message(F.caption_entities | F.entities, StateFilter(default_state))
async def handle_message_with_hashtags(message: types.Message):
    """
    Ловит сообщение с сущностями (например, хэштегами в тексте или подписи).
    Сохраняет в БД: регистрирует чат, логирует сообщение, сохраняет найденные хэштеги.
    StateFilter(default_state) — чтобы не мешать многошаговым диалогам (FSM).
    """
    tags = extract_hashtags(message)

    # Если хэштегов нет, выходим (пусть другие хендлеры работают)
    if not tags:
        return

    chat_id = message.chat.id
    msg_id = message.message_id
    user = message.from_user
    text = message.text or message.caption or ""

    try:
        # 1. Регистрируем чат (если новый)
        title = getattr(message.chat, "title", None) or getattr(message.chat, "username", None) or "Private"
        await crud.register_chat(chat_id, title)

        # 2. Логируем сообщение
        await crud.log_message(
            chat_id=chat_id,
            message_id=msg_id,
            user_id=getattr(user, "id", 0),
            username=(getattr(user, "username", None) or ""),
            text=text
        )

        # 3. Сохраняем каждый тег
        for tag in tags:
            try:
                await crud.add_hashtag(chat_id, msg_id, tag)
                logger.info("Сохранен хэштег: %s в чате %s", tag, chat_id)
            except Exception:
                logger.exception("Ошибка при сохранении хэштега %s в чате %s", tag, chat_id)

    except Exception:
        logger.exception("Ошибка сохранения данных сообщения с хэштегами (chat=%s msg=%s)", chat_id, msg_id)
