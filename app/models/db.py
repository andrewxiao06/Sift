"""SQLAlchemy engine, session, and the Paper table model."""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from app.config import DATABASE_URL, EMBEDDING_DIM

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class Paper(Base):
    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(primary_key=True)
    arxiv_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    title: Mapped[str] = mapped_column(String)
    abstract: Mapped[str] = mapped_column(String)
    authors: Mapped[list[str]] = mapped_column(ARRAY(String))
    categories: Mapped[list[str]] = mapped_column(ARRAY(String))
    published: Mapped[datetime] = mapped_column(DateTime)
    updated: Mapped[datetime] = mapped_column(DateTime)
    pdf_url: Mapped[str] = mapped_column(String)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM), nullable=True)


def init_db() -> None:
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()
