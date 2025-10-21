# app/ai/services.py
import json
from typing import List, Dict, Any
from groq import Groq
from ..config import GROQ_API_KEY, GROQ_MODEL_NAME

# 1. Создаем клиент Groq.
# Он будет автоматически использовать ключ, если вы установите его как переменную окружения,
# или можно передать его напрямую: client = Groq(api_key="ВАШ_КЛЮЧ")
client = Groq(api_key=GROQ_API_KEY)

# 2. Определяем системный промпт.
# Это инструкция для модели, которая не меняется. Она задает "личность" и формат ответа.
system_prompt = """
You are an expert assistant that generates synthetic data in JSON format.
Your response MUST be a valid JSON object that contains a single key "data", 
and the value of this key MUST be a list of objects.
Do not include any other text, explanations, or markdown formatting in your response.
"""


def generate_rows_for_schema(schema: Dict, instruction: str, count: int) -> List[Dict[str, Any]]:
    """
    Генерирует строки данных для датасета с помощью Groq API.
    """
    # 3. Формируем пользовательский промпт с переменными данными
    schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
    user_prompt = f"""
    Based on the provided data schema, generate {count} new data rows.
    Follow the user's instruction: "{instruction}".
    The data schema is as follows:
    {schema_str}
    """

    print("--- Отправка запроса в Groq API ---")
    try:
        # 4. Вызываем API Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # Мы используем быструю и умную модель Llama 3
            model=GROQ_MODEL_NAME,

            # Эта опция заставляет модель гарантированно вернуть валидный JSON!
            response_format={"type": "json_object"},

            # Температура влияет на "креативность" ответа
            temperature=0.7,
        )

        # 5. Получаем и парсим ответ
        response_str = chat_completion.choices[0].message.content
        print("--- Ответ от Groq API получен ---")

        # Преобразуем строковый JSON в Python-объект
        data = json.loads(response_str)

        # Возвращаем список из ключа "data", как мы просили в системном промпте
        return data.get("data", [])

    except Exception as e:
        print(f"❌ ОШИБКА при работе с Groq API: {e}")
        import traceback
        traceback.print_exc()
        return []

cleaning_system_prompt = """
You are an expert assistant that cleans and normalizes data in JSON format.
The user will provide you with a list of "dirty" JSON objects and an instruction for how to clean them.
Your response MUST be a valid JSON object with a single key "cleaned_data",
and the value of this key MUST be a list of the cleaned JSON objects in the same order as the input.
Do not include any other text, explanations, or markdown formatting in your response.
"""

def clean_rows_with_ai(
    schema: Dict,
    dirty_rows: List[Dict],
    instruction: str
) -> List[Dict[str, Any]]:
    """
    Очищает строки данных с помощью Groq API.
    """
    # Превращаем данные в строки для промпта
    schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
    dirty_rows_str = json.dumps(dirty_rows, indent=2, ensure_ascii=False)

    user_prompt = f"""
    Please clean the following data based on this instruction: "{instruction}".
    The data must conform to the following schema:
    {schema_str}

    Here is the list of "dirty" data objects to clean:
    {dirty_rows_str}
    """

    print("--- Отправка запроса на очистку в Groq API ---")
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": cleaning_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=GROQ_MODEL_NAME,
            response_format={"type": "json_object"},
            temperature=0.1, # Используем низкую температуру для предсказуемости
        )

        response_str = chat_completion.choices[0].message.content
        print("--- Ответ от Groq API получен ---")

        data = json.loads(response_str)
        return data.get("cleaned_data", [])

    except Exception as e:
        print(f"❌ ОШИБКА при работе с Groq API: {e}")
        return []

suggestion_system_prompt = """
You are an expert data analyst. Your task is to analyze a sample of JSON data and the current data schema it is supposed to follow. 
Your goal is to suggest improvements to the schema. For example, you might suggest changing a field's data type, splitting a single field into multiple fields, or adding a new field if you identify a consistent pattern in the data.

Your response MUST be a valid JSON object with a single key "suggestion". The value of this key should be a string containing your analysis and a markdown-formatted code block with the proposed new schema.
"""
def get_schema_suggestion_from_ai(
    current_schema: Dict,
    data_sample: List[Dict]
) -> Dict[str, Any]:
    """
    Анализирует данные и предлагает улучшения для схемы с помощью Groq API.
    """
    schema_str = json.dumps(current_schema, indent=2, ensure_ascii=False)
    sample_str = json.dumps(data_sample, indent=2, ensure_ascii=False)

    user_prompt = f"""
    Here is the current schema:
    {schema_str}

    Here is a sample of the data that is supposed to follow this schema:
    {sample_str}

    Please analyze this data and provide suggestions for improving the schema. Explain your reasoning.
    """

    print("--- Отправка запроса на анализ схемы в Groq API ---")
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": suggestion_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=GROQ_MODEL_NAME,
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        response_str = chat_completion.choices[0].message.content
        print("--- Ответ от Groq API получен ---")

        # Возвращаем весь JSON-объект, который должен содержать ключ "suggestion"
        return json.loads(response_str)

    except Exception as e:
        print(f"❌ ОШИБКА при работе с Groq API: {e}")
        return {"suggestion": "Failed to get a suggestion from the AI."}
