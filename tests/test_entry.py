import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace

from src.entry.handlers import cmd_start, cmd_on, cmd_off


# ---------- FIXTURES ----------

@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = SimpleNamespace(id=12345)
    return msg


# ---------- /start ----------

@pytest.mark.asyncio
async def test_cmd_start_normal(mock_message):
    await cmd_start(mock_message)

    mock_message.answer.assert_called_once()
    sent_text = mock_message.answer.call_args[0][0]

    assert "Привет" in sent_text
    assert "/on" in sent_text
    assert "/off" in sent_text
    assert "/settings" in sent_text


@pytest.mark.asyncio
async def test_cmd_start_called_twice(mock_message):
    """Повторный вызов /start не ломает состояние"""
    await cmd_start(mock_message)
    await cmd_start(mock_message)

    assert mock_message.answer.call_count == 2


@pytest.mark.asyncio
async def test_cmd_start_no_chat_id(mock_message):
    """Даже без chat.id бот не должен падать"""
    mock_message.chat.id = None

    await cmd_start(mock_message)

    mock_message.answer.assert_called_once()
    assert "Привет" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_cmd_start_empty_message_object():
    """Минимально возможный message"""
    msg = AsyncMock()
    msg.chat = SimpleNamespace(id=123)

    await cmd_start(msg)

    msg.answer.assert_called_once()


# ---------- /on ----------

@pytest.mark.asyncio
async def test_cmd_on_activates_chat(monkeypatch, mock_message):
    activate_mock = AsyncMock()
    monkeypatch.setattr("src.entry.handlers.activate_chat", activate_mock)

    await cmd_on(mock_message)

    activate_mock.assert_called_once_with(mock_message.chat)
    mock_message.answer.assert_called_once()

    sent_text = mock_message.answer.call_args[0][0]
    assert "активирован" in sent_text.lower()


@pytest.mark.asyncio
async def test_cmd_on_called_twice(monkeypatch, mock_message):
    """Повторный /on не должен падать"""
    activate_mock = AsyncMock()
    monkeypatch.setattr("src.entry.handlers.activate_chat", activate_mock)

    await cmd_on(mock_message)
    await cmd_on(mock_message)

    assert activate_mock.call_count == 2
    assert mock_message.answer.call_count == 2


@pytest.mark.asyncio
async def test_cmd_on_activate_chat_error(monkeypatch, mock_message):
    """Если activate_chat падает — хендлер тоже падает (честное поведение)"""
    async def broken_activate(chat):
        raise RuntimeError("DB error")

    monkeypatch.setattr("src.entry.handlers.activate_chat", broken_activate)

    with pytest.raises(RuntimeError):
        await cmd_on(mock_message)


# ---------- /off ----------

@pytest.mark.asyncio
async def test_cmd_off_deactivates_chat(monkeypatch, mock_message):
    deactivate_mock = AsyncMock()
    monkeypatch.setattr("src.entry.handlers.deactivate_chat", deactivate_mock)

    await cmd_off(mock_message)

    deactivate_mock.assert_called_once_with(mock_message.chat.id)
    mock_message.answer.assert_called_once()

    sent_text = mock_message.answer.call_args[0][0]
    assert "остановлен" in sent_text.lower()


@pytest.mark.asyncio
async def test_cmd_off_no_chat_id(monkeypatch, mock_message):
    """Даже если chat.id None — deactivate_chat всё равно вызывается"""
    mock_message.chat.id = None

    deactivate_mock = AsyncMock()
    monkeypatch.setattr("src.entry.handlers.deactivate_chat", deactivate_mock)

    await cmd_off(mock_message)

    deactivate_mock.assert_called_once_with(None)
    mock_message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_cmd_off_called_twice(monkeypatch, mock_message):
    deactivate_mock = AsyncMock()
    monkeypatch.setattr("src.entry.handlers.deactivate_chat", deactivate_mock)

    await cmd_off(mock_message)
    await cmd_off(mock_message)

    assert deactivate_mock.call_count == 2
    assert mock_message.answer.call_count == 2


@pytest.mark.asyncio
async def test_cmd_off_deactivate_error(monkeypatch, mock_message):
    async def broken_deactivate(chat_id):
        raise RuntimeError("DB error")

    monkeypatch.setattr("src.entry.handlers.deactivate_chat", broken_deactivate)

    with pytest.raises(RuntimeError):
        await cmd_off(mock_message)
