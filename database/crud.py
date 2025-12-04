from sqlalchemy import select
from database.session import async_session
from database.models import Tag, Hashtag, Link, Document

async def save_object(obj):
    """
    Универсальная функция для сохранения любого объекта (тега, ссылки и т.д.)
    """
    async with async_session() as session:
        session.add(obj)
        await session.commit()
        await session.refresh(obj)
        return obj

async def add_tag(message_id: int, tag_text: str):
    tag = Tag(message_id=message_id, tag=tag_text)
    await save_object(tag)

async def get_tags_by_message(message_id: int):
    """Получить все теги конкретного сообщения"""
    async with async_session() as session:
        query = select(Tag).where(Tag.message_id == message_id)
        result = await session.execute(query)
        return result.scalars().all()

async def add_hashtag(message_id: int, hashtag_text: str):
    hashtag = Hashtag(message_id=message_id, hashtag=hashtag_text)
    await save_object(hashtag)

async def get_hashtags_by_message(message_id: int):
    async with async_session() as session:
        query = select(Hashtag).where(Hashtag.message_id == message_id)
        result = await session.execute(query)
        return result.scalars().all()

async def add_link(message_id: int, url: str):
    link = Link(message_id=message_id, url=url)
    await save_object(link)

async def get_links_by_message(message_id: int):
    async with async_session() as session:
        query = select(Link).where(Link.message_id == message_id)
        result = await session.execute(query)
        return result.scalars().all()

async def add_document(message_id: int, name: str, path: str = None):
    doc = Document(message_id=message_id, document_name=name, file_path=path)
    await save_object(doc)

async def get_documents_by_message(message_id: int):
    async with async_session() as session:
        query = select(Document).where(Document.message_id == message_id)
        result = await session.execute(query)
        return result.scalars().all()

async def get_full_message_data(message_id: int):
    """
    Возвращает словарь со всеми данными по сообщению.
    Пригодится для суммаризации.
    """
    tags = await get_tags_by_message(message_id)
    hashtags = await get_hashtags_by_message(message_id)
    links = await get_links_by_message(message_id)
    docs = await get_documents_by_message(message_id)
    
    return {
        "tags": [t.tag for t in tags],
        "hashtags": [h.hashtag for h in hashtags],
        "links": [l.url for l in links],
        "documents": [d.document_name for d in docs]
    }