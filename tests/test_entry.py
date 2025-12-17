import pytest
from unittest.mock import AsyncMock
from src.entry.handlers import cmd_start
from types import SimpleNamespace


@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = SimpleNamespace(id=12345)
    msg.from_user = SimpleNamespace(id=11111)
    return msg


@pytest.mark.asyncio
async def test_cmd_start_normal(mock_message):
    await cmd_start(mock_message)

    # Проверяем, что отправлено приветственное сообщение
    assert mock_message.answer.call_count == 1
    sent_text = mock_message.answer.call_args[0][0]

    # Логическая проверка содержимого
    assert "Привет" in sent_text
    assert "/help" in sent_text


@pytest.mark.asyncio
async def test_cmd_start_no_user_id(mock_message):
    # Удаляем id пользователя
    mock_message.from_user.id = None

    await cmd_start(mock_message)

    # Должно отправиться сообщение без ошибок
    assert mock_message.answer.call_count == 1
    sent_text = mock_message.answer.call_args[0][0]
    assert "Привет" in sent_text
    assert "/help" in sent_text


@pytest.mark.asyncio
async def test_cmd_start_no_chat_id(mock_message):
    # Удаляем id чата
    mock_message.chat.id = None

    await cmd_start(mock_message)

    # Бот не должен падать
    assert mock_message.answer.call_count == 1
    sent_text = mock_message.answer.call_args[0][0]
    assert "Привет" in sent_text
    assert "/help" in sent_text
