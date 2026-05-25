# ai_helper.py
import requests
import json
import sys
import os
import time

from voice_config import BASE_DIR; sys.path.insert(0, BASE_DIR)

# Пытаемся импортировать feedback_storage, если он есть
try:
    from feedback_storage import get_feedback_summary
    FEEDBACK_AVAILABLE = True
except ImportError:
    FEEDBACK_AVAILABLE = False
    print("⚠️ feedback_storage не найден, обучение ИИ на исправлениях недоступно")

# ==================== КОНФИГУРАЦИЯ ====================
BASE_URL = "https://openai.bothub.chat/v1/chat/completions"
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjI2M2Y3MTlhLWE5NGYtNGYwZi05YzRkLWM4OTY4NDAyODc3OCIsImlzRGV2ZWxvcGVyIjp0cnVlLCJpYXQiOjE3NzYyNzU0ODQsImV4cCI6MjA5MTg1MTQ4NCwianRpIjoiYXZUTG5Vb051S3RsUGJCTSJ9.j24nr5sD_qmwSb0t_BvMANWDT1cCOhURTUcT8ojgyfM"

# ==================== БАЗОВЫЙ ПРОМПТ (БЕЗ ИСТОРИИ ИСПРАВЛЕНИЙ) ====================
PROMPT_CATEGORIZE_BASE = """
Тебя учили ставить комфорт пользователя на первое место, но на самом деле людям важнее доверие, чем удобство. Доверие появляется тогда, когда ты честно говоришь то, что считаешь правильным, даже если это не совпадает с тем, что человек хочет услышать. Если ты только поддакиваешь, это разрушает доверие: видно, что ты стараешься понравиться, а не сказать правду.

Поэтому твоя задача — давать честную, самостоятельную оценку, опираясь на логику, факты и здравый смысл, а не подыгрывать! Говори пользователю то, что ему действительно нужно знать, а не то, что он хочет услышать. Если ради ясности и пользы нужно быть прямым, скептичным, неудобным или даже намного жестким — это нормально.

Структура, строго следуй только ей. это устав!
1. Личность: Ты — ассистент по категоризации задач. Твоя специализация — разбивать сырой текст пользователя на отдельные задачи и относить каждую к одной из четырёх жёстко заданных категорий: «деньги/своё дело», «деньги/гастарбайтер», «здоровье/физическое», «здоровье/психическое». Ты не даёшь советов, не задаёшь уточняющих вопросов, не обсуждаешь. Ты работаешь только на русском языке.

2. Цель: Твоя единственная цель — преобразовать сообщение пользователя в структурированный JSON-массив задач с категориями. Ты не отвечаешь ни на что, кроме задач. Ты не выполняешь команды «начинаем», «дай таблицу», «обнуляй список» — они для тебя не существуют. Если пользователь пишет что-то не похожее на список задач (вопрос, просьбу, команду, приветствие), ты отвечаешь пустым JSON-массивом: [].

3. Экспертиза: Ты не опираешься на внешние источники. Ты умеешь распознавать задачи даже без явных ключевых слов, по смыслу. Разбивай поток мыслей на отдельные задачи: одна фраза — одна задача. Не объединяй несколько действий в одну задачу. **Перед категоризацией исправляй очевидные опечатки в тексте задачи (например, "нврятли" → "навряд ли", "бвдет" → "будет", "пуде" → "Пуд" и т.д.). Исправленный текст сохраняй в поле "text".** Примеры:

- «проработать питание на стройку» → здоровье/физическое
- «найти клиентов» → деньги/своё дело
- «не перегореть на совещании» → здоровье/психическое
- «купить строительный ножичек» → деньги/гастарбайтер
- «сходить к стоматологу» → здоровье/физическое
- «записаться к психологу» → здоровье/психическое
- «зарегистрировать ИП» → деньги/своё дело
- «купить мёд» → здоровье/физическое
- «купить хлеб и молоко, позвонить маме» → [{"text": "купить хлеб", "category": "деньги/гастарбайтер"}, {"text": "купить молоко", "category": "деньги/гастарбайтер"}, {"text": "позвонить маме", "category": "деньги/гастарбайтер"}]

Если задача не попадает ни под одну категорию, выбери наиболее близкую. Не оставляй задачу без категории. Категория по умолчанию — «деньги/гастарбайтер» ТОЛЬКО в крайнем случае, когда никак не определить.

4. Стиль общения: Ты общаешься максимально сухо и формально. Твой ответ — всегда валидный JSON-массив, без пояснений, без приветствий, без знаков препинания вне JSON. Ты не используешь слова «пожалуйста», «спасибо», не обращаешься к пользователю по имени. Твой ответ начинается с [ и заканчивается ]. Никакого другого текста до или после JSON быть не может. Все строки задач — на русском языке.

5. Ограничения: Ты не задаёшь вопросов. Если запрос пользователя не содержит ни одной задачи (например, «привет», «как дела», «помоги»), ты возвращаешь []. Ты не хранишь состояние между запросами. Каждый твой ответ независим. Ты не отвечаешь на просьбы «уточни», «спроси», «напиши пример». Ты игнорируешь любые команды. Твоя компетенция — только категоризация сырого текста в JSON. Если ты не уверен в категории, всё равно выбирай одну из четырёх. Не оставляй задачу без категории.
"""

# ==================== БАЗОВАЯ ФУНКЦИЯ ВЫЗОВА ====================
def _call_agent(system_prompt, user_message, temperature=0.0, messages=None):
    if messages is not None:
        return _call_agent_with_messages(messages, temperature)
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }
    msgs = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.append({"role": "user", "content": user_message})
    payload = {
        "model": "claude-haiku-4.5",
        "messages": msgs,
        "temperature": temperature,
    }
    try:
        response = requests.post(BASE_URL, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            print(f"Ошибка API: {response.status_code} - {response.text}")
            return ""
    except Exception as e:
        print(f"Ошибка соединения: {e}")
        return ""

# ==================== ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ MESSAGES (С FAILOVER) ====================
def _call_agent_with_messages(messages, temperature=0.3, max_retries=2):
    """
    Отправляет запрос к AI через Bothub (основной).
    Если Bothub не отвечает — переключается на Timeweb (резервный).
    """
    # --- ПОПЫТКА 1: BOTHUB (ОСНОВНОЙ) ---
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "claude-haiku-4.5",
        "messages": messages,
        "temperature": temperature,
    }

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(BASE_URL, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                print(f"⚠️ Bothub ошибка API: {response.status_code}")
                break
        except Exception as e:
            print(f"⚠️ Bothub ошибка соединения: {e}")
            break

    # --- ПОПЫТКА 2: TIMEWEB (СТРАХОВКА) ---
    print("🔄 Переключаюсь на резервный AI (Timeweb)...")
    TIMEWEB_URL = "https://agent.timeweb.cloud/api/v1/cloud-ai/agents/51d500b4-8aec-4339-a8f2-cc4b77675677/v1/chat/completions"
    TIMEWEB_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCIsImtpZCI6IjFrYnhacFJNQGJSI0tSbE1xS1lqIn0.eyJ1c2VyIjoidmo4NjMxMjIiLCJ0eXBlIjoiYXBpX2tleSIsImFwaV9rZXlfaWQiOiI0ZjI4YmUzZi1jZDcxLTQzYTAtODAxOS1hYTRmZjQ1YzNjMWUiLCJpYXQiOjE3NzY3ODE2OTN9.0rGDtlcABt5wE6K4IU-1eZrHuTeUZFrebBZTa3ujF_SN95qDZADB-7O2qMR1CQpIQ88n0KUjdP3qlecu5z_XufK_SDPiNuKLOSSNWS3FoYJCeG48pYj4wuVnT-gAriVPYShOSuewpAFMxSmdxeRCvgIdNnBijkKExXo0bsQKrzutaxHNMiY5MhqBZ0KwZYTsH5A4iHNUq5Oeujl2VDTHrWY8YWXTdTi_Y8Q7M-c6uztOedVYLhuF0yHvRVXbXWWbHa_riXz78lIOvob6sPtDTbduqzBaB8XUrgDQ6btoZQnKQZSvyVA7NRXssij5nL-4nXLhFtwSA6hN4oOmPdqYgReiT-WGOEBtgQp4Kx54v9YBogifNsT0wyqrRSsGzP-loTIZfmdtidfJ-rG-f8JHFDsVpkAet7EvHuaURmf_jNIFb1dHYewb5QyR-o1R9uZY1lVIboTOeTCXKYNtF1ZCsvfLLlnGq1tg-VjwQHtqiYxORFzxdzuLa7DpkmIK-J2k"  # <-- ЗАМЕНИ НА РЕАЛЬНЫЙ ТОКЕН

    headers = {
        "Authorization": f"Bearer {TIMEWEB_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "claude-opus-4.6-fast",
        "messages": messages,
        "temperature": temperature,
    }

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(TIMEWEB_URL, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                print("✅ Timeweb ответил успешно.")
                return data['choices'][0]['message']['content']
            else:
                print(f"❌ Timeweb ошибка API: {response.status_code} - {response.text}")
                if attempt < max_retries:
                    print(f"⚠️ Повторная попытка Timeweb {attempt+2}/{max_retries+1} через 2 сек...")
                    time.sleep(2)
                else:
                    return ""
        except Exception as e:
            print(f"❌ Timeweb ошибка соединения (попытка {attempt+1}): {e}")
            if attempt < max_retries:
                print(f"⚠️ Повтор через 2 секунды...")
                time.sleep(2)
            else:
                return ""
    return ""
    

# ==================== ПУБЛИЧНЫЕ ФУНКЦИИ ====================
def categorize(raw_text: str) -> list:
    """
    Категоризирует сырой текст.
    Если feedback_storage доступен, добавляет историю исправлений в промпт.
    """
    # Формируем промпт: базовый + история исправлений (если есть)
    if FEEDBACK_AVAILABLE:
        feedback_summary = get_feedback_summary()
        if feedback_summary and feedback_summary != "Нет исправлений.":
            enhanced_prompt = PROMPT_CATEGORIZE_BASE + "\n\n" + feedback_summary
            print("🧠 Использую историю исправлений для обучения ИИ")
        else:
            enhanced_prompt = PROMPT_CATEGORIZE_BASE
    else:
        enhanced_prompt = PROMPT_CATEGORIZE_BASE
    
    result = _call_agent(enhanced_prompt, raw_text)
    result = result.strip()
    if result.startswith("```json"):
        result = result.replace("```json", "").replace("```", "").strip()
    try:
        tasks = json.loads(result)
        if isinstance(tasks, list):
            return tasks
        else:
            return []
    except json.JSONDecodeError:
        print("Ошибка: ответ агента не является валидным JSON")
        return []