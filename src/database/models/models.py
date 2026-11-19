from __future__ import annotations
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Computed,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


# зададим размерность эмбеддингов 
# в нашем случае модель all-MiniLM-L6-v2
EMBEDDING_DIM = 384


class Document(Base):
    """
        Исходная статья целиком
    """

    __tablename__ = "documents"

    # основные поля документа
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), unique=True)
    text: Mapped[str] = mapped_column(Text)

    # свяжем документ с вопросами и чанками
    questions: Mapped[list[Question]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )
    chunks: Mapped[list[Chunk]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )


class Question(Base):
    """
        Вопрос + позиция правильного ответа в исходном документе
    """

    __tablename__ = "questions"

    # основные поля вопроса
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    question: Mapped[str] = mapped_column(Text)
    answer_text: Mapped[str] = mapped_column(Text)
    answer_start: Mapped[int] = mapped_column(Integer)
    answer_end: Mapped[int] = mapped_column(Integer)

    # тут тоже связываем вопрос с исходным документом
    document: Mapped[Document] = relationship(back_populates="questions")


class Chunk(Base):
    """
        Фрагмент документа, полученный определённой стратегией нарезки
    """

    __tablename__ = "chunks"

    # зазадим ограничения и индексы для ускорения поиска
    __table_args__ = (
        # запрещаем повторение позиции чанка в рамках документа и стратегии
        UniqueConstraint("document_id", "strategy", "chunk_index", name="uq_chunk_position"),
        # создаем индексы
        Index("ix_chunks_strategy_document", "strategy", "document_id"),
        Index("ix_chunks_tsv", "tsv", postgresql_using="gin"),
    )

    # основные поля чанка
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    strategy: Mapped[str] = mapped_column(String(64))
    chunk_index: Mapped[int] = mapped_column(Integer)
    start_char: Mapped[int] = mapped_column(Integer)
    end_char: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)

    # добавляем поле для хранения эмбеддинга
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIM), nullable=True
    )

    tsv = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', content)", persisted=True),
    )

    # и тут тоже связываем чанки с исходным документом
    document: Mapped[Document] = relationship(back_populates="chunks")
