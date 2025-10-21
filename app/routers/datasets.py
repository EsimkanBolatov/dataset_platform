# app/routers/datasets.py
from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid
import csv
import io
from urllib.parse import quote
from .. import schemas, crud, auth, models, database
from fastapi import BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
import pandas as pd

router = APIRouter(
    dependencies=[Depends(auth.get_current_user)]
)

@router.post("", response_model=schemas.Dataset, status_code=201, tags=["Datasets"])
def create_new_dataset(dataset: schemas.DatasetCreate, db: Session = Depends(database.get_db),
                       current_user: models.User = Depends(auth.get_current_user)):
    # Проверка, существует ли шаблон
    template = crud.get_template(db, template_id=dataset.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return crud.create_dataset(db=db, dataset=dataset, user_id=current_user.id)


@router.get("", response_model=List[schemas.Dataset], tags=["Datasets"])
def read_datasets_for_user(db: Session = Depends(database.get_db),
                           current_user: models.User = Depends(auth.get_current_user), skip: int = 0, limit: int = 100):
    return crud.get_datasets(db, owner_id=current_user.id, skip=skip, limit=limit)


@router.get("/{dataset_id}", response_model=schemas.Dataset, tags=["Datasets"])
def read_dataset(dataset_id: uuid.UUID, db: Session = Depends(database.get_db)):
    db_dataset = crud.get_dataset(db, dataset_id=dataset_id)
    if db_dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return db_dataset


@router.post("/{dataset_id}/rows", response_model=schemas.DatasetRow, status_code=201, tags=["Datasets"])
def create_row_for_dataset(dataset_id: uuid.UUID, row: schemas.DatasetRowCreate,
                           db: Session = Depends(database.get_db)):
    return crud.create_dataset_row(db=db, row=row, dataset_id=dataset_id)


@router.get("/{dataset_id}/rows", response_model=List[schemas.DatasetRow], tags=["Datasets"])
def read_rows_for_dataset(dataset_id: uuid.UUID, db: Session = Depends(database.get_db), skip: int = 0,
                          limit: int = 100):
    return crud.get_dataset_rows(db=db, dataset_id=dataset_id, skip=skip, limit=limit)

# --- Функция для фоновой обработки ---
def process_csv_import(file_contents: str, dataset_id: uuid.UUID):
    """
    Парсит CSV и добавляет строки в БД. Эту функцию мы запустим в фоне.
    """
    print(f"--- Начало фонового импорта для датасета {dataset_id} ---")

    # Для фоновой задачи нужно создать свою собственную сессию БД
    db = database.SessionLocal()

    try:
        # Находим датасет и его схему
        db_dataset = crud.get_dataset(db, dataset_id=dataset_id)
        if not db_dataset:
            print(f"Ошибка импорта: датасет {dataset_id} не найден.")
            return

        template_schema = db_dataset.template.schema_
        field_names = [field.get("field_name", "") for field in template_schema.get("fields", [])]

        # Читаем CSV из строки
        string_io = io.StringIO(file_contents)
        reader = csv.reader(string_io)

        # Пропускаем заголовок
        header = next(reader, None)

        # Обрабатываем строки и добавляем в БД
        rows_added = 0
        for row in reader:
            row_data = {field_name: value for field_name, value in zip(field_names, row)}
            row_to_create = schemas.DatasetRowCreate(row_data=row_data)
            crud.create_dataset_row(db=db, row=row_to_create, dataset_id=dataset_id)
            rows_added += 1

        print(f"--- Фоновый импорт завершен. Добавлено {rows_added} строк. ---")

    finally:
        db.close()


@router.post("/{dataset_id}/import/csv", tags=["Datasets"])
async def import_dataset_from_csv(
    dataset_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Импортирует данные из CSV в датасет в фоновом режиме.
    """
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    # Читаем содержимое файла
    contents = await file.read()

    # Добавляем задачу в фон и сразу возвращаем ответ пользователю
    background_tasks.add_task(process_csv_import, contents.decode("utf-8"), dataset_id)

    return {"status": "ok", "message": "File import started in the background."}

@router.get("/{dataset_id}/export/csv", tags=["Datasets"])
def export_dataset_to_csv(dataset_id: uuid.UUID, db: Session = Depends(database.get_db)):
    """
    Экспортирует все строки датасета в CSV файл.
    """
    # 1. Находим датасет и связанные с ним шаблон и строки
    db_dataset = crud.get_dataset(db, dataset_id=dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 2. Получаем схему из шаблона, чтобы знать названия колонок
    template_schema = db_dataset.template.schema_
    # Извлекаем "field_name" для заголовков и "display_name" для красивых названий
    field_names = [field.get("field_name", "") for field in template_schema.get("fields", [])]
    display_names = [field.get("display_name", field_names[i]) for i, field in
                     enumerate(template_schema.get("fields", []))]

    # 3. Создаем CSV-файл в памяти
    string_io = io.StringIO()
    writer = csv.writer(string_io)

    # 4. Записываем заголовки (первую строку файла)
    writer.writerow(display_names)

    # 5. Получаем все строки датасета и записываем их в файл
    rows = crud.get_dataset_rows(db, dataset_id=dataset_id, limit=10000)  # Ограничим экспорт для безопасности
    for row in rows:
        # Извлекаем значения для каждой колонки в правильном порядке
        writer.writerow([row.row_data.get(field_name) for field_name in field_names])

    # 6. Создаем HTTP-ответ, который вернет файл
    response = StreamingResponse(
        iter([string_io.getvalue()]),
        media_type="text/csv"
    )

    # Формируем имя файла
    filename = f"{db_dataset.name}.csv"
    # Кодируем его в безопасный для URL формат, чтобы поддержать кириллицу
    encoded_filename = quote(filename)
    # Устанавливаем заголовок в формате RFC 6266
    response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"
    return response

@router.get("/{dataset_id}/export/xlsx", tags=["Datasets"])
def export_dataset_to_xlsx(dataset_id: uuid.UUID, db: Session = Depends(database.get_db)):
    """
    Экспортирует все строки датасета в XLSX файл.
    """
    # 1. Получаем датасет, его схему и строки (логика та же, что и для CSV)
    db_dataset = crud.get_dataset(db, dataset_id=dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    template_schema = db_dataset.template.schema_
    field_names = [field.get("field_name", "") for field in template_schema.get("fields", [])]
    display_names = [field.get("display_name", field_names[i]) for i, field in enumerate(template_schema.get("fields", []))]

    rows = crud.get_dataset_rows(db, dataset_id=dataset_id, limit=10000)

    # 2. Подготавливаем данные для pandas
    # Создаем список словарей, где каждый словарь - это строка
    data_for_df = []
    for row in rows:
        data_for_df.append({display: row.row_data.get(field) for field, display in zip(field_names, display_names)})

    # 3. Создаем pandas DataFrame
    df = pd.DataFrame(data_for_df)

    # 4. Создаем Excel-файл в памяти
    # Используем BytesIO, так как XLSX - это бинарный формат
    output_buffer = io.BytesIO()
    df.to_excel(output_buffer, index=False, sheet_name='Dataset')
    output_buffer.seek(0) # Перемещаем курсор в начало "файла"

    # 5. Создаем HTTP-ответ для скачивания файла
    headers = {
        'Content-Disposition': f'attachment; filename="{db_dataset.name}.xlsx"'
    }
    return StreamingResponse(
        output_buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )

@router.get("/{dataset_id}/export/json", tags=["Datasets"])
def export_dataset_to_json(dataset_id: uuid.UUID, db: Session = Depends(database.get_db)):
    """
    Экспортирует все строки датасета в JSON файл.
    """
    # 1. Находим датасет
    db_dataset = crud.get_dataset(db, dataset_id=dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 2. Получаем все строки и извлекаем из них только данные
    rows = crud.get_dataset_rows(db, dataset_id=dataset_id, limit=10000)
    data = [row.row_data for row in rows]

    # 3. Устанавливаем заголовок, чтобы браузер скачал файл
    headers = {
        'Content-Disposition': f'attachment; filename="{db_dataset.name}.json"'
    }

    # 4. Возвращаем JSONResponse с данными и заголовком
    return JSONResponse(content=data, headers=headers)

def process_xlsx_import(file_contents: bytes, dataset_id: uuid.UUID):
    """
    Парсит XLSX и добавляет строки в БД. Запускается в фоне.
    """
    print(f"--- Начало фонового импорта XLSX для датасета {dataset_id} ---")
    db = database.SessionLocal()
    try:
        db_dataset = crud.get_dataset(db, dataset_id=dataset_id)
        if not db_dataset:
            print(f"Ошибка импорта: датасет {dataset_id} не найден.")
            return

        # Создаем карту сопоставления "Display Name" -> "field_name"
        template_schema = db_dataset.template.schema_
        header_map = {
            field.get("display_name", field.get("field_name")): field.get("field_name")
            for field in template_schema.get("fields", [])
        }

        # Читаем Excel файл из байтов в pandas DataFrame
        df = pd.read_excel(io.BytesIO(file_contents))

        rows_added = 0
        # Итерируемся по строкам DataFrame
        for index, row in df.iterrows():
            # Преобразуем строку DataFrame в словарь, который соответствует схеме БД
            row_data = {}
            for display_name, field_name in header_map.items():
                if display_name in row:
                    row_data[field_name] = row[display_name]

            if row_data:
                row_to_create = schemas.DatasetRowCreate(row_data=row_data)
                crud.create_dataset_row(db=db, row=row_to_create, dataset_id=dataset_id)
                rows_added += 1

        print(f"--- Фоновый импорт XLSX завершен. Добавлено {rows_added} строк. ---")

    finally:
        db.close()


@router.post("/{dataset_id}/import/xlsx", tags=["Datasets"])
async def import_dataset_from_xlsx(
    dataset_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Импортирует данные из XLSX в датасет в фоновом режиме.
    """
    # Проверяем тип файла
    allowed_mimetypes = [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ]
    if file.content_type not in allowed_mimetypes:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an XLSX file.")

    contents = await file.read()
    background_tasks.add_task(process_xlsx_import, contents, dataset_id)

    return {"status": "ok", "message": "XLSX file import started in the background."}


