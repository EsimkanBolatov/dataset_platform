# app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
import uuid
from typing import List

# --- Функции для работы с Шаблонами (Templates) ---

def get_template(db: Session, template_id: uuid.UUID):
    """Получить один шаблон по его ID."""
    return db.query(models.Template).filter(models.Template.id == template_id).first()

def get_templates(db: Session, skip: int = 0, limit: int = 100):
    """Получить список шаблонов с пагинацией."""
    return db.query(models.Template).offset(skip).limit(limit).all()

def create_template(db: Session, template: schemas.TemplateCreate, user_id: uuid.UUID):
    """Создать новый шаблон в БД."""
    db_template = models.Template(
        name=template.name,
        description=template.description,
        schema_=template.schema_,
        ui_hints=template.ui_hints,
        owner_id=user_id
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

# --- Функции для работы с Пользователями (Users) ---

def get_user_by_email(db: Session, email: str):
    """Получить пользователя по его email."""
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    """Создать нового пользователя."""
    from . import auth
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        name=user.name,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Функции для работы с Датасетами (Datasets) ---

def create_dataset(db: Session, dataset: schemas.DatasetCreate, user_id: uuid.UUID):
    """Создать новый датасет."""
    db_dataset = models.Dataset(**dataset.model_dump(), owner_id=user_id)
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    return db_dataset

def get_datasets(db: Session, owner_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Получить список датасетов для пользователя."""
    return db.query(models.Dataset).filter(models.Dataset.owner_id == owner_id).offset(skip).limit(limit).all()

def get_dataset(db: Session, dataset_id: uuid.UUID):
    """Получить датасет по ID."""
    return db.query(models.Dataset).filter(models.Dataset.id == dataset_id).first()

def create_dataset_row(db: Session, row: schemas.DatasetRowCreate, dataset_id: uuid.UUID):
    """Добавить строку в датасет."""
    db_row = models.DatasetRow(row_data=row.row_data, dataset_id=dataset_id)
    db.add(db_row)
    db.commit()
    db.refresh(db_row)
    return db_row

def get_dataset_rows(db: Session, dataset_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Получить строки датасета."""
    return db.query(models.DatasetRow).filter(models.DatasetRow.dataset_id == dataset_id).offset(skip).limit(limit).all()

def get_rows_by_ids(db: Session, row_ids: List[uuid.UUID]) -> List[models.DatasetRow]:
    """Получить несколько строк датасета по списку их ID."""
    return db.query(models.DatasetRow).filter(models.DatasetRow.id.in_(row_ids)).all()