# app/routers/templates.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from .. import schemas, crud, auth, models, database

# Создаем роутер и сразу указываем, что все эндпоинты в нем
# будут зависеть от get_current_user. Это и есть решение проблемы!
router = APIRouter(
    dependencies=[Depends(auth.get_current_user)]
)

@router.post("", response_model=schemas.Template, status_code=201, tags=["Templates"])
def create_new_template(template: schemas.TemplateCreate, db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    return crud.create_template(db=db, template=template, user_id=current_user.id)

@router.get("", response_model=List[schemas.Template], tags=["Templates"])
def read_templates(db: Session = Depends(database.get_db), skip: int = 0, limit: int = 100):
    # current_user здесь уже не нужен, так как он проверяется на уровне роутера
    templates = crud.get_templates(db, skip=skip, limit=limit)
    return templates

@router.get("/{template_id}", response_model=schemas.Template, tags=["Templates"])
def read_template(template_id: uuid.UUID, db: Session = Depends(database.get_db)):
    db_template = crud.get_template(db, template_id=template_id)
    if db_template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return db_template