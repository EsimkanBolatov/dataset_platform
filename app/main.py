# app/main.py

from fastapi import FastAPI
from . import models
from .database import engine
from .routers import auth as auth_router
from .routers import templates as templates_router
from .routers import datasets as datasets_router
from .routers import ai as ai_router
from .routers import veritas as veritas_router

# Эта команда создает все таблицы в БД при старте, если их нет
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Dataset Management Platform API",
    description="API для управления, генерации и анализа датасетов с сервисом 'Veritas'.",
    version="1.1"
)

# Подключаем роутер для аутентификации
app.include_router(auth_router.router, prefix="/api/auth")

# Подключаем роутер для шаблонов
app.include_router(templates_router.router, prefix="/api/templates")

# Подключаем роутер для датасетов
app.include_router(datasets_router.router, prefix="/api/datasets")

# Подключаем роутер для ИИ-операций
app.include_router(ai_router.router, prefix="/api")

# Подключаем роутер для сервиса "Veritas"
app.include_router(veritas_router.router, prefix="/api")

@app.get("/", tags=["Root"])
def read_root():
    return {"status": "ok", "message": "Welcome to the Dataset Platform API!"}