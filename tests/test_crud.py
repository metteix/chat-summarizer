import pytest
from database.models import Mention, Hashtag, Document, Link, Task
from sqlalchemy.exc import IntegrityError

CRUD_TEST_CASES = [
    (Mention, {"chat_id": 1, "message_id": 10, "mention": "@user", "context": "Привет @user"},
               {"mention": "@new", "context": "Новый контекст"}),
    (Hashtag, {"chat_id": 2, "message_id": 20, "hashtag": "#test", "context": "Тест #test"},
               {"hashtag": "#new", "context": "Новый контекст"}),
    (Document, {"chat_id": 3, "message_id": 30, "file_id": "file_1", "document_name": "doc.pdf", "context": "Документ"},
               {"document_name": "new.pdf", "context": "Новый документ"}),
    (Link, {"chat_id": 4, "message_id": 40, "url": "https://example.com", "context": "Ссылка"},
          {"url": "https://new.com", "context": "Новая ссылка"}),
    (Task, {"chat_id": 5, "message_id": 50, "task_name": "Сделать тест", "context": "До пятницы"},
           {"task_name": "Новое задание", "context": "Новый контекст"}),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("model, create_data, update_data", CRUD_TEST_CASES)
async def test_crud_operations(db_session, model, create_data, update_data):
    # --- CREATE ---
    obj = model(**create_data)
    db_session.add(obj)
    await db_session.commit()

    # --- READ ---
    fetched = await db_session.get(model, obj.id)
    for key, value in create_data.items():
        assert getattr(fetched, key) == value

    # --- UPDATE ---
    for key, value in update_data.items():
        setattr(fetched, key, value)
    await db_session.commit()

    updated = await db_session.get(model, obj.id)
    for key, value in update_data.items():
        assert getattr(updated, key) == value

    # --- DELETE ---
    await db_session.delete(updated)
    await db_session.commit()

    deleted = await db_session.get(model, obj.id)
    assert deleted is None

@pytest.mark.asyncio
@pytest.mark.parametrize("model, create_data", [(m, c) for m, c, _ in CRUD_TEST_CASES])
async def test_crud_bulk_create(db_session, model, create_data):
    """
    Тест массового создания объектов. Для уникальности изменяем message_id.
    """
    objs = [model(**{**create_data, "message_id": create_data["message_id"] + i}) for i in range(5)]
    db_session.add_all(objs)
    await db_session.commit()

    for obj in objs:
        fetched = await db_session.get(model, obj.id)
        assert fetched is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("model, create_data", [(m, c) for m, c, _ in CRUD_TEST_CASES])
async def test_crud_edge_cases(db_session, model, create_data):
    """
    Дополнительные логические проверки:
    - Объект с пустым контекстом
    - Объект с очень длинным текстом
    """
    # Пустой контекст
    obj_empty = model(**{**create_data, "context": ""})
    db_session.add(obj_empty)

    # Длинный текст
    long_text = "x" * 1000
    obj_long = model(**{**create_data, "context": long_text})
    db_session.add(obj_long)

    await db_session.commit()

    fetched_empty = await db_session.get(model, obj_empty.id)
    fetched_long = await db_session.get(model, obj_long.id)
    assert fetched_empty.context == ""
    assert fetched_long.context == long_text
