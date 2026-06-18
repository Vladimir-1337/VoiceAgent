# ============================================================
# ai_distributor.py — ПОД КЛЮЧ (БЕЗ ТОКЕНОВ, ТОЛЬКО ПРОКСИ)
# ============================================================
import sys
import json
import time
import requests

from voice_config import BASE_DIR; sys.path.insert(0, BASE_DIR)

from config import AI_PRIMARY_URL as BOTHUB_URL, AI_FALLBACK_URL as TIMEWEB_URL

# ==================== BOTHUB (ОСНОВНОЙ) ====================
def _call_bothub(prompt, text):
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "claude-haiku-4.5",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        "temperature": 0.0
    }
    try:
        r = requests.post(BOTHUB_URL, headers=headers, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()['choices'][0]['message']['content']
        print(f"⚠️ Bothub ошибка API: {r.status_code}")
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

# ==================== TIMEWEB (РЕЗЕРВ) ====================
def _call_timeweb(prompt, text):
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "claude-opus-4.6-fast",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text}
        ],
        "temperature": 0.0
    }
    try:
        r = requests.post(TIMEWEB_URL, headers=headers, json=payload, timeout=20)
        if r.status_code == 200:
            print("✅ Timeweb ответил успешно.")
            return r.json()['choices'][0]['message']['content']
        print(f"❌ Timeweb ошибка API: {r.status_code} - {r.text[:100]}")
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

# ==================== ОРКЕСТРАТОР ====================
def _call_ai(prompt, text):
    print("🤖 Обращаюсь к Bothub...")
    result = _call_bothub(prompt, text)
    if result:
        return result
    print("🔄 Переключаюсь на Timeweb...")
    result = _call_timeweb(prompt, text)
    if result:
        return result
    print("❌ Оба AI недоступны.")
    return ""

# ==================== ПРОМПТЫ ====================
PROMPT_TITLE_RULES = """
1. TITLE (главное действие):
   - Выдели ГЛАВНОЕ ДЕЙСТВИЕ: глагол + объект.
   - НЕ возвращай только глагол. Если есть дополнение — включи его.
   - Убери из title всё, что относится к другим полям (лица, время, место, «с собой»).
"""

PROMPT_SLOT_RULES = """
2. SLOT (режим оперативной памяти):
   - Только ОДИН из трёх: «ехать», «уткнуться в экран», «делать привычное», или пусто.
   - «ехать» — если есть «в дороге», «пока еду», «пешком», «в транспорте», «за рулём», «в метро», «в такси», «по пути».
   - «уткнуться в экран» — если есть «в телефоне», «за ноутбуком», «в планшете», «онлайн», «по зуму», «читать», «листать».
   - «делать привычное» — если есть «на автомате», «привычное», «руки делают», «готовка», «уборка», «стирка».
   - Если ни одного триггера нет — оставь пусто.
"""

PROMPT_PEOPLE_RULES = """
3. THIRD_PARTY (третье лицо) и INVITE (пригласить):
   - Если есть упоминание человека — выдели в third_party.
   - «с», «вместе с» → invite: true. «для», «ради» → invite: false. Нет предлога → invite: false.
"""

PROMPT_DURATION_DESC_RULES = """
4. DURATION (минуты) и DESCRIPTION (заметки):
   - DURATION: «на полчаса»→30, «на час»→60, «на 15 минут»→15. Иначе null.
   - DESCRIPTION: всё остальное (срочность, важность и т.д.).
"""

PROMPT_DISTRIBUTE = (
    "Ты — ассистент по разбору остатка фразы. Верни ТОЛЬКО валидный JSON.\n"
    "Ответ начинается с { и заканчивается }.\n\n"
    + PROMPT_TITLE_RULES + "\n"
    + PROMPT_SLOT_RULES + "\n"
    + PROMPT_PEOPLE_RULES + "\n"
    + PROMPT_DURATION_DESC_RULES + "\n"
    'ФОРМАТ: {"title": "...", "slot": "...", "third_party": "...", "invite": true/false, "duration": число/null, "description": "..."}'
)

CLEAN_PROMPT = """
Ты — ассистент по очистке текста от диктофона.
ПРАВИЛА:
1. Убери слова-паразиты: "типа", "короче", "блин", "ну", "э-э-э".
2. Убери повторяющиеся союзы подряд.
3. Одиночную точку внутри фразы → склей части.
4. Исправь очевидные опечатки: "на помни"→"напомни", "завтро"→"завтра", "в 16 ноль ноль"→"в 16:00".
5. НЕ трогай "ПРИКАЗЫВАЮ".
6. НЕ меняй даты, время, места, имена.
7. Верни ТОЛЬКО очищенный текст.
"""

# ==================== ФУНКЦИИ ====================
def distribute(remainder):
    defaults = {
        "title": remainder if remainder else "",
        "slot": "",
        "third_party": "",
        "invite": False,
        "invite_email": "",
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
    
    try:
        raw_clean = raw.strip()
        if raw_clean.startswith("```json"):
            raw_clean = raw_clean.replace("```json", "").replace("```", "").strip()
        if raw_clean.startswith("```"):
            raw_clean = raw_clean.replace("```", "").strip()
        result = json.loads(raw_clean)
    except json.JSONDecodeError:
        print(f"⚠️ AI вернул не JSON: «{raw[:80]}...».")
        return defaults
    
    title = result.get("title", "").strip() or remainder
    slot = result.get("slot", "").strip()
    if slot not in ["ехать", "уткнуться в экран", "делать привычное"]:
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

def build_title(distributed, items=None):
    parts = []
    title = distributed.get("title", "").strip()
    if title:
        parts.append(title)
    if items:
        parts.append(", ".join(items))
    tp = distributed.get("third_party", "").strip()
    if tp:
        parts.append(tp)
    dur = distributed.get("duration")
    if dur and isinstance(dur, int) and dur > 0:
        parts.append(f"{dur} мин")
    slot = distributed.get("slot", "").strip()
    if slot:
        parts.append(slot)
    desc = distributed.get("description", "").strip()
    if desc:
        parts.append(desc)
    return " | ".join(parts)

def merge_task(intent, distributed, items=None):
    title = build_title(distributed, items)
    third_party = intent.get("third_party", "") or distributed.get("third_party", "")
    invite = intent.get("invite", False) or distributed.get("invite", False)
    invite_email = intent.get("invite_email", "") or distributed.get("invite_email", "")
    return {
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

def ai_clean_text(text):
    if not text or not text.strip():
        return text
    if len(text.split()) < 5:
        return text
    print("   🧹 AI очищает текст от мусора...")
    result = _call_bothub(CLEAN_PROMPT, text)
    if not result:
        print("   🔄 Bothub недоступен, пробую Timeweb...")
        result = _call_timeweb(CLEAN_PROMPT, text)
    if result:
        result = result.strip().strip('"').strip("'")
        if result:
            return result
    print("   ⚠️ Оба AI недоступны — использую исходный текст")
    return text