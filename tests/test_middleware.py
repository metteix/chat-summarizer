import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace

from aiogram.types import Message
from middlewares.middleware import CollectorMiddleware


# ---------- helpers ----------

def make_message(
    text="hello",
    *,
    chat_id=123,
    message_id=10,
    document=None,
    entities=None,
    caption_entities=None,
):
    msg = AsyncMock(spec=Message)
    msg.text = text
    msg.caption = None
    msg.chat = SimpleNamespace(id=chat_id)
    msg.message_id = message_id
    msg.document = document
    msg.entities = entities
    msg.caption_entities = caption_entities
    return msg


# ---------- fixtures ----------

@pytest.fixture
def handler():
    return AsyncMock()


@pytest.fixture
def session():
    session = AsyncMock()

    session.add = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    chat = SimpleNamespace(chat_id=123, is_active=True)

    result = SimpleNamespace(
        scalar_one_or_none=lambda: chat
    )

    session.execute = AsyncMock(return_value=result)

    return session


@pytest.fixture
def middleware():
    return CollectorMiddleware()


# ---------- early exits ----------

@pytest.mark.asyncio
async def test_skip_non_message(middleware, handler):
    await middleware(handler, object(), {})
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_skip_without_session(middleware, handler):
    msg = make_message()
    await middleware(handler, msg, {})
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_skip_command_message(middleware, handler, session):
    msg = make_message(text="/start")
    await middleware(handler, msg, {"session": session})

    session.add.assert_not_called()
    session.commit.assert_not_called()
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_skip_inactive_chat(middleware, handler, session):
    session.execute.return_value = SimpleNamespace(
        scalar_one_or_none=lambda: SimpleNamespace(is_active=False)
    )

    msg = make_message(text="обычный текст")
    await middleware(handler, msg, {"session": session})

    session.add.assert_not_called()
    session.commit.assert_not_called()
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_skip_chat_not_found(middleware, handler, session):
    session.execute.return_value = SimpleNamespace(
        scalar_one_or_none=lambda: None
    )

    msg = make_message(text="обычный текст")
    await middleware(handler, msg, {"session": session})

    session.add.assert_not_called()
    session.commit.assert_not_called()
    handler.assert_called_once()


# ---------- collecting ----------

@pytest.mark.asyncio
async def test_document_collected(middleware, handler, session):
    document = SimpleNamespace(file_name="file.pdf", file_id="123")

    msg = make_message(text="описание", document=document)
    await middleware(handler, msg, {"session": session})

    session.add.assert_called()
    session.commit.assert_called_once()


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

    session.add.assert_called()
    session.commit.assert_called_once()


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

    session.add.assert_called()
    session.commit.assert_called_once()


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

    session.add.assert_called()
    session.commit.assert_called_once()


# ---------- tasks ----------

@pytest.mark.asyncio
async def test_task_created_from_keywords(middleware, handler, session):
    msg = make_message(text="надо сделать домашку")
    await middleware(handler, msg, {"session": session})

    session.add.assert_called()
    session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_short_text_not_task(middleware, handler, session):
    msg = make_message(text="надо")
    await middleware(handler, msg, {"session": session})

    session.add.assert_not_called()
    session.commit.assert_called_once()


# ---------- transactions ----------

@pytest.mark.asyncio
async def test_commit_error_rollbacks(middleware, handler, session):
    session.commit.side_effect = Exception("DB error")

    msg = make_message(text="надо сделать отчет")
    await middleware(handler, msg, {"session": session})

    session.rollback.assert_called_once()
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_handler_always_called(middleware, handler, session):
    msg = make_message(text="обычный текст")
    await middleware(handler, msg, {"session": session})

    handler.assert_called_once()
