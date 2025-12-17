from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, Boolean
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.sql import func

class Base(AsyncAttrs, DeclarativeBase):
    pass


class ChatSettings(Base):
    __tablename__ = 'chat_settings'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, unique=True, nullable=False)

    is_auto_summary = Column(Boolean, default=False)
    summary_time = Column(String(5), default="09:00")

    include_tasks = Column(Boolean, default=True)
    include_links = Column(Boolean, default=True)
    include_docs = Column(Boolean, default=True)
    include_mentions = Column(Boolean, default=True)
    include_hashtags = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())

class Mention(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    mention = Column(String(50), nullable=False)
    context = Column(Text, nullable=True)     
    created_at = Column(DateTime, default=func.now()) 

class Hashtag(Base):
    __tablename__ = 'hashtags'
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    hashtag = Column(String(50), nullable=False)
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    file_id = Column(String(255), nullable=False)
    document_name = Column(String(255), nullable=False)
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

class Link(Base):
    __tablename__ = 'links'
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    url = Column(String(500), nullable=False)
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    task_name = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

