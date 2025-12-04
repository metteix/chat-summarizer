from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Boolean, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.sql import func

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Chat(Base):
    __tablename__ = 'chats'

    id = Column(BigInteger, primary_key=True)
    title = Column(String(255), nullable=True)
    
    # Настройки (из ТЗ)
    is_auto_summary = Column(Boolean, default=True)
    summary_time = Column(String(5), default="09:00")
    timezone = Column(String(50), default="UTC")
    
    # Что включать в сводку
    include_tasks = Column(Boolean, default=True)
    include_links = Column(Boolean, default=True)
    include_docs = Column(Boolean, default=True)
    include_mentions = Column(Boolean, default=True)

    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<Chat(id={self.id}, title='{self.title}')>"

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'), nullable=False) # Связь с чатом
    telegram_message_id = Column(BigInteger, nullable=False) # ID сообщения в телеграме
    user_id = Column(BigInteger, nullable=False) # Кто написал
    username = Column(String(255), nullable=True)
    text = Column(Text, nullable=True) # Текст сообщения
    
    created_at = Column(DateTime, default=func.now())

class Mention(Base):
    __tablename__ = 'mentions'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'), nullable=False)
    message_id = Column(BigInteger, nullable=False) # Ссылка на сообщение
    
    mentioned_username = Column(String(255), nullable=False) # Кого тегнули
    
    created_at = Column(DateTime, default=func.now())

class Hashtag(Base):
    __tablename__ = 'hashtags'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'), nullable=False)
    message_id = Column(BigInteger, nullable=False)
    
    hashtag = Column(String(255), nullable=False)
    
    created_at = Column(DateTime, default=func.now())

class Task(Base):
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'), nullable=False)
    message_id = Column(BigInteger, nullable=False)
    
    description = Column(Text, nullable=False) # Что сделать
    assignee = Column(String(255), nullable=True) # Ответственный (если ML нашел)
    deadline = Column(DateTime, nullable=True) # Срок (если ML нашел)
    is_completed = Column(Boolean, default=False) # Выполнено или нет
    
    created_at = Column(DateTime, default=func.now())

class Link(Base):
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'), nullable=False)
    message_id = Column(BigInteger, nullable=False)
    
    url = Column(Text, nullable=False)
    description = Column(String(255), nullable=True) # Заголовок страницы (если парсили)
    
    created_at = Column(DateTime, default=func.now())

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'), nullable=False)
    message_id = Column(BigInteger, nullable=False)
    
    file_name = Column(String(255), nullable=False)
    file_id = Column(String(255), nullable=False) # ID файла в Телеграм
    file_type = Column(String(50), nullable=True) # pdf, docx, img
    
    created_at = Column(DateTime, default=func.now())