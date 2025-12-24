import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace
from src.summary.handlers import cmd_summary


@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = AsyncMock()
    msg.chat.id = 12345
    msg.chat.username = "test_chat"
    msg.answer = AsyncMock()
    msg.answer.return_value = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_cmd_summary_no_settings(mock_message, monkeypatch):
    async def fake_get_settings(chat_id):
        return None

    monkeypatch.setattr("src.summary.handlers.get_chat_settings", fake_get_settings)

    await cmd_summary(mock_message)

    mock_message.answer.assert_called_once_with("❌ Бот не активирован. Напишите /on")


@pytest.mark.asyncio
async def test_cmd_summary_no_data(mock_message, monkeypatch):
    async def fake_get_settings(chat_id):
        return SimpleNamespace(include_tasks=True)

    async def fake_get_daily_data(chat_id):
        return {"tasks": [], "links": []}

    monkeypatch.setattr("src.summary.handlers.get_chat_settings", fake_get_settings)
    monkeypatch.setattr("src.summary.handlers.get_daily_data", fake_get_daily_data)

    await cmd_summary(mock_message)

    mock_message.answer.assert_called_once_with("📭 За последние 24 часа данных не найдено.")


@pytest.mark.asyncio
async def test_cmd_summary_full_success(mock_message, monkeypatch):
    fake_settings = SimpleNamespace(
        include_tasks=True, include_links=True, include_docs=True,
        include_mentions=True, include_hashtags=True
    )

    fake_data = {
        "tasks": [SimpleNamespace(message_id=1, task_name="Task 1", about=None)],
        "links": [SimpleNamespace(url="https://test.com", about="Link 1")],
        "documents": [SimpleNamespace(message_id=2, document_name="doc.pdf", about=None)],
        "mentions": [SimpleNamespace(message_id=3, mention="@user", about=None)],
        "hashtags": [SimpleNamespace(message_id=4, hashtag="#tag", about=None)]
    }

    async def fake_get_settings(chat_id): return fake_settings

    async def fake_get_daily_data(chat_id): return fake_data

    async def fake_pipeline(items, item_type, model_class): return items

    monkeypatch.setattr("src.summary.handlers.get_chat_settings", fake_get_settings)
    monkeypatch.setattr("src.summary.handlers.get_daily_data", fake_get_daily_data)
    monkeypatch.setattr("src.summary.handlers.process_items_pipeline", fake_pipeline)

    await cmd_summary(mock_message)

    status_msg = mock_message.answer.return_value
    sent_text = status_msg.edit_text.call_args[0][0]

    assert "📊 СВОДКА ЗА 24 ЧАСА" in sent_text
    assert "Task 1" in sent_text
    assert "https://test.com" in sent_text
    assert "doc.pdf" in sent_text
    assert "@user" in sent_text
    assert "#tag" in sent_text
    assert "https://t.me/test_chat/1" in sent_text


@pytest.mark.asyncio
async def test_cmd_summary_pipeline_error(mock_message, monkeypatch):
    fake_settings = SimpleNamespace(include_tasks=True, include_links=False, include_docs=False, include_mentions=False,
                                    include_hashtags=False)
    fake_data = {"tasks": [SimpleNamespace(message_id=1, task_name="Task", about=None)]}

    async def fake_get_settings(chat_id): return fake_settings

    async def fake_get_daily_data(chat_id): return fake_data

    async def fake_pipeline_error(items, item_type, model_class): return None

    monkeypatch.setattr("src.summary.handlers.get_chat_settings", fake_get_settings)
    monkeypatch.setattr("src.summary.handlers.get_daily_data", fake_get_daily_data)
    monkeypatch.setattr("src.summary.handlers.process_items_pipeline", fake_pipeline_error)

    await cmd_summary(mock_message)

    status_msg = mock_message.answer.return_value
    assert "Временная ошибка Gemini" in status_msg.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_cmd_summary_all_filtered(mock_message, monkeypatch):
    fake_settings = SimpleNamespace(include_tasks=True, include_links=False, include_docs=False, include_mentions=False,
                                    include_hashtags=False)
    fake_data = {"tasks": [SimpleNamespace(message_id=1, task_name="Noise", about=None)]}

    async def fake_get_settings(chat_id): return fake_settings

    async def fake_get_daily_data(chat_id): return fake_data

    async def fake_pipeline_empty(items, item_type, model_class): return []

    monkeypatch.setattr("src.summary.handlers.get_chat_settings", fake_get_settings)
    monkeypatch.setattr("src.summary.handlers.get_daily_data", fake_get_daily_data)
    monkeypatch.setattr("src.summary.handlers.process_items_pipeline", fake_pipeline_empty)

    await cmd_summary(mock_message)

    status_msg = mock_message.answer.return_value
    assert "нейросеть посчитала всё это неважным" in status_msg.edit_text.call_args[0][0]