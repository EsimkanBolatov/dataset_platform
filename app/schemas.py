# schemas.py

import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any




# --- Схемы для Шаблонов (Templates) ---

class TemplateBase(BaseModel):
    name: str
    description: str | None = None

    schema_: Dict[str, Any] = Field(..., alias="schema")

    ui_hints: Dict[str, Any] | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "Клиентская база",
                "description": "Шаблон для ведения списка клиентов",
                "schema": {
                    "fields": [
                        {"field_name": "full_name", "display_name": "ФИО", "type": "string"},
                        {"field_name": "email", "display_name": "Email", "type": "email"}
                    ]
                }
            }
        }
    )


class TemplateCreate(TemplateBase):
    pass # Наследует все поля от TemplateBase


class Template(TemplateBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        # Эта настройка позволяет Pydantic читать данные
        # напрямую из ORM-объектов SQLAlchemy
        from_attributes = True

# --- Схемы для Пользователей (Users) ---

class UserBase(BaseModel):
    email: str
    name: str | None = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: uuid.UUID
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Схемы для Токенов (Tokens) ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

# --- Схемы для Строк Датасета (DatasetRows) ---

class DatasetRowBase(BaseModel):
    row_data: Dict[str, Any]

class DatasetRowCreate(DatasetRowBase):
    pass

class DatasetRow(DatasetRowBase):
    id: uuid.UUID
    dataset_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- Схемы для Датасетов (Datasets) ---

class DatasetBase(BaseModel):
    name: str
    meta: Dict[str, Any] | None = None # <-- ADD THIS LINE

class DatasetCreate(DatasetBase):
    template_id: uuid.UUID

class Dataset(DatasetBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    template_id: uuid.UUID
    created_at: datetime
    template: Template

    class Config:
        from_attributes = True

# --- Схемы для сервиса Veritas ---

class VeritasEvidence(BaseModel):
    feature: str
    description: str
    impact: str # e.g., "high", "medium", "low"

class VeritasResponse(BaseModel):
    request_id: uuid.UUID
    authenticity_score: int = Field(..., ge=0, le=100)
    evidence: List[VeritasEvidence]