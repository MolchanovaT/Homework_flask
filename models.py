import datetime
import os

from sqlalchemy import DateTime, Integer, String, func, ForeignKey
from sqlalchemy.ext.asyncio import (AsyncAttrs, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, WriteOnlyMapped, relationship

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5431")
POSTGRES_DB = os.getenv("POSTGRES_DB", "")
POSTGRES_USER = os.getenv("POSTGRES_USER", "")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

PG_DSN = (
    f"postgresql+asyncpg://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_async_engine(PG_DSN)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase, AsyncAttrs):
    pass


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    created_on: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)

    @property
    def json(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "created_on": self.created_on.isoformat(),
            "user_id": self.user_id,
        }


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(72), nullable=False)
    announcements: WriteOnlyMapped['Announcement'] = relationship('Announcement', backref='owner')

    @property
    def json(self):
        return {
            "id": self.id,
            "name": self.name,
        }


async def init_orm():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
