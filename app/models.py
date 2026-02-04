# app/models.py

import uuid
from sqlalchemy import Column, String, DateTime, func, Enum as SAEnum, JSON, ForeignKey, Integer
# ИЗМЕНЕНИЕ: Импортируем UUID из основного пакета, а не из диалекта postgresql
from sqlalchemy import UUID
from sqlalchemy.orm import relationship

from app.database import Base
import enum

class UserRole(enum.Enum):
    admin = "admin"
    user = "user"
    viewer = "viewer"

class User(Base):
    __tablename__ = "users"

    # ИЗМЕНЕНИЕ: Используем стандартный UUID. as_uuid=True работает и здесь.
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String)
    role = Column(SAEnum(UserRole), default=UserRole.user, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Template(Base):
    __tablename__ = "templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    schema_ = Column("schema", JSON, nullable=False)
    ui_hints = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner = relationship("User")


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True, nullable=False)
    meta = Column(JSON)
    row_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("templates.id"), nullable=False)

    owner = relationship("User")
    template = relationship("Template")
    rows = relationship("DatasetRow", back_populates="dataset", cascade="all, delete-orphan")


class DatasetRow(Base):
    __tablename__ = "dataset_rows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    row_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"), nullable=False)
    dataset = relationship("Dataset", back_populates="rows")