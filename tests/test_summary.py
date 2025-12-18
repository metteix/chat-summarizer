import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from types import SimpleNamespace
import html

from src.summary.handlers import summary_handler, format_summary, ml_filter_important

@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = SimpleNamespace(id=12345)
    msg.answer = AsyncMock()
    return msg

# --- Основные тесты ---

@pytest.mark.asyncio
async def test_format_summary_no_data():
    mock_chat = SimpleNamespace(
        is_active=True,
        include_tasks=True,
        include_docs=True,
        include_links=True,
        include_mentions=True,
        include_hashtags=True
    )
    with patch("src.summary.handlers.get_chat_settings", AsyncMock(return_value=mock_chat)), \
         patch("src.summary.handlers.get_daily_items", AsyncMock(return_value=([], [], [], [], []))):
        text = await format_summary(12345)
        # Если данных нет, заголовка нет
        assert text.startswith("✅ Нет данных для сводки")
@pytest.mark.asyncio
async def test_format_summary_with_data():
    mock_chat = SimpleNamespace(
        is_active=True,
        include_tasks=True,
        include_docs=True,
        include_links=True,
        include_mentions=True,
        include_hashtags=True
    )

    # Мокаем данные с html и спецсимволами
    TaskMock = SimpleNamespace(task_name="Сделать <тест>")
    DocumentMock = SimpleNamespace(document_name="Документ &1")
    LinkMock = SimpleNamespace(url="https://example.com")
    MentionMock = SimpleNamespace(mention="@user")
    HashtagMock = SimpleNamespace(hashtag="#hashtag")

    with patch("src.summary.handlers.get_chat_settings", AsyncMock(return_value=mock_chat)), \
         patch("src.summary.handlers.get_daily_items", AsyncMock(return_value=(
             [TaskMock],
             [DocumentMock],
             [LinkMock],
             [MentionMock],
             [HashtagMock]
         ))):
        text = await format_summary(12345)

        # Проверяем, что html-символы экранируются
        assert "&lt;тест&gt;" in text
        assert "&amp;1" in text
        assert "Сделать" in text
        assert "Документ" in text
        assert "https://example.com" in text
        assert "@user" in text
        assert "#hashtag" in text

@pytest.mark.asyncio
async def test_summary_handler_calls_answer(mock_message):
    with patch("src.summary.handlers.format_summary", AsyncMock(return_value="SUMMARY_TEXT")):
        await summary_handler(mock_message)
        mock_message.answer.assert_called_once_with("SUMMARY_TEXT", disable_web_page_preview=True)

@pytest.mark.asyncio
async def test_format_summary_inactive_chat():
    mock_chat = SimpleNamespace(is_active=False)
    with patch("src.summary.handlers.get_chat_settings", AsyncMock(return_value=mock_chat)):
        text = await format_summary(12345)
        assert "Бот не активен" in text

@pytest.mark.asyncio
async def test_ml_filter_important_returns_same():
    items = [1,2,3]
    filtered = await ml_filter_important(items)
    assert filtered == items

# --- Крайние и логические тесты ---

@pytest.mark.asyncio
async def test_format_summary_partial_settings():
    mock_chat = SimpleNamespace(
        is_active=True,
        include_tasks=False,
        include_docs=True,
        include_links=False,
        include_mentions=True,
        include_hashtags=False
    )
    DocumentMock = SimpleNamespace(document_name="Документ1")
    MentionMock = SimpleNamespace(mention="@user")
    with patch("src.summary.handlers.get_chat_settings", AsyncMock(return_value=mock_chat)), \
         patch("src.summary.handlers.get_daily_items", AsyncMock(return_value=([], [DocumentMock], [], [MentionMock], []))):
        text = await format_summary(12345)
        # Проверяем, что только включенные категории отображаются
        assert "Документ1" in text
        assert "@user" in text
        assert "Задачи" not in text
        assert "Ссылки" not in text
        assert "#️⃣" not in text

@pytest.mark.asyncio
async def test_format_summary_with_none_values():
    mock_chat = SimpleNamespace(
        is_active=True,
        include_tasks=True,
        include_docs=True,
        include_links=True,
        include_mentions=True,
        include_hashtags=True
    )
    TaskMock = SimpleNamespace(task_name=None)
    DocumentMock = SimpleNamespace(document_name=None)
    LinkMock = SimpleNamespace(url=None)
    MentionMock = SimpleNamespace(mention=None)
    HashtagMock = SimpleNamespace(hashtag=None)

    with patch("src.summary.handlers.get_chat_settings", AsyncMock(return_value=mock_chat)), \
         patch("src.summary.handlers.get_daily_items", AsyncMock(return_value=(
             [TaskMock],
             [DocumentMock],
             [LinkMock],
             [MentionMock],
             [HashtagMock]
         ))):
        text = await format_summary(12345)
        # Должны корректно отображаться "Без описания" или аналог
        assert "Без описания" in text or "Без названия" in text

@pytest.mark.asyncio
async def test_summary_handler_includes_header(mock_message):
    with patch("src.summary.handlers.format_summary", AsyncMock(return_value="📊 Сводка важного за сегодняшний день 📝\n\nDETAILS")):
        await summary_handler(mock_message)
        sent_text = mock_message.answer.call_args[0][0]
        assert sent_text.startswith("📊 Сводка важного")
        assert "DETAILS" in sent_text

@pytest.mark.asyncio
async def test_format_summary_with_some_data():
    mock_chat = SimpleNamespace(
        is_active=True,
        include_tasks=True,
        include_docs=False,
        include_links=False,
        include_mentions=False,
        include_hashtags=False
    )
    TaskMock = SimpleNamespace(task_name="Сделать тест")

    with patch("src.summary.handlers.get_chat_settings", AsyncMock(return_value=mock_chat)), \
         patch("src.summary.handlers.get_daily_items", AsyncMock(return_value=([TaskMock], [], [], [], []))):
        text = await format_summary(12345)
        # Заголовок должен быть
        assert text.startswith("📊 Сводка важного")
        assert "Сделать тест" in text