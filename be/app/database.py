from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings


SQLALCHEMY_DATABASE_URL = settings.SQLSERVER_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"fast_executemany": True},
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import package which registers all models via app/models/__init__.py
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
