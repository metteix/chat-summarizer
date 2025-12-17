import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace
from src.mentions.handlers import get_mentions_handler
from src.hashtags.handlers import get_mentions_handler as get_hashtags_handler

@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = AsyncMock()
    msg.chat.id = 12345
    return msg

# --- MENTIONS ---
@pytest.mark.asyncio
async def test_get_mentions_handler_with_mentions(mock_message, monkeypatch):
    fake_mentions = [
        SimpleNamespace(message_id=1, mention="@user1", context="Первое упоминание"),
        SimpleNamespace(message_id=2, mention="@user2", context="Второе упоминание")
    ]

    async def fake_get_daily_mentions(chat_id: int):
        return fake_mentions

    monkeypatch.setattr("src.mentions.handlers.get_daily_mentions", fake_get_daily_mentions)
    await get_mentions_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "@user1" in sent_text
    assert "@user2" in sent_text
    assert "https://t.me/c/12345/1" in sent_text
    assert "https://t.me/c/12345/2" in sent_text

@pytest.mark.asyncio
async def test_get_mentions_handler_no_mentions(mock_message, monkeypatch):
    async def empty_mentions(chat_id: int):
        return []

    monkeypatch.setattr("src.mentions.handlers.get_daily_mentions", empty_mentions)
    await get_mentions_handler(mock_message)

    # Просто проверяем текст, disable_web_page_preview тут нет
    sent_text = mock_message.answer.call_args[0][0]
    assert sent_text == "🔕 Важных упоминаний за сутки не найдено."

# --- HASHTAGS ---
@pytest.mark.asyncio
async def test_get_hashtags_handler_with_hashtags(mock_message, monkeypatch):
    fake_hashtags = [
        SimpleNamespace(message_id=1, hashtag="#test1", context="Первый хэштег"),
        SimpleNamespace(message_id=2, hashtag="#test2", context="Второй хэштег")
    ]

    async def fake_get_daily_hashtags(chat_id: int):
        return fake_hashtags

    monkeypatch.setattr("src.hashtags.handlers.get_daily_hashtags", fake_get_daily_hashtags)
    await get_hashtags_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "#test1" in sent_text
    assert "#test2" in sent_text
    assert "https://t.me/c/12345/1" in sent_text
    assert "https://t.me/c/12345/2" in sent_text

@pytest.mark.asyncio
async def test_get_hashtags_handler_no_hashtags(mock_message, monkeypatch):
    async def empty_hashtags(chat_id: int):
        return []

    monkeypatch.setattr("src.hashtags.handlers.get_daily_hashtags", empty_hashtags)
    await get_hashtags_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert sent_text == "#️⃣ Важных хэштегов за сутки не найдено."

@pytest.mark.asyncio
async def test_get_mentions_handler_without_context(mock_message, monkeypatch):
    fake_mentions = [
        SimpleNamespace(message_id=1, mention="@user1", context=None),
    ]

    async def fake_get_daily_mentions(chat_id: int):
        return fake_mentions

    monkeypatch.setattr("src.mentions.handlers.get_daily_mentions", fake_get_daily_mentions)
    await get_mentions_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "@user1" in sent_text
    assert "https://t.me/c/12345/1" in sent_text

# @pytest.mark.asyncio
# async def test_get_mentions_handler_long_context(mock_message, monkeypatch):
#     long_context = "А" * 1000
#     fake_mentions = [
#         SimpleNamespace(message_id=1, mention="@user1", context=long_context),
#     ]
#
#     async def fake_get_daily_mentions(chat_id: int):
#         return fake_mentions
#
#     monkeypatch.setattr("src.mentions.handlers.get_daily_mentions", fake_get_daily_mentions)
#     await get_mentions_handler(mock_message)
#
#     sent_text = mock_message.answer.call_args[0][0]
#     assert long_context in sent_text

@pytest.mark.asyncio
async def test_get_mentions_handler_many_mentions(mock_message, monkeypatch):
    fake_mentions = [
        SimpleNamespace(
            message_id=i,
            mention=f"@user{i}",
            context=f"Контекст {i}"
        )
        for i in range(20)
    ]

    async def fake_get_daily_mentions(chat_id: int):
        return fake_mentions

    monkeypatch.setattr("src.mentions.handlers.get_daily_mentions", fake_get_daily_mentions)
    await get_mentions_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "@user0" in sent_text
    assert "@user19" in sent_text

@pytest.mark.asyncio
async def test_get_hashtags_handler_without_context(mock_message, monkeypatch):
    fake_hashtags = [
        SimpleNamespace(message_id=1, hashtag="#test", context=None),
    ]

    async def fake_get_daily_hashtags(chat_id: int):
        return fake_hashtags

    monkeypatch.setattr("src.hashtags.handlers.get_daily_hashtags", fake_get_daily_hashtags)
    await get_hashtags_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "#test" in sent_text
    assert "https://t.me/c/12345/1" in sent_text

@pytest.mark.asyncio
async def test_get_hashtags_handler_special_chars(mock_message, monkeypatch):
    fake_hashtags = [
        SimpleNamespace(
            message_id=1,
            hashtag="#тест🚀",
            context="Контекст с эмодзи 😎 & символами <>"
        )
    ]

    async def fake_get_daily_hashtags(chat_id: int):
        return fake_hashtags

    monkeypatch.setattr("src.hashtags.handlers.get_daily_hashtags", fake_get_daily_hashtags)
    await get_hashtags_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "#тест🚀" in sent_text

@pytest.mark.asyncio
async def test_get_hashtags_handler_many_hashtags(mock_message, monkeypatch):
    fake_hashtags = [
        SimpleNamespace(
            message_id=i,
            hashtag=f"#tag{i}",
            context=f"Контекст {i}"
        )
        for i in range(30)
    ]

    async def fake_get_daily_hashtags(chat_id: int):
        return fake_hashtags

    monkeypatch.setattr("src.hashtags.handlers.get_daily_hashtags", fake_get_daily_hashtags)
    await get_hashtags_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "#tag0" in sent_text
    assert "#tag29" in sent_text

