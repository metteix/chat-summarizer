import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace
from src.tasks.handlers import get_tasks_handler

@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = AsyncMock()
    msg.chat.id = 12345
    return msg


@pytest.mark.asyncio
async def test_get_tasks_handler_with_tasks(mock_message, monkeypatch):
    fake_tasks = [
        SimpleNamespace(task_name="Первая задача"),
        SimpleNamespace(task_name="Вторая задача")
    ]

    async def fake_get_daily_tasks(chat_id: int):
        return fake_tasks

    monkeypatch.setattr("src.tasks.handlers.get_daily_tasks", fake_get_daily_tasks)
    await get_tasks_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "Первая задача" in sent_text
    assert "Вторая задача" in sent_text

@pytest.mark.asyncio
async def test_get_tasks_handler_no_tasks(mock_message, monkeypatch):
    async def empty_tasks(chat_id: int):
        return []

    monkeypatch.setattr("src.tasks.handlers.get_daily_tasks", empty_tasks)
    await get_tasks_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert sent_text == "✅ Задач за последние 24 часа не найдено."

# ---------- ЛОГИЧЕСКИЕ И КРАЙНИЕ СЛУЧАИ ----------

@pytest.mark.asyncio
async def test_get_tasks_handler_single_task(mock_message, monkeypatch):
    """Одна задача → выводится корректно"""
    fake_tasks = [
        SimpleNamespace(task_name="Единственная задача")
    ]

    async def fake_get_daily_tasks(chat_id: int):
        return fake_tasks

    monkeypatch.setattr("src.tasks.handlers.get_daily_tasks", fake_get_daily_tasks)
    await get_tasks_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "Единственная задача" in sent_text


@pytest.mark.asyncio
async def test_get_tasks_handler_task_with_unicode_and_emojis(mock_message, monkeypatch):
    """Юникод и эмодзи не ломают вывод"""
    fake_tasks = [
        SimpleNamespace(task_name="Сдать лабу №2 🚀")
    ]

    async def fake_get_daily_tasks(chat_id: int):
        return fake_tasks

    monkeypatch.setattr("src.tasks.handlers.get_daily_tasks", fake_get_daily_tasks)
    await get_tasks_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "№2" in sent_text
    assert "🚀" in sent_text


@pytest.mark.asyncio
async def test_get_tasks_handler_very_long_task_name(mock_message, monkeypatch):
    """Очень длинное название задачи"""
    long_name = "Очень важная задача " * 500
    fake_tasks = [
        SimpleNamespace(task_name=long_name)
    ]

    async def fake_get_daily_tasks(chat_id: int):
        return fake_tasks

    monkeypatch.setattr("src.tasks.handlers.get_daily_tasks", fake_get_daily_tasks)
    await get_tasks_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "Очень важная задача" in sent_text


@pytest.mark.asyncio
async def test_get_tasks_handler_multiple_calls(mock_message, monkeypatch):
    """Хендлер можно вызывать повторно без побочных эффектов"""
    fake_tasks = [
        SimpleNamespace(task_name="Повторяемая задача")
    ]

    async def fake_get_daily_tasks(chat_id: int):
        return fake_tasks

    monkeypatch.setattr("src.tasks.handlers.get_daily_tasks", fake_get_daily_tasks)

    await get_tasks_handler(mock_message)
    await get_tasks_handler(mock_message)

    assert mock_message.answer.call_count == 2


@pytest.mark.asyncio
async def test_get_tasks_handler_ignores_extra_fields(mock_message, monkeypatch):
    """Лишние поля в объекте задачи не ломают хендлер"""
    fake_tasks = [
        SimpleNamespace(
            task_name="Задача с лишними полями",
            context="Контекст",
            random_field=123
        )
    ]

    async def fake_get_daily_tasks(chat_id: int):
        return fake_tasks

    monkeypatch.setattr("src.tasks.handlers.get_daily_tasks", fake_get_daily_tasks)
    await get_tasks_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "Задача с лишними полями" in sent_text
