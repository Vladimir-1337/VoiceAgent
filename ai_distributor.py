#ai_distributor.py


# ai_distributor.py — Распределение остатка фразы по опциональным полям
# Блок D.1.1: Импорты и конфигурация

import sys
import json
import time
import requests

from voice_config import BASE_DIR; sys.path.insert(0, BASE_DIR)

# --- Bothub (основной AI) ---
BOTHUB_URL = "https://openai.bothub.chat/v1/chat/completions"
BOTHUB_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjI2M2Y3MTlhLWE5NGYtNGYwZi05YzRkLWM4OTY4NDAyODc3OCIsImlzRGV2ZWxvcGVyIjp0cnVlLCJpYXQiOjE3NzYyNzU0ODQsImV4cCI6MjA5MTg1MTQ4NCwianRpIjoiYXZUTG5Vb051S3RsUGJCTSJ9.j24nr5sD_qmwSb0t_BvMANWDT1cCOhURTUcT8ojgyfM"

# --- Timeweb (резервный AI) ---
TIMEWEB_URL = "https://agent.timeweb.cloud/api/v1/cloud-ai/agents/51d500b4-8aec-4339-a8f2-cc4b77675677/v1/chat/completions"
TIMEWEB_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCIsImtpZCI6IjFrYnhacFJNQGJSI0tSbE1xS1lqIn0.eyJ1c2VyIjoidmo4NjMxMjIiLCJ0eXBlIjoiYXBpX2tleSIsImFwaV9rZXlfaWQiOiI0ZjI4YmUzZi1jZDcxLTQzYTAtODAxOS1hYTRmZjQ1YzNjMWUiLCJpYXQiOjE3NzY3ODE2OTN9.0rGDtlcABt5wE6K4IU-1eZrHuTeUZFrebBZTa3ujF_SN95qDZADB-7O2qMR1CQpIQ88n0KUjdP3qlecu5z_XufK_SDPiNuKLOSSNWS3FoYJCeG48pYj4wuVnT-gAriVPYShOSuewpAFMxSmdxeRCvgIdNnBijkKExXo0bsQKrzutaxHNMiY5MhqBZ0KwZYTsH5A4iHNUq5Oeujl2VDTHrWY8YWXTdTi_Y8Q7M-c6uztOedVYLhuF0yHvRVXbXWWbHa_riXz78lIOvob6sPtDTbduqzBaB8XUrgDQ6btoZQnKQZSvyVA7NRXssij5nL-4nXLhFtwSA6hN4oOmPdqYgReiT-WGOEBtgQp4Kx54v9YBogifNsT0wyqrRSsGzP-loTIZfmdtidfJ-rG-f8JHFDsVpkAet7EvHuaURmf_jNIFb1dHYewb5QyR-o1R9uZY1lVIboTOeTCXKYNtF1ZCsvfLLlnGq1tg-VjwQHtqiYxORFzxdzuLa7DpkmIK-J2k"




# ai_distributor.py — продолжение
# Блок D.1.2: _call_bothub() — запрос к основному AI


def _call_bothub(prompt, text):
    """
    Отправляет запрос к Bothub (Claude Haiku).
    
    Вход:
        prompt — строка-инструкция для AI
        text   — остаток фразы, который нужно разобрать
    
    Выход:
        ответ AI (строка) или None при ошибке
    """
    headers = {
        "Authorization": f"Bearer {BOTHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "claude-haiku-4.5",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        "temperature": 0.0
    }
    
    try:
        response = requests.post(BOTHUB_URL, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            return content
        else:
            print(f"⚠️ Bothub ошибка API: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print("⚠️ Bothub: таймаут (15 сек)")
        return None
    except requests.exceptions.ConnectionError:
        print("⚠️ Bothub: ошибка соединения")
        return None
    except Exception as e:
        print(f"⚠️ Bothub: {e}")
        return None
        
        
        
        
# ai_distributor.py — продолжение
# Блок D.1.3: _call_timeweb() — запрос к резервному AI


def _call_timeweb(prompt, text):
    """
    Отправляет запрос к Timeweb DeepSeek (резервный AI).
    Вызывается только если Bothub недоступен.
    
    Вход:
        prompt — строка-инструкция для AI
        text   — остаток фразы, который нужно разобрать
    
    Выход:
        ответ AI (строка) или None при ошибке
    """
    headers = {
        "Authorization": f"Bearer {TIMEWEB_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "claude-opus-4.6-fast",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        "temperature": 0.0
    }
    
    try:
        response = requests.post(TIMEWEB_URL, headers=headers, json=payload, timeout=20)
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            print("✅ Timeweb ответил успешно.")
            return content
        else:
            print(f"❌ Timeweb ошибка API: {response.status_code} - {response.text[:100]}")
            return None
    except requests.exceptions.Timeout:
        print("❌ Timeweb: таймаут (20 сек)")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Timeweb: ошибка соединения")
        return None
    except Exception as e:
        print(f"❌ Timeweb: {e}")
        return None
        
        
        
# ai_distributor.py — продолжение
# Блок D.1.4: _call_ai() — оркестратор с fallback на резерв


def _call_ai(prompt, text):
    """
    Вызывает Bothub. Если недоступен — переключается на Timeweb.
    
    Вход:
        prompt — строка-инструкция для AI
        text   — остаток фразы, который нужно разобрать
    
    Выход:
        ответ AI (строка) или "" при полной недоступности обоих AI
    """
    # Попытка 1: Bothub (основной)
    print("🤖 Обращаюсь к Bothub...")
    result = _call_bothub(prompt, text)
    if result:
        return result
    
    # Попытка 2: Timeweb (резервный)
    print("🔄 Переключаюсь на Timeweb...")
    result = _call_timeweb(prompt, text)
    if result:
        return result
    
    # Оба AI недоступны
    print("❌ Оба AI недоступны. Распределение невозможно.")
    return ""
    
    
    
# ai_distributor.py — продолжение
# Блок D.2.1: Правила для title в промпте


PROMPT_TITLE_RULES = """
1. TITLE (главное действие):
   - Выдели ГЛАВНОЕ ДЕЙСТВИЕ: глагол + объект.
   - НЕ возвращай только глагол. Если есть дополнение — включи его.
   - Если объект не указан — верни глагол как есть.
   - Убери из title всё, что относится к другим полям (лица, время, место, «с собой»).
   - Примеры:
     «купить хлеб маме срочно» → title: «купить хлеб»
     «позвонить» → title: «позвонить»
     «забрать посылку на почте» → title: «забрать посылку»
     «сделать отчёт для начальника к вечеру» → title: «сделать отчёт»
"""



# ai_distributor.py — замена PROMPT_SLOT_RULES (Блок D.2.2, расширенный)


PROMPT_SLOT_RULES = """
2. SLOT (режим оперативной памяти, который занимает задача):
   - Определи, в каком режиме пользователь может выполнять эту задачу.
   - Только ОДИН из трёх вариантов, или пусто:

     · «ехать» — если есть фразы:
       «в дороге», «пока еду», «пешком», «в транспорте»,
       «за рулём», «в машине», «на ходу», «в пути»,
       «в автобусе», «в метро», «в маршрутке», «в такси»,
       «в поезде», «в электричке», «на трамвае», «на троллейбусе»,
       «по дороге», «по пути», «в движении», «на ходу»,
       «еду», «едешь», «идёшь», «шёл», «гуляю», «на прогулке»

     · «уткнуться в экран» — если есть фразы:
       «в телефоне», «за ноутбуком», «в планшете», «за компом»,
       «посмотреть на экране», «набрать текст», «прочитать с экрана»,
       «в интернете», «онлайн», «по зуму», «в зуме», «по видеосвязи»,
       «за монитором», «в чате», «написать», «напечатать»,
       «посмотреть видео», «в ютубе», «читать», «листать»

     · «делать привычное» — если есть фразы:
       «на автомате», «привычное», «руки делают», «не думая»,
       «на расслабоне», «готовка», «уборка», «стирка»,
       «по привычке», «рутина», «машинально», «автоматически»,
       «готовить», «убираться», «стирать», «мыть», «чистить»,
       «на кухне», «по дому», «домашние дела», «бытовуха»

   - Если ни одного триггера нет — оставь пусто.
   - Примеры:
     «купить хлеб в дороге» → slot: «ехать»
     «ответить в чате уткнувшись в экран» → slot: «уткнуться в экран»
     «приготовить ужин на автомате» → slot: «делать привычное»
     «купить хлеб» → slot: «»
     «созвон по зуму» → slot: «уткнуться в экран»
     «помыть посуду» → slot: «делать привычное»
     «послушать подкаст в метро» → slot: «ехать»
"""





# ai_distributor.py — продолжение
# Блок D.2.3: Правила для third_party и invite в промпте


PROMPT_PEOPLE_RULES = """
3. THIRD_PARTY (третье лицо) и INVITE (пригласить):
   - Если в остатке есть упоминание человека — выдели его в third_party.
   - Определи invite по предлогу ПЕРЕД лицом:
     · «с», «вместе с», «вдвоём с» → invite: true (пригласить как участника)
     · «для», «ради», «чтобы», «за» → invite: false (просто заметка)
     · Нет предлога → invite: false
   - Если лица нет — third_party: "", invite: false.
   - Примеры:
     «купить хлеб с мамой» → third_party: «мама», invite: true
     «купить хлеб для мамы» → third_party: «мама», invite: false
     «купить хлеб маме» → third_party: «мама», invite: false
     «позвонить врачу» → third_party: «врач», invite: false
     «купить хлеб» → third_party: "", invite: false
"""






# ai_distributor.py — продолжение
# Блок D.2.4: Правила для duration и description в промпте


PROMPT_DURATION_DESC_RULES = """
4. DURATION (длительность в минутах) и DESCRIPTION (заметки):
   - DURATION:
     · Если есть фразы «на полчаса», «займёт 15 минут», «на час» — выдели число минут.
     · «на полчаса» → 30, «на час» → 60, «на 15 минут» → 15.
     · Если длительность не указана — оставь пусто.
   - DESCRIPTION:
     · ВСЁ ОСТАЛЬНОЕ, что не попало в title, slot, third_party, duration — положи в description.
     · Слова-маркеры срочности («срочно», «важно», «кровь из носу») — включи в description.
     · Если ничего не осталось — оставь пусто.
   - Примеры:
     «купить хлеб срочно на полчаса» → duration: 30, description: «срочно»
     «позвонить маме важно» → duration: null, description: «важно»
     «купить хлеб» → duration: null, description: «»
"""



# ai_distributor.py — продолжение
# Блок D.2.5: Сборка полного промпта PROMPT_DISTRIBUTE


PROMPT_DISTRIBUTE = (
    "Ты — ассистент по разбору остатка фразы после того, как из неё уже убрали дату, время и место.\n"
    "Твоя задача — распределить остаток по полям и вернуть ТОЛЬКО валидный JSON.\n"
    "Никаких пояснений, приветствий, знаков препинания вне JSON.\n"
    "Ответ начинается с { и заканчивается }.\n\n"
    + PROMPT_TITLE_RULES + "\n"
    + PROMPT_SLOT_RULES + "\n"
    + PROMPT_PEOPLE_RULES + "\n"
    + PROMPT_DURATION_DESC_RULES + "\n"
    "ФОРМАТ ОТВЕТА (строго JSON, без пояснений):\n"
    '{"title": "...", "slot": "...", "third_party": "...", "invite": true/false, "duration": число или null, "description": "..."}'
)



# ai_distributor.py — продолжение
# Блок D.3.1: distribute() — вызов AI с промптом


def distribute(remainder):
    """
    Принимает остаток фразы, отправляет AI, получает распределение по полям.
    
    Вход:
        remainder — строка остатка после parse_intent
    
    Выход:
        словарь с полями: title, slot, third_party, invite, duration, description
    """
    if not remainder or not remainder.strip():
        return {
            "title": "",
            "slot": "",
            "third_party": "",
            "invite": False,
            "duration": None,
            "description": ""
        }
    
    print(f"🧠 AI распределяет остаток: «{remainder}»")
    raw = _call_ai(PROMPT_DISTRIBUTE, remainder)
    
    if not raw:
        print("⚠️ AI не ответил. Остаток уходит в title целиком.")
        return {
            "title": remainder,
            "slot": "",
            "third_party": "",
            "invite": False,
            "duration": None,
            "description": ""
        }
    
    # Парсинг и валидация — в D.3.2
    # Пока возвращаем заглушку
    return {
        "title": remainder,
        "slot": "",
        "third_party": "",
        "invite": False,
        "duration": None,
        "description": ""
    }
    
    
    
# ai_distributor.py — замена функции distribute (Блок D.3.2)


def distribute(remainder):
    """
    Принимает остаток фразы, отправляет AI, получает распределение по полям.
    
    Вход:
        remainder — строка остатка после parse_intent
    
    Выход:
        словарь с полями: title, slot, third_party, invite, duration, description
    """
    # Умолчания для всех полей
    defaults = {
        "title": remainder if remainder else "",
        "slot": "",
        "third_party": "",
        "invite": False,
        "duration": None,
        "description": ""
    }
    
    if not remainder or not remainder.strip():
        return defaults
    
    print(f"🧠 AI распределяет остаток: «{remainder}»")
    raw = _call_ai(PROMPT_DISTRIBUTE, remainder)
    
    if not raw:
        print("⚠️ AI не ответил. Остаток уходит в title целиком.")
        return defaults
    
    # Парсинг JSON
    try:
        raw_clean = raw.strip()
        if raw_clean.startswith("```json"):
            raw_clean = raw_clean.replace("```json", "").replace("```", "").strip()
        if raw_clean.startswith("```"):
            raw_clean = raw_clean.replace("```", "").strip()
        result = json.loads(raw_clean)
    except json.JSONDecodeError:
        print(f"⚠️ AI вернул не JSON: «{raw[:80]}...». Остаток уходит в title.")
        return defaults
    
    # Валидация: проверяем наличие всех полей, подставляем умолчания
    title = result.get("title", "").strip()
    if not title:
        title = remainder  # если AI не дал title — берём остаток целиком
    
    slot = result.get("slot", "").strip()
    # Приводим слот к одному из трёх вариантов
    allowed_slots = ["ехать", "уткнуться в экран", "делать привычное"]
    if slot not in allowed_slots:
        slot = ""
    
    third_party = result.get("third_party", "").strip()
    
    invite = result.get("invite", False)
    if not isinstance(invite, bool):
        invite = False
    
    invite_email = result.get("invite_email", "").strip()
    
    duration = result.get("duration")
    if duration is not None and not isinstance(duration, int):
        try:
            duration = int(duration)
        except (ValueError, TypeError):
            duration = None
    
    description = result.get("description", "").strip()
    
    return {
        "title": title,
        "slot": slot,
        "third_party": third_party,
        "invite": invite,
        "invite_email": invite_email,
        "duration": duration,
        "description": description
    }
    
    
    
# ai_distributor.py — продолжение
# Блок D.4.1: build_title() — сборка title с разделителями |


def build_title(distributed, items=None):
    """
    Собирает title из главного действия и дополнительных полей.
    Поля разделяются символом | для читаемости в SMS и календаре.
    
    Вход:
        distributed — словарь от distribute(): title, slot, third_party, duration, description
        items       — список предметов от parse_intent (опционально)
    
    Выход:
        строка title с разделителями |
    """
    parts = []
    
    # 1. Главное действие (обязательно)
    title = distributed.get("title", "").strip()
    if title:
        parts.append(title)
    
    # 2. Предметы "с собой"
    if items:
        items_str = ", ".join(items)
        if items_str:
            parts.append(items_str)
    
    # 3. Третье лицо
    tp = distributed.get("third_party", "").strip()
    if tp:
        parts.append(tp)
    
    # 4. Длительность
    dur = distributed.get("duration")
    if dur and isinstance(dur, int) and dur > 0:
        parts.append(f"{dur} мин")
    
    # 5. Слот
    slot = distributed.get("slot", "").strip()
    if slot:
        parts.append(slot)
    
    # 6. Описание (остаток)
    desc = distributed.get("description", "").strip()
    if desc:
        parts.append(desc)
    
    return " | ".join(parts)







# ai_distributor.py — продолжение
# Блок D.4.2 (F.3): merge_task() с приоритетом intent над distributed


def merge_task(intent, distributed, items=None):
    """
    Объединяет результаты parse_intent и distribute в готовый словарь задачи.
    
    Вход:
        intent      — словарь от parse_intent (date, time, place, third_party, invite, ...)
        distributed — словарь от distribute (title, slot, third_party, ...)
        items       — список предметов от parse_intent
    
    Выход:
        словарь задачи для ready_tasks.json
    """
    # Собираем title с палочками
    title = build_title(distributed, items)
    
    # third_party и invite: приоритет у парсера (intent), fallback на AI (distributed)
    third_party = intent.get("third_party", "") or distributed.get("third_party", "")
    invite = intent.get("invite", False) or distributed.get("invite", False)
    invite_email = intent.get("invite_email", "") or distributed.get("invite_email", "")
    
    task = {
        "date": intent.get("date", ""),
        "time": intent.get("time", ""),
        "place": intent.get("place", ""),
        "title": title,
        "duration": distributed.get("duration") or 5,
        "repeat": {"type": "none", "days": [], "interval_minutes": 0, "until": ""},
        "description": ", ".join(items) if items else "",
        "slot": distributed.get("slot", ""),
        "third_party": third_party,
        "invite": invite,
        "invite_email": invite_email,
        "caldav_uid": "",
        "exported": False
    }
    
    return task


# ai_distributor.py — продолжение
# Блок S.1.1: Промпт для AI-очистки текста

CLEAN_PROMPT = """
Ты — ассистент по очистке текста от диктофона.
Твоя задача — привести сырой текст в порядок, НЕ меняя смысл и НЕ добавляя ничего от себя.

ПРАВИЛА (строго):
1. Убери слова-паразиты: "типа", "короче", "блин", "ну", "э-э-э", "как его", "в общем", "это самое", "так сказать".
2. Убери повторяющиеся союзы подряд: "и... и... и..." оставь один "и".
3. Если Whisper вставил одиночную точку ВНУТРИ цельной фразы (пауза при раздумье) — склей части обратно, убрав точку. 
   Пример: "купить хлеб . завтра в 16 дома" → "купить хлеб завтра в 16 дома".
4. Исправь очевидные опечатки Whisper: "на помни" → "напомни", "завтро" → "завтра", "сегодя" → "сегодня", "в 16 ноль ноль" → "в 16:00".
5. НЕ трогай слово "ПРИКАЗЫВАЮ" — оно должно остаться как есть.
6. НЕ меняй даты, время, названия мест, имена людей.
7. Верни ТОЛЬКО очищенный текст. Без пояснений, без приветствий.

Примеры:
Вход: "купить типа хлеба завтра... ну и ещё блин позвонить маме"
Выход: "купить хлеб завтра и позвонить маме"

Вход: "на помни купить хлеб завтро в 16 ноль ноль дома"
Выход: "напомни купить хлеб завтра в 16:00 дома"

Вход: "купить хлеб . завтра в 16 дома"
Выход: "купить хлеб завтра в 16 дома"
"""



# ai_distributor.py — замена функции ai_clean_text (Блок S.1.2, финал)

def ai_clean_text(text):
    """
    Отправляет текст в AI для очистки от мусора.
    Пробует Bothub, при ошибке — Timeweb (резерв).
    При падении обоих AI возвращает исходный текст без изменений.
    
    Вход:  сырой текст от Whisper
    Выход: очищенный текст
    """
    if not text or not text.strip():
        return text
    
    # Не дёргаем AI для коротких фраз
    if len(text.split()) < 5:
        return text
    
    print("   🧹 AI очищает текст от мусора...")
    
    # Пробуем Bothub
    result = _call_bothub(CLEAN_PROMPT, text)
    
    # Если Bothub вернул ошибку или пустоту — пробуем Timeweb
    if not result:
        print("   🔄 Bothub недоступен, пробую Timeweb...")
        result = _call_timeweb(CLEAN_PROMPT, text)
    
    if result:
        result = result.strip().strip('"').strip("'")
        if result:
            return result
    
    print("   ⚠️ Оба AI недоступны — использую исходный текст")
    return text