# app/routers/veritas.py

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List
import uuid

from .. import schemas, auth
from ..veritas import feature_calculator, predictor

router = APIRouter(
    prefix="/veritas",
    tags=["Veritas Analysis"],
    dependencies=[Depends(auth.get_current_user)]
)

@router.post("/analyze/file", response_model=schemas.VeritasResponse)
async def analyze_dataset_from_file(file: UploadFile = File(...)):
    """
    Анализирует датасет из файла (CSV/JSON) и возвращает оценку подлинности.
    """
    # 1. Определяем тип файла и читаем его содержимое
    file_type = None
    if file.content_type == "text/csv":
        file_type = 'csv'
    elif file.content_type == "application/json":
        file_type = 'json'
    elif file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        file_type = 'xlsx'
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload CSV or JSON.")

    contents = await file.read()

    # 2. Вычисляем статистические признаки
    features = feature_calculator.calculate_features(contents, file_type=file_type)
    if "error" in features:
        raise HTTPException(status_code=422, detail=features["error"])

    # 3. Получаем предсказание от ML-модели
    # Модель возвращает вероятность того, что датасет - СИНТЕТИЧЕСКИЙ (от 0.0 до 1.0)
    synthetic_probability = predictor.model_predictor.predict(features)

    # 4. Формируем итоговый ответ согласно ТЗ
    # Преобразуем вероятность синтетики в "оценку подлинности"
    authenticity_score = int((1 - synthetic_probability) * 100)

    # TODO: В будущем здесь будет логика генерации "доказательств" (evidence)
    # Пока используем заглушку
    evidence = [
        {"feature": "Benford's Law", "description": "Deviation is low", "impact": "low"},
        {"feature": "Column Correlation", "description": "Correlation matrix appears normal", "impact": "medium"}
    ]

    return {
        "request_id": uuid.uuid4(),
        "authenticity_score": authenticity_score,
        "evidence": evidence
    }