# tests/test_handlers_links.py
import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace
from src.links.handlers import get_links_handler

@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = AsyncMock()
    msg.chat.id = 12345
    return msg

@pytest.mark.asyncio
async def test_get_links_handler_with_links(mock_message, monkeypatch):
    fake_links = [
        SimpleNamespace(url="https://example.com/1", context="Первый линк"),
        SimpleNamespace(url="https://example.com/2", context="Второй линк")
    ]

    async def fake_get_daily_links(chat_id: int):
        return fake_links

    monkeypatch.setattr("src.links.handlers.get_daily_links", fake_get_daily_links)
    await get_links_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
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

    sent_text = mock_message.answer.call_args[0][0]
    assert sent_text == "📭 Ссылок за последние сутки не было."

@pytest.mark.asyncio
async def test_get_links_handler_links_without_context(mock_message, monkeypatch):
    fake_links = [
        SimpleNamespace(url="https://example.com/1", context=""),
        SimpleNamespace(url="https://example.com/2", context=None)
    ]

    async def fake_get_daily_links(chat_id: int):
        return fake_links

    monkeypatch.setattr("src.links.handlers.get_daily_links", fake_get_daily_links)
    await get_links_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "https://example.com/1" in sent_text
    assert "https://example.com/2" in sent_text

# @pytest.mark.asyncio
# async def test_get_links_handler_long_texts(mock_message, monkeypatch):
#     long_url = "https://example.com/" + "a"*500
#     long_context = "К" * 1000
#     fake_links = [SimpleNamespace(url=long_url, context=long_context)]
#
#     async def fake_get_daily_links(chat_id: int):
#         return fake_links
#
#     monkeypatch.setattr("src.links.handlers.get_daily_links", fake_get_daily_links)
#     await get_links_handler(mock_message)
#
#     sent_text = mock_message.answer.call_args[0][0]
#     assert long_url in sent_text
#     assert long_context in sent_text

@pytest.mark.asyncio
async def test_get_links_handler_special_characters(mock_message, monkeypatch):
    fake_links = [
        SimpleNamespace(url="https://example.com/?q=<>&", context="Тест & эмодзи 🚀")
    ]

    async def fake_get_daily_links(chat_id: int):
        return fake_links

    monkeypatch.setattr("src.links.handlers.get_daily_links", fake_get_daily_links)
    await get_links_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "<>" in sent_text
    assert "🚀" in sent_text

@pytest.mark.asyncio
async def test_get_links_handler_many_links(mock_message, monkeypatch):
    fake_links = [SimpleNamespace(url=f"https://example.com/{i}", context=f"Контекст {i}") for i in range(100)]

    async def fake_get_daily_links(chat_id: int):
        return fake_links

    monkeypatch.setattr("src.links.handlers.get_daily_links", fake_get_daily_links)
    await get_links_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    # Проверим несколько первых и последних ссылок
    assert "https://example.com/0" in sent_text
    assert "Контекст 0" in sent_text
    assert "https://example.com/99" in sent_text
    assert "Контекст 99" in sent_text
