from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.sql import func

class Base(AsyncAttrs, DeclarativeBase):
    pass

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