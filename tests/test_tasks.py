import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace
from src.tasks.handlers import get_tasks_handler


@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = AsyncMock()
    msg.chat.id = 12345
    msg.chat.username = "test_chat"
    msg.answer = AsyncMock()
    msg.answer.return_value = AsyncMock()
    return msg


async def fake_process_items_pipeline(all_items, item_type, model_class):
    return all_items


@pytest.mark.asyncio
async def test_get_tasks_handler_with_tasks(mock_message, monkeypatch):
    fake_tasks = [
        SimpleNamespace(message_id=1, task_name="Первая задача", about=None)
    ]

    async def fake_get_daily_tasks(chat_id: int):
        return fake_tasks

    monkeypatch.setattr("src.tasks.handlers.get_daily_tasks", fake_get_daily_tasks)
    monkeypatch.setattr("src.tasks.handlers.process_items_pipeline", fake_process_items_pipeline)

    await get_tasks_handler(mock_message)

    mock_message.answer.assert_called_with("🔎 Анализирую задачи и дедлайны...")
    status_msg = mock_message.answer.return_value
    sent_text = status_msg.edit_text.call_args[0][0]

    assert "Первая задача" in sent_text
    assert "https://t.me/test_chat/1" in sent_text


@pytest.mark.asyncio
async def test_get_tasks_handler_no_tasks(mock_message, monkeypatch):
    async def empty_tasks(chat_id: int):
        return []

    monkeypatch.setattr("src.tasks.handlers.get_daily_tasks", empty_tasks)
    await get_tasks_handler(mock_message)
    mock_message.answer.assert_called_once_with("✅ Задач за последние 24 часа не найдено.")