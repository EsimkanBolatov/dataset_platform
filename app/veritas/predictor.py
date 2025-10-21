# app/veritas/predictor.py

import joblib
import pandas as pd
from typing import Dict, Any

class ModelPredictor:
    def __init__(self, model_path: str):
        print(f"--- Загрузка ML-модели из файла: {model_path} ---")
        try:
            self.model = joblib.load(model_path)
            print("--- Модель успешно загружена ---")
        except Exception as e:
            self.model = None
            print(f" ОШИБКА: Не удалось загрузить модель. {e}")

    def predict(self, features: Dict[str, Any]) -> float:
        """
        Принимает на вход словарь со статистическими признаками
        и возвращает предсказание модели.
        """
        if not self.model:
            print("⚠️ ВНИМАНИЕ: Модель не загружена, возвращается значение по умолчанию.")
            return 0.5 # Возвращаем нейтральное значение, если модель не работает

        try:
            # Преобразуем входные данные в DataFrame, который ожидает модель
            # Убедитесь, что порядок колонок совпадает с тем, на котором обучалась модель
            df = pd.DataFrame([features])

            # Получаем вероятность класса "1" (синтетика)
            # Индекс [0, 1] может отличаться в зависимости от вашей модели
            probability = self.model.predict_proba(df)[0, 1]

            return float(probability)
        except Exception as e:
            print(f" ОШИБКА: Не удалось выполнить предсказание. {e}")
            return 0.5

# --- ГЛАВНАЯ ЧАСТЬ ---
# Создаем единственный экземпляр нашего предсказателя, который будет использоваться во всем приложении
model_predictor = ModelPredictor("app/ml_models/authenticity_model.pkl")