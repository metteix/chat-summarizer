import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from types import SimpleNamespace

# Мокаем database.crud до импорта handlers
sys.modules["database.crud"] = MagicMock(
    get_chat_settings=AsyncMock(),
    update_chat_settings=AsyncMock()
)

from src.settings.handlers import cmd_settings, settings_callback_router, process_time_input, SettingsStates


@pytest.fixture
def mock_message():
    msg = AsyncMock()
    msg.chat = SimpleNamespace(id=12345, title="TestChat")
    msg.from_user = SimpleNamespace(id=1)
    msg.answer = AsyncMock()
    msg.reply = AsyncMock()
    return msg


@pytest.fixture
def mock_callback():
    cb = AsyncMock()
    cb.message = SimpleNamespace(chat=SimpleNamespace(id=12345, title="TestChat"))
    cb.from_user = SimpleNamespace(id=1)
    cb.data = ""
    cb.answer = AsyncMock()
    cb.message.edit_text = AsyncMock()
    cb.message.edit_reply_markup = AsyncMock()
    return cb


@pytest.mark.asyncio
async def test_cmd_settings(mock_message):
    with patch("src.settings.handlers.is_user_admin", new_callable=AsyncMock) as mock_admin, \
         patch("src.settings.handlers.get_status_text", new_callable=AsyncMock) as mock_status, \
         patch("src.settings.handlers.get_summary_fields_kb", return_value=None):

        mock_admin.return_value = True
        mock_status.return_value = "STATUS_TEXT"

        await cmd_settings(mock_message, bot=None)

        # Проверяем текст и parse_mode, не зависим от клавиатуры
        mock_message.answer.assert_called_once()
        sent_text = mock_message.answer.call_args[0][0]
        sent_parse_mode = mock_message.answer.call_args[1]["parse_mode"]
        assert sent_text == "STATUS_TEXT"
        assert sent_parse_mode == "Markdown"


@pytest.mark.asyncio
async def test_settings_callback_toggle_field(mock_callback):
    with patch("src.settings.handlers.is_user_admin", new_callable=AsyncMock) as mock_admin, \
         patch("src.settings.handlers.get_chat_settings") as mock_get, \
         patch("src.settings.handlers.update_chat_settings") as mock_update, \
         patch("src.settings.handlers.get_summary_fields_kb") as mock_kb:

        mock_admin.return_value = True
        mock_get.return_value = SimpleNamespace(
            include_tasks=True,
            include_links=False,
            include_docs=True,
            include_mentions=True,
            include_hashtags=False
        )
        mock_kb.return_value = "KEYBOARD"

        mock_callback.data = "toggle_field_files"

        await settings_callback_router(mock_callback, state=AsyncMock(), bot=None)

        mock_update.assert_called_once()
        mock_callback.answer.assert_called_once()


# потом включим когда доделаем settings


# @pytest.mark.asyncio
# async def test_process_time_input_valid(mock_message):
#     mock_message.text = "12:30"
#
#     # Создаём state с нужным методом
#     state = AsyncMock()
#     state.update_data = AsyncMock()
#
#     await process_time_input(mock_message, state)
#
#     # Проверяем, что state.update_data был вызван с любыми аргументами
#     state.update_data.assert_called_once()
#     state.clear.assert_called_once()
#     mock_message.answer.assert_called_once()
#

@pytest.mark.asyncio
async def test_process_time_input_invalid(mock_message):
    mock_message.text = "invalid"

    state = AsyncMock()
    await process_time_input(mock_message, state)

    mock_message.reply.assert_called_once_with("Формат: 09:00")
    state.clear.assert_not_called()  # state не должен очищаться при ошибке
