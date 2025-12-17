import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace
from aiogram.types import Message

from middlewares.middleware import CollectorMiddleware
from database.models import Mention, Hashtag, Document, Link, Task


# --- Фикстуры ---
@pytest.fixture
def middleware():
    return CollectorMiddleware()

@pytest.fixture
def handler():
    return AsyncMock()

@pytest.fixture
def session():
    s = AsyncMock()
    s.add = AsyncMock()
    s.commit = AsyncMock()
    s.rollback = AsyncMock()
    return s


# --- Вспомогательная функция для создания сообщений ---
def make_message(
    text=None,
    entities=None,
    document=None
):
    msg = AsyncMock(spec=Message)
    msg.text = text
    msg.caption = None
    msg.entities = entities
    msg.caption_entities = None
    msg.document = document
    msg.chat = SimpleNamespace(id=123)
    msg.message_id = 456
    return msg


# --- 1. Команда не сохраняется ---
@pytest.mark.asyncio
async def test_skip_command_message(middleware, handler, session):
    msg = make_message(text="/start")

    await middleware(handler, msg, {"session": session})

    session.add.assert_not_called()
    session.commit.assert_not_called()
    handler.assert_called_once()


# --- 2. Обычный текст без сущностей ---
@pytest.mark.asyncio
async def test_plain_text_no_entities(middleware, handler, session):
    msg = make_message(text="просто сообщение")

    await middleware(handler, msg, {"session": session})

    session.add.assert_not_called()
    session.commit.assert_called_once()
    handler.assert_called_once()


# --- 3. Документ ---
@pytest.mark.asyncio
async def test_document_collected(middleware, handler, session):
    document = SimpleNamespace(
        file_name="file.pdf",
        file_id="file_123"
    )

    msg = make_message(
        text="описание",
        document=document
    )

    await middleware(handler, msg, {"session": session})

    added = session.add.call_args[0][0]
    assert isinstance(added, Document)
    assert added.document_name == "file.pdf"
    assert added.file_id == "file_123"

    handler.assert_called_once()


# --- 4. Hashtag ---
@pytest.mark.asyncio
async def test_hashtag_collected(middleware, handler, session):
    entity = SimpleNamespace(
        type="hashtag",
        extract_from=lambda text: "#test"
    )

    msg = make_message(
        text="текст #test",
        entities=[entity]
    )

    await middleware(handler, msg, {"session": session})
    added = session.add.call_args[0][0]
    assert isinstance(added, Hashtag)
    assert added.hashtag == "#test"

    handler.assert_called_once()


# --- 5. Link ---
@pytest.mark.asyncio
async def test_link_collected(middleware, handler, session):
    entity = SimpleNamespace(
        type="url",
        extract_from=lambda text: "https://example.com"
    )

    msg = make_message(
        text="https://example.com",
        entities=[entity]
    )

    await middleware(handler, msg, {"session": session})

    added = session.add.call_args[0][0]
    assert isinstance(added, Link)
    assert added.url == "https://example.com"

    handler.assert_called_once()


# --- 6. Mention ---
@pytest.mark.asyncio
async def test_mention_collected(middleware, handler, session):
    entity = SimpleNamespace(
        type="mention",
        extract_from=lambda text: "@user"
    )

    msg = make_message(
        text="привет @user",
        entities=[entity]
    )

    await middleware(handler, msg, {"session": session})

    added = session.add.call_args[0][0]
    assert isinstance(added, Mention)
    assert added.mention == "@user"

    handler.assert_called_once()


# --- 7. Task по ключевым словам ---
@pytest.mark.asyncio
async def test_task_created_from_keywords(middleware, handler, session):
    msg = make_message(text="надо сделать домашку")

    await middleware(handler, msg, {"session": session})

    added = session.add.call_args[0][0]
    assert isinstance(added, Task)
    assert "надо" in added.task_name.lower()

    handler.assert_called_once()


# --- 8. Короткий текст → Task не создаётся ---
@pytest.mark.asyncio
async def test_short_text_not_task(middleware, handler, session):
    msg = make_message(text="надо")

    await middleware(handler, msg, {"session": session})

    session.add.assert_not_called()
    session.commit.assert_called_once()
    handler.assert_called_once()


# --- 9. Ошибка commit → rollback ---
@pytest.mark.asyncio
async def test_commit_error_rollbacks(middleware, handler, session):
    session.commit.side_effect = Exception("DB error")

    msg = make_message(text="надо сделать отчет")

    await middleware(handler, msg, {"session": session})

    session.rollback.assert_called_once()
    handler.assert_called_once()


# --- 10. Handler вызывается всегда ---
@pytest.mark.asyncio
async def test_handler_always_called(middleware, handler, session):
    msg = make_message(text="любой текст")

    await middleware(handler, msg, {"session": session})

    handler.assert_called_once()
