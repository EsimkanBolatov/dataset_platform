# app/routers/ai.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import uuid
from typing import List, Dict, Any
from .. import schemas, crud, auth, models, database
from ..ai import services as ai_services

router = APIRouter(
    prefix="/ai",
    tags=["AI"],
    dependencies=[Depends(auth.get_current_user)]
)

# Модель для тела запроса (у вас она уже есть и написана отлично)
class AIGenerationRequest(BaseModel):
    count: int = Field(..., gt=0, le=50, description="Number of rows to generate")
    instruction: str = Field(..., min_length=10, max_length=500, description="Text prompt with generation rules")

# Эта модель точно описывает структуру, которую вы хотите вернуть
class AIGenerationResponse(BaseModel):
    count: int
    rows: List[Dict[str, Any]]

class AICleaningRequest(BaseModel):
    row_ids: List[uuid.UUID] = Field(..., description="List of row IDs to clean")
    instruction: str = Field(..., max_length=500, description="Text prompt with cleaning rules")

class AICleaningResponse(BaseModel):
    count: int
    # Возвращаем diff: старые и новые данные для сравнения
    diff: List[Dict[str, Any]]

# Эта модель описывает структуру, которую вы хотите вернуть для третьего промта
class AICleaningResponse(BaseModel):
    count: int
class AISchemaSuggestionResponse(BaseModel):
    suggestion: str

@router.post("/datasets/{dataset_id}/generate", response_model=AIGenerationResponse) # <--- ИЗМЕНЕНО
def generate_data_for_dataset(dataset_id: uuid.UUID, request: AIGenerationRequest, db: Session = Depends(database.get_db)):
    """
    Generate new rows for a dataset using AI and save them to the database.
    """
    # 1. Получаем датасет и связанный с ним шаблон
    db_dataset = crud.get_dataset(db, dataset_id=dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 2. Получаем схему из связанного шаблона
    template_schema = db_dataset.template.schema_

    # 3. Вызываем AI сервис для генерации данных
    generated_rows = ai_services.generate_rows_for_schema(
        schema=template_schema,
        instruction=request.instruction,
        count=request.count
    )

    if not generated_rows:
        raise HTTPException(status_code=500, detail="AI failed to generate data or returned an invalid format.")

    # 4. Проходим по каждой сгенерированной строке и сохраняем её
    for row_data in generated_rows:
        row_to_create = schemas.DatasetRowCreate(row_data=row_data)
        crud.create_dataset_row(db=db, row=row_to_create, dataset_id=dataset_id)

    # 5. Возвращаем структурированный ответ (теперь он соответствует response_model)
    return {"count": len(generated_rows), "rows": generated_rows}

@router.post("/datasets/{dataset_id}/clean", response_model=AICleaningResponse)
def clean_data_in_dataset(
    dataset_id: uuid.UUID,
    request: AICleaningRequest,
    db: Session = Depends(database.get_db)
):
    """
    Clean specific rows in a dataset using AI.
    """
    # 1. Получаем датасет и его схему
    db_dataset = crud.get_dataset(db, dataset_id=dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    template_schema = db_dataset.template.schema_

    # 2. Получаем строки, которые нужно очистить
    rows_to_clean = crud.get_rows_by_ids(db, row_ids=request.row_ids)
    if len(rows_to_clean) != len(request.row_ids):
        raise HTTPException(status_code=404, detail="One or more rows not found")

    # 3. Готовим "грязные" данные для отправки в ИИ-сервис
    dirty_data = [row.row_data for row in rows_to_clean]

    # 4. Вызываем сервис очистки
    cleaned_data = ai_services.clean_rows_with_ai(
        schema=template_schema,
        dirty_rows=dirty_data,
        instruction=request.instruction
    )

    if not cleaned_data or len(cleaned_data) != len(dirty_data):
        raise HTTPException(status_code=500, detail="AI failed to clean data or returned an invalid format.")

    # 5. Формируем "diff" для ответа, чтобы UI мог показать разницу
    diff = []
    for i, original_row in enumerate(rows_to_clean):
        diff.append({
            "row_id": original_row.id,
            "original": original_row.row_data,
            "cleaned": cleaned_data[i]
        })

    return {"count": len(diff), "diff": diff}

@router.post("/datasets/{dataset_id}/schema-suggestion", response_model=AISchemaSuggestionResponse)
def get_schema_suggestion(
    dataset_id: uuid.UUID,
    db: Session = Depends(database.get_db)
):
    """
    Analyzes a sample of dataset data and suggests schema improvements.
    """
    # 1. Получаем датасет и его текущую схему
    db_dataset = crud.get_dataset(db, dataset_id=dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    current_schema = db_dataset.template.schema_

    # 2. Получаем выборку данных для анализа (например, первые 20 строк)
    data_sample_rows = crud.get_dataset_rows(db, dataset_id=dataset_id, limit=20)
    if not data_sample_rows:
        raise HTTPException(status_code=400, detail="Not enough data in the dataset to provide a suggestion.")

    data_sample = [row.row_data for row in data_sample_rows]

    # 3. Вызываем сервис для получения предложений
    suggestion_data = ai_services.get_schema_suggestion_from_ai(
        current_schema=current_schema,
        data_sample=data_sample
    )

    if "suggestion" not in suggestion_data:
         raise HTTPException(status_code=500, detail="AI failed to return a valid suggestion.")

    return {"suggestion": suggestion_data["suggestion"]}
