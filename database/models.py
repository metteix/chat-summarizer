# database/models.py
from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.sql import func

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    tag = Column(String(20), nullable=False)
    message_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=func.now()) 

    def __repr__(self):
        return f"<Tag(tag='{self.tag}', message_id={self.message_id})>"

class Hashtag(Base):
    __tablename__ = 'hashtags'

    id = Column(Integer, primary_key=True)
    hashtag = Column(String(50), nullable=False)
    message_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Hashtag(hashtag='{self.hashtag}', message_id={self.message_id})>"

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    document_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=True) 
    message_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Document(name='{self.document_name}', path='{self.file_path}')>"

class Link(Base):
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False)
    message_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Link(url='{self.url}', message_id={self.message_id})>"