import os
import logging

# ================== НАЧАЛО БЛОКА ОТЛАДКИ ==================
# Включаем базовую конфигурацию логгирования, чтобы видеть ВСЕ сообщения
logging.basicConfig(level=logging.DEBUG)

# Принудительно устанавливаем уровень DEBUG для библиотеки huggingface_hub
# Это заставит её показывать все свои действия, включая сетевые запросы
logging.getLogger("huggingface_hub").setLevel(logging.DEBUG)
print("--- Режим подробного логгирования включен принудительно ---")
# =================== КОНЕЦ БЛОКА ОТЛАДКИ ===================

from huggingface_hub import InferenceClient

# ВАЖНО: Убедитесь, что здесь ваш правильный токен
HF_TOKEN = "hf_fUCN... (вставьте ваш полный WRITE токен сюда)"

client = InferenceClient(token=HF_TOKEN)
model_id = "google/flan-t5-large"
prompt_text = "Translate from English to French: How are you?"

print(f"--- Пытаюсь обратиться к модели: {model_id} ---")

try:
    response = client.text_generation(prompt=prompt_text, model=model_id)

    print("\n✅ УСПЕХ! Ответ от API получен:")
    print(response)

except Exception as e:
    print(f"\n❌ ОШИБКА! Не удалось получить ответ от API.")
    # Печатаем не только ошибку, но и полный traceback для диагностики
    import traceback
    traceback.print_exc()