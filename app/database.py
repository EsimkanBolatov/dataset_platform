# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base # Обновленный импорт
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- ВОТ ЭТА ФУНКЦИЯ ---
# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()