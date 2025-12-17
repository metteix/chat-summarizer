import pytest
from unittest.mock import AsyncMock
from src.docs.handlers import get_documents_handler
from types import SimpleNamespace

@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = AsyncMock()
    msg.chat.id = 12345
    msg.chat.username = "testchat"
    return msg

@pytest.mark.asyncio
async def test_get_documents_handler_with_docs(mock_message, monkeypatch):
    fake_docs = [
        SimpleNamespace(message_id=1, document_name="doc1.pdf", context="Первый документ"),
        SimpleNamespace(message_id=2, document_name="doc2.pdf", context="Второй документ")
    ]

    async def fake_get_daily_documents(chat_id: int):
        return fake_docs

    monkeypatch.setattr("src.docs.handlers.get_daily_documents", fake_get_daily_documents)

    await get_documents_handler(mock_message)

    assert mock_message.answer.call_count == 1
    sent_text = mock_message.answer.call_args[0][0]
    for doc in fake_docs:
        assert doc.document_name in sent_text
        assert doc.context in sent_text

@pytest.mark.asyncio
async def test_get_documents_handler_no_docs(mock_message, monkeypatch):
    async def empty_docs(chat_id: int):
        return []

    monkeypatch.setattr("src.docs.handlers.get_daily_documents", empty_docs)

    await get_documents_handler(mock_message)

    mock_message.answer.assert_called_once_with(
        "✅ Документов за последние 24 часа не найдено."
    )

@pytest.mark.asyncio
async def test_get_documents_handler_doc_without_context(mock_message, monkeypatch):
    fake_docs = [
        SimpleNamespace(message_id=1, document_name="doc1.pdf", context=None),
        SimpleNamespace(message_id=2, document_name="doc2.pdf", context="Второй документ")
    ]

    async def fake_get_daily_documents(chat_id: int):
        return fake_docs

    monkeypatch.setattr("src.docs.handlers.get_daily_documents", fake_get_daily_documents)

    await get_documents_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    assert "doc1.pdf" in sent_text
    assert "doc2.pdf" in sent_text
    # Документ без контекста не должен ломать вывод
    assert "Второй документ" in sent_text

@pytest.mark.asyncio
async def test_get_documents_handler_many_docs(mock_message, monkeypatch):
    fake_docs = [SimpleNamespace(message_id=i, document_name=f"doc{i}.pdf", context=f"Документ {i}") for i in range(1, 51)]

    async def fake_get_daily_documents(chat_id: int):
        return fake_docs

    monkeypatch.setattr("src.docs.handlers.get_daily_documents", fake_get_daily_documents)

    await get_documents_handler(mock_message)

    sent_text = mock_message.answer.call_args[0][0]
    # Проверяем, что первые и последние документы упомянуты
    assert "doc1.pdf" in sent_text
    assert "doc50.pdf" in sent_text
    assert "Документ 1" in sent_text
    assert "Документ 50" in sent_text

# @pytest.mark.asyncio
# async def test_get_documents_handler_long_text(mock_message, monkeypatch):
#     # Создадим 200 документов с длинным контекстом, чтобы текст точно был большим
#     fake_docs = [
#         SimpleNamespace(
#             message_id=i,
#             document_name=f"doc{i}.pdf",
#             context="Описание " + "x" * 50  # длинный текст
#         )
#         for i in range(1, 201)
#     ]
#
#     async def fake_get_daily_documents(chat_id: int):
#         return fake_docs
#
#     monkeypatch.setattr("src.docs.handlers.get_daily_documents", fake_get_daily_documents)
#
#     await get_documents_handler(mock_message)
#
#     # Проверяем, что answer вызывался несколько раз (текст был разбит)
#     assert mock_message.answer.call_count > 1
#
#     # Проверяем, что первые и последние документы попали хотя бы в одно из сообщений
#     all_texts = [call[0][0] for call in mock_message.answer.call_args_list]
#     combined_text = "\n".join(all_texts)
#
#     assert "doc1.pdf" in combined_text
#     assert "doc200.pdf" in combined_text
#     assert "Описание " in combined_text
