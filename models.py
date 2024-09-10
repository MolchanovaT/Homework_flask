import datetime
import os
from atexit import register

from sqlalchemy import DateTime, Integer, String, create_engine, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, relationship, WriteOnlyMapped

POSTGRES_USER = os.getenv("POSTGRES_USER", "")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
POSTGRES_DB = os.getenv("POSTGRES_DB", "")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5431")

PG_DSN = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(PG_DSN)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
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


Base.metadata.create_all(bind=engine)

register(engine.dispose)
