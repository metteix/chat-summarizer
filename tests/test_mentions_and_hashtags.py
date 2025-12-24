import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace
from src.mentions.handlers import get_mentions_handler
from src.hashtags.handlers import get_hashtags_handler


@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = AsyncMock()
    msg.chat.id = -10012345
    msg.answer = AsyncMock()

    msg.answer.return_value = AsyncMock()
    return msg


async def fake_process_items_pipeline(all_items, item_type, model_class):
    return all_items


@pytest.mark.asyncio
async def test_get_mentions_handler_with_mentions(mock_message, monkeypatch):
    fake_mentions = [
        SimpleNamespace(message_id=1, mention="@user1", about="Тема 1", context=None),
        SimpleNamespace(message_id=2, mention="@user2", about=None, context="Тема 2")
    ]

    async def fake_get_daily_mentions(chat_id: int):
        return fake_mentions

    monkeypatch.setattr("src.mentions.handlers.get_daily_mentions", fake_get_daily_mentions)
    monkeypatch.setattr("src.mentions.handlers.process_items_pipeline", fake_process_items_pipeline)

    await get_mentions_handler(mock_message)

    mock_message.answer.assert_called_with("🔎 Проверяю, кого звали по делу...")
    status_msg = mock_message.answer.return_value
    sent_text = status_msg.edit_text.call_args[0][0]

    assert "@user1" in sent_text
    assert "@user2" in sent_text
    assert "https://t.me/c/12345/1" in sent_text
    assert "Тема 1" in sent_text


@pytest.mark.asyncio
async def test_get_mentions_handler_no_mentions(mock_message, monkeypatch):
    async def empty_mentions(chat_id: int):
        return []

    monkeypatch.setattr("src.mentions.handlers.get_daily_mentions", empty_mentions)

    await get_mentions_handler(mock_message)

    mock_message.answer.assert_called_once_with("🔕 Упоминаний за сутки не найдено.")



@pytest.mark.asyncio
async def test_get_hashtags_handler_with_hashtags(mock_message, monkeypatch):
    fake_hashtags = [
        SimpleNamespace(message_id=10, hashtag="#отчет", about="Работа сделана", context=None),
        SimpleNamespace(message_id=20, hashtag="#важно", about=None, context="Срочный апдейт")
    ]

    async def fake_get_daily_hashtags(chat_id: int):
        return fake_hashtags

    monkeypatch.setattr("src.hashtags.handlers.get_daily_hashtags", fake_get_daily_hashtags)
    monkeypatch.setattr("src.hashtags.handlers.process_items_pipeline", fake_process_items_pipeline)

    await get_hashtags_handler(mock_message)

    mock_message.answer.assert_called_with("🔎 Анализирую хэштеги...")

    status_msg = mock_message.answer.return_value
    sent_text = status_msg.edit_text.call_args[0][0]

    assert "#отчет" in sent_text
    assert "#важно" in sent_text
    assert "https://t.me/c/12345/10" in sent_text
    assert "Работа сделана" in sent_text


@pytest.mark.asyncio
async def test_get_hashtags_handler_no_hashtags(mock_message, monkeypatch):
    async def empty_hashtags(chat_id: int):
        return []

    monkeypatch.setattr("src.hashtags.handlers.get_daily_hashtags", empty_hashtags)

    await get_hashtags_handler(mock_message)

    mock_message.answer.assert_called_once_with("#️⃣ Хэштегов за сутки не найдено.")


@pytest.mark.asyncio
async def test_get_hashtags_handler_special_chars(mock_message, monkeypatch):
    fake_hashtags = [
        SimpleNamespace(message_id=1, hashtag="#тест", about="Запрос <script>", context=None)
    ]

    async def fake_get_daily_hashtags(chat_id: int):
        return fake_hashtags

    monkeypatch.setattr("src.hashtags.handlers.get_daily_hashtags", fake_get_daily_hashtags)
    monkeypatch.setattr("src.hashtags.handlers.process_items_pipeline", fake_process_items_pipeline)

    await get_hashtags_handler(mock_message)

    status_msg = mock_message.answer.return_value
    sent_text = status_msg.edit_text.call_args[0][0]

    assert "&lt;script&gt;" in sent_text


@pytest.mark.asyncio
async def test_get_mentions_handler_pipeline_error(mock_message, monkeypatch):
    async def fake_get_daily_mentions(chat_id: int):
        return [SimpleNamespace(message_id=1, mention="@u", about="x", context="y")]

    async def fake_pipeline_error(all_items, item_type, model_class):
        return None

    monkeypatch.setattr("src.mentions.handlers.get_daily_mentions", fake_get_daily_mentions)
    monkeypatch.setattr("src.mentions.handlers.process_items_pipeline", fake_pipeline_error)

    await get_mentions_handler(mock_message)

    status_msg = mock_message.answer.return_value
    assert "Временная ошибка Gemini" in status_msg.edit_text.call_args[0][0]