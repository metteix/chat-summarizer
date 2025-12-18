import sys
import re
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

# -----------------------------
# mock database.crud BEFORE import
# -----------------------------
sys.modules["database.crud"] = MagicMock(
    get_chat_settings=AsyncMock(),
    update_settings_field=AsyncMock(),
    activate_chat=AsyncMock(),
)

# -----------------------------
# import after mocks
# -----------------------------
from src.settings.handlers import (
    cmd_settings,
    settings_callback_router,
    process_time_input,
)
from src.settings.states import SettingsStates


# -----------------------------
# fixtures
# -----------------------------
@pytest.fixture
def message():
    msg = AsyncMock()
    msg.chat = SimpleNamespace(id=123, title="TestChat")
    msg.from_user = SimpleNamespace(id=1)
    msg.text = ""
    msg.answer = AsyncMock()
    msg.reply = AsyncMock()
    return msg


@pytest.fixture
def callback():
    cb = AsyncMock()
    cb.data = ""
    cb.from_user = SimpleNamespace(id=1)
    cb.message = SimpleNamespace(
        chat=SimpleNamespace(id=123, title="TestChat"),
        edit_text=AsyncMock(),
        edit_reply_markup=AsyncMock(),
        delete=AsyncMock(),
    )
    cb.answer = AsyncMock()
    return cb


@pytest.fixture
def state():
    st = AsyncMock()
    st.set_state = AsyncMock()
    st.clear = AsyncMock()
    return st


# -----------------------------
# /settings command
# -----------------------------
@pytest.mark.asyncio
async def test_cmd_settings_admin_ok(message):
    with patch("src.settings.handlers.is_user_admin", new_callable=AsyncMock) as admin, \
         patch("src.settings.handlers.get_chat_settings", new_callable=AsyncMock) as get_chat, \
         patch("src.settings.handlers.activate_chat", new_callable=AsyncMock) as activate_chat, \
         patch("src.settings.handlers.format_status_text", return_value="STATUS"), \
         patch("src.settings.handlers.get_main_settings_kb", return_value="KB"):

        admin.return_value = True
        get_chat.return_value = SimpleNamespace(is_auto_summary=False)

        await cmd_settings(message, bot=None)

        message.answer.assert_called_once_with("STATUS", reply_markup="KB")


@pytest.mark.asyncio
async def test_cmd_settings_not_admin(message):
    with patch("src.settings.handlers.is_user_admin", new_callable=AsyncMock) as admin:
        admin.return_value = False

        await cmd_settings(message, bot=None)

        message.reply.assert_called_once()
        message.answer.assert_not_called()


# -----------------------------
# callback router
# -----------------------------
@pytest.mark.asyncio
async def test_delete_message_callback(callback, state):
    callback.data = "delete_message"

    await settings_callback_router(callback, state, bot=None)

    callback.message.delete.assert_called_once()


@pytest.mark.asyncio
async def test_toggle_field_callback(callback, state):
    callback.data = "toggle_field_files"

    chat = SimpleNamespace(
        include_docs=True,
        include_tasks=True,
        include_links=False,
        include_mentions=True,
        include_hashtags=False,
        is_auto_summary=False,
    )

    with patch("src.settings.handlers.is_user_admin", new_callable=AsyncMock) as admin, \
         patch("src.settings.handlers.get_chat_settings", new_callable=AsyncMock) as get_chat, \
         patch("src.settings.handlers.update_settings_field", new_callable=AsyncMock) as update, \
         patch("src.settings.handlers.get_summary_fields_kb", return_value="KB"):

        admin.return_value = True
        get_chat.side_effect = [chat, chat]

        await settings_callback_router(callback, state, bot=None)

        update.assert_called_once()
        callback.message.edit_reply_markup.assert_called_once_with(reply_markup="KB")
        callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_settings_home(callback, state):
    callback.data = "settings_home"

    chat = SimpleNamespace(is_auto_summary=False)

    with patch("src.settings.handlers.is_user_admin", new_callable=AsyncMock) as admin, \
         patch("src.settings.handlers.get_chat_settings", return_value=chat), \
         patch("src.settings.handlers.format_status_text", return_value="STATUS"), \
         patch("src.settings.handlers.get_main_settings_kb", return_value="KB"):

        admin.return_value = True

        await settings_callback_router(callback, state, bot=None)

        state.clear.assert_called_once()
        callback.message.edit_text.assert_called_once()
        callback.answer.assert_called_once()


# -----------------------------
# time input FSM
# -----------------------------
@pytest.mark.asyncio
async def test_process_time_input_valid(message, state):
    message.text = "18:30"

    with patch("src.settings.handlers.update_settings_field", new_callable=AsyncMock), \
         patch("src.settings.handlers.get_chat_settings", new_callable=AsyncMock) as get_chat, \
         patch("src.settings.handlers.format_status_text", return_value="STATUS"), \
         patch("src.settings.handlers.get_main_settings_kb", return_value="KB"):

        get_chat.return_value = SimpleNamespace(is_auto_summary=True)

        await process_time_input(message, state)

        state.clear.assert_called_once()
        message.answer.assert_called()


@pytest.mark.asyncio
async def test_process_time_input_invalid(message, state):
    message.text = "invalid"

    await process_time_input(message, state)

    message.answer.assert_called_once()
    state.clear.assert_not_called()
