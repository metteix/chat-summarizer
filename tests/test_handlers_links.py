import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace
from src.links.handlers import get_links_handler


@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = AsyncMock()
    msg.chat.id = 12345
    msg.answer = AsyncMock()
    msg.answer.return_value = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_get_links_handler_with_links(mock_message, monkeypatch):
    fake_links = [
        SimpleNamespace(url="https://example.com/1", about="Первый линк", context=None),
        SimpleNamespace(url="https://example.com/2", about=None, context="Второй линк")
    ]

    async def fake_get_daily_links(chat_id: int):
        return fake_links

    async def fake_process_items_pipeline(all_items, item_type, model_class):
        return all_items

    monkeypatch.setattr("src.links.handlers.get_daily_links", fake_get_daily_links)
    monkeypatch.setattr("src.links.handlers.process_items_pipeline", fake_process_items_pipeline)

    await get_links_handler(mock_message)

    mock_message.answer.assert_called_with("🔎 Проверяю ссылки...")
    status_msg = mock_message.answer.return_value
    sent_text = status_msg.edit_text.call_args[0][0]

    assert "https://example.com/1" in sent_text
    assert "Первый линк" in sent_text
    assert "https://example.com/2" in sent_text
    assert "Второй линк" in sent_text


@pytest.mark.asyncio
async def test_get_links_handler_no_links(mock_message, monkeypatch):
    async def empty_links(chat_id: int):
        return []

    monkeypatch.setattr("src.links.handlers.get_daily_links", empty_links)

    await get_links_handler(mock_message)
    mock_message.answer.assert_called_once_with("📭 Ссылок за последние сутки не было.")


@pytest.mark.asyncio
async def test_get_links_handler_pipeline_error(mock_message, monkeypatch):
    fake_links = [SimpleNamespace(url="https://ex.com", about="Link", context=None)]

    async def fake_get_daily_links(chat_id: int):
        return fake_links

    async def fake_process_items_pipeline(all_items, item_type, model_class):
        return None

    monkeypatch.setattr("src.links.handlers.get_daily_links", fake_get_daily_links)
    monkeypatch.setattr("src.links.handlers.process_items_pipeline", fake_process_items_pipeline)

    await get_links_handler(mock_message)

    status_msg = mock_message.answer.return_value
    assert "Временная ошибка Gemini" in status_msg.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_get_links_handler_special_characters(mock_message, monkeypatch):
    fake_links = [
        SimpleNamespace(url="https://example.com", about="Тест <открытый тег>", context=None)
    ]

    async def fake_get_daily_links(chat_id: int):
        return fake_links

    async def fake_process_items_pipeline(all_items, item_type, model_class):
        return all_items

    monkeypatch.setattr("src.links.handlers.get_daily_links", fake_get_daily_links)
    monkeypatch.setattr("src.links.handlers.process_items_pipeline", fake_process_items_pipeline)

    await get_links_handler(mock_message)

    status_msg = mock_message.answer.return_value
    sent_text = status_msg.edit_text.call_args[0][0]

    assert "&lt;" in sent_text
    assert "&gt;" in sent_text


@pytest.mark.asyncio
async def test_get_links_handler_many_links(mock_message, monkeypatch):
    fake_links = [
        SimpleNamespace(url=f"https://example.com/{i}", about=f"Описание {i}", context=None)
        for i in range(10)
    ]

    async def fake_get_daily_links(chat_id: int):
        return fake_links

    async def fake_process_items_pipeline(all_items, item_type, model_class):
        return all_items

    monkeypatch.setattr("src.links.handlers.get_daily_links", fake_get_daily_links)
    monkeypatch.setattr("src.links.handlers.process_items_pipeline", fake_process_items_pipeline)

    await get_links_handler(mock_message)

    status_msg = mock_message.answer.return_value
    sent_text = status_msg.edit_text.call_args[0][0]

    assert "Описание 0" in sent_text
    assert "Описание 9" in sent_text