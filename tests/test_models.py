import pytest
from database.models import (
    Mention,
    Hashtag,
    Document,
    Link,
    Task
)


def test_mention_model_fields():
    """
    Проверяем, что модель Mention корректно создаётся
    и поля chat_id, message_id, mention и context
    принимают правильные значения.
    """
    mention = Mention(
        chat_id=1,
        message_id=10,
        mention="@user",
        context="Привет @user"
    )

    assert mention.chat_id == 1
    assert mention.message_id == 10
    assert mention.mention == "@user"
    assert mention.context == "Привет @user"


def test_hashtag_model_fields():
    """
    Проверяем корректное создание модели Hashtag
    и правильность полей chat_id, message_id, hashtag, context.
    """
    hashtag = Hashtag(
        chat_id=2,
        message_id=20,
        hashtag="#exam",
        context="Будет #exam завтра"
    )

    assert hashtag.chat_id == 2
    assert hashtag.message_id == 20
    assert hashtag.hashtag == "#exam"
    assert hashtag.context == "Будет #exam завтра"


def test_document_model_fields():
    """
    Проверяем создание модели Document
    и правильность полей chat_id, message_id, file_id, document_name, context.
    """
    doc = Document(
        chat_id=3,
        message_id=30,
        file_id="file_123",
        document_name="lecture.pdf",
        context="Лекция"
    )

    assert doc.file_id == "file_123"
    assert doc.document_name == "lecture.pdf"
    assert doc.context == "Лекция"


def test_link_model_fields():
    """
    Проверяем модель Link: поля chat_id, message_id, url, context.
    Убеждаемся, что url корректный (начинается с https://).
    """
    link = Link(
        chat_id=4,
        message_id=40,
        url="https://example.com",
        context="Полезная ссылка"
    )

    assert link.url.startswith("https://")
    assert link.context == "Полезная ссылка"


def test_task_model_fields():
    """
    Проверяем модель Task: chat_id, message_id, task_name, context.
    """
    task = Task(
        chat_id=5,
        message_id=50,
        task_name="Сдать лабу",
        context="До пятницы"
    )

    assert task.task_name == "Сдать лабу"
    assert "пятницы" in task.context


# ---------- MENTION ----------

def test_mention_allows_unicode_and_emojis():
    mention = Mention(
        chat_id=1,
        message_id=1,
        mention="@пользователь🚀",
        context="Контекст с эмодзи 😎"
    )

    assert "🚀" in mention.mention
    assert "😎" in mention.context


def test_mention_empty_context_allowed():
    mention = Mention(
        chat_id=1,
        message_id=2,
        mention="@user",
        context=""
    )

    assert mention.context == ""


# ---------- HASHTAG ----------

def test_hashtag_with_special_characters():
    hashtag = Hashtag(
        chat_id=2,
        message_id=10,
        hashtag="#тест_2025🚀",
        context="Контекст"
    )

    assert hashtag.hashtag.startswith("#")
    assert "🚀" in hashtag.hashtag


def test_hashtag_long_context():
    long_context = "x" * 10_000
    hashtag = Hashtag(
        chat_id=2,
        message_id=11,
        hashtag="#long",
        context=long_context
    )

    assert len(hashtag.context) == 10_000


# ---------- DOCUMENT ----------

def test_document_with_long_filename():
    long_name = "a" * 255 + ".pdf"
    doc = Document(
        chat_id=3,
        message_id=20,
        file_id="file_long",
        document_name=long_name,
        context="Документ"
    )

    assert doc.document_name.endswith(".pdf")
    assert len(doc.document_name) > 200


def test_document_empty_context_allowed():
    doc = Document(
        chat_id=3,
        message_id=21,
        file_id="file_empty",
        document_name="empty.pdf",
        context=""
    )

    assert doc.context == ""


# ---------- LINK ----------

def test_link_http_and_https_allowed():
    link_http = Link(
        chat_id=4,
        message_id=30,
        url="http://example.com",
        context="http ссылка"
    )

    link_https = Link(
        chat_id=4,
        message_id=31,
        url="https://example.com",
        context="https ссылка"
    )

    assert link_http.url.startswith("http")
    assert link_https.url.startswith("https")


def test_link_with_query_and_fragment():
    link = Link(
        chat_id=4,
        message_id=32,
        url="https://example.com/page?x=1#section",
        context="Сложный URL"
    )

    assert "?" in link.url
    assert "#" in link.url


# ---------- TASK ----------

def test_task_name_with_unicode_and_symbols():
    task = Task(
        chat_id=5,
        message_id=40,
        task_name="Сдать лабу №2 🚀",
        context="Важно!"
    )

    assert "№" in task.task_name
    assert "🚀" in task.task_name


def test_task_long_context():
    long_context = "Очень важно. " * 1000
    task = Task(
        chat_id=5,
        message_id=41,
        task_name="Дедлайн",
        context=long_context
    )

    assert len(task.context) > 5000
