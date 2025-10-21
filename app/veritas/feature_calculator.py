# app/veritas/feature_calculator.py

import pandas as pd
import io
from typing import Dict, Any, Union
import numpy as np

def calculate_features(file_contents: bytes, file_type: str = 'csv') -> Dict[str, Any]:
    """
    Вычисляет набор статистических признаков из содержимого файла.

    :param file_contents: Содержимое файла в виде байтов.
    :param file_type: Тип файла ('csv' или 'json').
    :return: Словарь с вычисленными признаками.
    """
    features = {}

    try:
        if file_type == 'csv':
            df = pd.read_csv(io.BytesIO(file_contents))
        elif file_type == 'json':
            df = pd.read_json(io.BytesIO(file_contents))
        elif file_type == 'xlsx':
            df = pd.read_excel(io.BytesIO(file_contents))
        else:
            raise ValueError("Unsupported file type")
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return {"error": "Failed to parse the file."}

    #Example

    features['row_count'] = len(df)
    features['column_count'] = len(df.columns)

    for col in df.columns:
        # Признаки для числовых колонок
        if pd.api.types.is_numeric_dtype(df[col]):
            features[f'{col}_mean'] = df[col].mean()
            features[f'{col}_std'] = df[col].std()
            features[f'{col}_skew'] = df[col].skew()
            features[f'{col}_kurtosis'] = df[col].kurt()

        # Признаки для текстовых/категориальных колонок
        elif pd.api.types.is_object_dtype(df[col]):
            # Коэффициент уникальности (отношение уникальных значений ко всем)
            features[f'{col}_uniqueness_ratio'] = df[col].nunique() / len(df) if len(df) > 0 else 0

    # Удаляем NaN/inf значения, которые не сериализуются в JSON
    cleaned_features = {}
    for key, value in features.items():
        # Проверяем, является ли значение числом и конечным (не NaN/inf)
        if isinstance(value, (int, float, np.number)) and np.isfinite(value):
            cleaned_features[key] = float(value)  # Приводим к float для совместимости с JSON
        else:
            cleaned_features[key] = value if isinstance(value, (int, float, str)) else None

    return cleaned_features