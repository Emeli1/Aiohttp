import os
import datetime
from typing import List

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, mapped_column, MappedColumn, relationship
from sqlalchemy import Integer, String, DateTime, func, ForeignKey

POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "12345")
POSTGRES_USER = os.getenv("POSTGRES_USER", "advs")
POSTGRES_DB = os.getenv("POSTGRES_DB", "advs")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5431")

POSTGRES_DSN = (f"postgresql+asyncpg://"
          f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
          f"{POSTGRES_HOST}:{POSTGRES_PORT}/"
          f"{POSTGRES_DB}"
          )

engine = create_async_engine(POSTGRES_DSN)
AsyncSession = async_sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase, AsyncAttrs):

    @property
    def id_dict(self):           # во всех моделях нужно получение id в виде json
        return {"id": self.id}


class User(Base):
    __tablename__ = "users"

    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    name: MappedColumn[str] = mapped_column(String, unique=True)
    password: MappedColumn[str] = mapped_column(String)
    advs: MappedColumn[List["Advertisement"]] = relationship(back_populates="owner")


    @property
    def dict(self):
        return {
            "id": self.id,
            "name": self.name
        }


class Advertisement(Base):
    __tablename__ = "advs"

    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    name: MappedColumn[str] = mapped_column(String)
    description: MappedColumn[str] = mapped_column(String)
    date: MappedColumn[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    owner_id: MappedColumn[int] = mapped_column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"))

    owner: MappedColumn["User"] = relationship(back_populates="advs")  # связка с полем advs в User


    @property
    def json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "date": self.date.isoformat(),
            "owner_id": self.owner_id
        }


async def init_orm():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_orm():
    await engine.dispose()