import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace
from src.docs.handlers import get_documents_handler


@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = AsyncMock()
    msg.chat.id = 12345
    msg.chat.username = "testchat"
    msg.answer = AsyncMock()
    # Настраиваем возврат значения для status_msg
    msg.answer.return_value = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_get_documents_handler_with_docs(mock_message, monkeypatch):
    # Данные для теста
    fake_docs = [
        SimpleNamespace(
            message_id=1,
            document_name="doc1.pdf",
            about="Первый документ",
            created_at=None
        ),
        SimpleNamespace(
            message_id=2,
            document_name="doc2.pdf",
            about="Второй документ",
            created_at=None
        ),
    ]

    # Мокаем функции получения данных и пайплайна
    async def fake_get_daily_documents(chat_id: int):
        return fake_docs

    async def fake_process_items_pipeline(all_items, item_type, model_class):
        return all_items

    monkeypatch.setattr("src.docs.handlers.get_daily_documents", fake_get_daily_documents)
    monkeypatch.setattr("src.docs.handlers.process_items_pipeline", fake_process_items_pipeline)

    # Запуск хендлера
    await get_documents_handler(mock_message)

    # 1. Проверяем, что ответ "Анализирую..." был отправлен один раз
    assert mock_message.answer.call_count == 1
    assert mock_message.answer.call_args[0][0] == "🔎 Анализирую файлы..."

    # 2. Получаем объект сообщения, которое редактировалось (status_msg)
    status_msg = mock_message.answer.return_value

    # Проверяем, что edit_text был вызван
    assert status_msg.edit_text.called
    sent_text = status_msg.edit_text.call_args[0][0]

    # 3. Проверяем содержимое финального текста
    assert "<b>📂 Важные документы за сутки:</b>" in sent_text
    assert "Первый документ" in sent_text
    assert "Второй документ" in sent_text
    assert "https://t.me/testchat/1" in sent_text
    assert "https://t.me/testchat/2" in sent_text


@pytest.mark.asyncio
async def test_get_documents_handler_no_docs(mock_message, monkeypatch):
    async def empty_docs(chat_id: int):
        return []

    monkeypatch.setattr("src.docs.handlers.get_daily_documents", empty_docs)

    await get_documents_handler(mock_message)

    mock_message.answer.assert_called_once_with("📭 Документов за последние сутки не было.")


@pytest.mark.asyncio
async def test_get_documents_handler_pipeline_error(mock_message, monkeypatch):
    fake_docs = [SimpleNamespace(message_id=1, document_name="doc1.pdf", about="Документ", created_at=None)]

    async def fake_get_daily_documents(chat_id: int):
        return fake_docs

    async def fake_process_items_pipeline(all_items, item_type, model_class):
        return None

    monkeypatch.setattr("src.docs.handlers.get_daily_documents", fake_get_daily_documents)
    monkeypatch.setattr("src.docs.handlers.process_items_pipeline", fake_process_items_pipeline)

    await get_documents_handler(mock_message)

    status_msg = mock_message.answer.return_value
    assert "Временная ошибка" in status_msg.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_get_documents_handler_empty_after_filter(mock_message, monkeypatch):
    fake_docs = [SimpleNamespace(message_id=1, document_name="doc1.pdf", about="Документ", created_at=None)]

    async def fake_get_daily_documents(chat_id: int):
        return fake_docs

    async def fake_process_items_pipeline(all_items, item_type, model_class):
        return []

    monkeypatch.setattr("src.docs.handlers.get_daily_documents", fake_get_daily_documents)
    monkeypatch.setattr("src.docs.handlers.process_items_pipeline", fake_process_items_pipeline)

    await get_documents_handler(mock_message)

    status_msg = mock_message.answer.return_value
    assert "ничего важного" in status_msg.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_get_documents_handler_without_username(mock_message, monkeypatch):
    # Тест случая без юзернейма (ссылка через -100...)
    mock_message.chat.username = None
    mock_message.chat.id = -1001234567890

    fake_docs = [SimpleNamespace(message_id=42, document_name="doc.pdf", about="Документ", created_at=None)]

    async def fake_get_daily_documents(chat_id: int):
        return fake_docs

    async def fake_process_items_pipeline(all_items, item_type, model_class):
        return all_items

    monkeypatch.setattr("src.docs.handlers.get_daily_documents", fake_get_daily_documents)
    monkeypatch.setattr("src.docs.handlers.process_items_pipeline", fake_process_items_pipeline)

    await get_documents_handler(mock_message)

    status_msg = mock_message.answer.return_value
    sent_text = status_msg.edit_text.call_args[0][0]

    assert "https://t.me/c/1234567890/42" in sent_text