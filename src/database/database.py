import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from database.base import Base
import database.models.models


# Загружаем переменные из .env
load_dotenv()


def _env(name: str) -> str:
    """
        Получаем переменную окружения
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"В .env не задана переменная {name}")
    return value


# Собираем URL подключения к PostgreSQL
def build_url() -> URL:
    """
        Собираем URL подключения к PostgreSQL из переменных окружения
    """
    return URL.create(
        drivername="postgresql+psycopg",
        username=_env("PG_USER"),
        password=_env("PG_PASSWORD"),
        host=_env("PG_HOST"),
        port=int(_env("PG_PORT")),
        database=_env("PG_DBNAME"),
    )


engine = create_engine(build_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """
        Создаем таблицы, если их ещё нет
    """
    Base.metadata.create_all(engine)


# Удаляем все таблицы проекта
def drop_db() -> None:
    """
        Удаляем все таблицы проекта
    """
    Base.metadata.drop_all(engine)
