from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()

# Предпочтительно хранить ключ и базовый URL в переменных окружения
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.artemox.com/v1")

if not API_KEY:
    raise ValueError("API_KEY не найден!")

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

def ask_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Ты автономный веб-агент. Возвращай ТОЛЬКО ОДНО действие."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()