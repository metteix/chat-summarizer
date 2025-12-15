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
    mention = Column(String(20), nullable=False)
    context = Column(Text, nullable=True)     
    created_at = Column(DateTime, default=func.now()) 

    def __repr__(self):
        return f"<Mention(mention={self.mention}, message_id={self.message_id})>"

class Hashtag(Base):
    __tablename__ = 'hashtags'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    hashtag = Column(String(50), nullable=False)
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Hashtag(hashtag={self.hashtag}message_id={self.message_id})>"

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    file_id = Column(BigInteger, nullable=False)
    document_name = Column(String(255), nullable=False)
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Document(name='{self.document_name}', message_id='{self.message_id}')>"

class Link(Base):
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    url = Column(String(255), nullable=False)
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Link(url='{self.url}', description={self.description}, message_id={self.message_id})>"

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    message_id = Column(BigInteger, nullable=False)
    task_name = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<Task(message_id={self.message_id})"
