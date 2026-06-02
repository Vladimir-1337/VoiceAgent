# caldav_client.py — Финальная версия с эмуляцией интервалов
# URL календаря берётся из voice_config.py (один IP для всего)

import requests
import json
import time
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, "/storage/emulated/0/VoiceAgent")

# URL CalDAV — автоматически из voice_config.py
try:
    from voice_config import SERVER_URL as _VOICE_URL
    MCP_SERVER_URL = _VOICE_URL.replace(":5000/voice", ":8100/mcp")
except ImportError:
    # Fallback: если voice_config не найден — жёсткий IP
    MCP_SERVER_URL = "http://157.22.202.232:8100/mcp"

# Кеш
_calendar_url_cache = None

# Безопасные пределы для интервалов
MIN_INTERVAL_MINUTES = 1        # минимальный шаг 1 минута
MAX_INTERVAL_EVENTS = 100       # максимум событий в одной серии
SAFE_DELAY_SEC = 2              # пауза между запросами к Яндекс


# ---------- НИЗКОУРОВНЕВЫЙ ВЫЗОВ MCP ----------
def _call_mcp(method, args, timeout=30):
    """Отправляет запрос на VPS. Возвращает (True, result) или (False, error)."""
    try:
        response = requests.post(
            MCP_SERVER_URL,
            json={"method": method, "args": args},
            timeout=timeout
        )
        data = response.json()
        if data.get("ok"):
            return (True, data["result"])
        else:
            return (False, data.get("error", "Неизвестная ошибка"))
    except requests.exceptions.Timeout:
        return (False, f"Таймаут ({timeout} сек) – VPS не отвечает")
    except requests.exceptions.ConnectionError:
        return (False, "VPS недоступен. Проверь интернет или сервер.")
    except Exception as e:
        return (False, str(e))


# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def get_calendar_url():
    global _calendar_url_cache
    if _calendar_url_cache:
        return _calendar_url_cache
    ok, result = _call_mcp("list-calendars", {}, timeout=15)
    if not ok:
        return None
    try:
        text = result['content'][0]['text']
        calendars = json.loads(text)
        url = calendars[0]['url']
        _calendar_url_cache = url
        return url
    except:
        return None


def _build_start_end(task):
    date_str = task.get("date", "")
    time_str = task.get("time", "")
    duration = task.get("duration", 5)
    if not date_str or not time_str:
        return (None, None)
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        start = dt.strftime("%Y-%m-%dT%H:%M:%S") + "+03:00"
        end_dt = dt + timedelta(minutes=duration)
        end = end_dt.strftime("%Y-%m-%dT%H:%M:%S") + "+03:00"
        return (start, end)
    except ValueError:
        return (None, None)


def _build_description(task):
    desc = task.get("description", "").strip()
    slot = task.get("slot", "").strip()
    parts = []
    if desc:
        parts.append(desc)
    if slot:
        parts.append(f"[Слот: {slot}]")
    return " ".join(parts)


# ---------- ПРАВИЛА ПОВТОРЕНИЯ (daily / weekly) ----------
def build_rrule(repeat):
    """
    Преобразует repeat в recurrenceRule.
    Поддерживаются только daily и weekly (интервалы эмулируются отдельно).
    """
    if not isinstance(repeat, dict):
        return None
    rtype = repeat.get("type", "none")
    if rtype in ("none", "interval") or not rtype:
        return None

    until = repeat.get("until", "").strip()

    if rtype == "daily":
        result = {"freq": "DAILY"}
        if until:
            result["until"] = until
        return result

    if rtype == "weekly":
        days = repeat.get("days", [])
        day_names = {1: "MO", 2: "TU", 3: "WE", 4: "TH", 5: "FR", 6: "SA", 7: "SU"}
        if days:
            byday = [day_names[d] for d in days if isinstance(d, int) and 1 <= d <= 7]
            result = {"freq": "WEEKLY", "byday": byday} if byday else {"freq": "WEEKLY"}
        else:
            result = {"freq": "WEEKLY"}
        if until:
            result["until"] = until
        return result

    return None


# ---------- СОЗДАНИЕ ОДНОГО СОБЫТИЯ ----------
def create_event(task):
    """Создаёт одно событие в Яндекс.Календаре. Возвращает UID или None."""
    calendar_url = get_calendar_url()
    if not calendar_url:
        print("# Ошибка: не удалось получить URL календаря")
        return None
    start, end = _build_start_end(task)
    if not start or not end:
        print(f"# Ошибка: не удалось собрать start/end")
        return None
    args = {
        "summary":     task.get("title", ""),
        "start":       start,
        "end":         end,
        "calendarUrl": calendar_url,
        "description": _build_description(task),
        "location":    task.get("place", ""),
        "attendee":    [{"email": task["invite_email"]}] if task.get("invite") and task.get("invite_email") else []
    }
    rrule = build_rrule(task.get("repeat", {}))
    if rrule:
        args["recurrenceRule"] = rrule
    print(f"# Создаю событие: {args['summary']} на {start}")
    ok, result = _call_mcp("create-event", args, timeout=20)
    if not ok:
        print(f"# Ошибка создания события: {result}")
        return None
    try:
        uid = result['content'][0]['text'].strip()
        print(f"# Событие создано, UID={uid}")
        return uid
    except:
        return None


# ---------- ЭМУЛЯЦИЯ ИНТЕРВАЛА ----------
def create_interval_events(task):
    """
    Эмулирует повторение 'каждые N минут' созданием цепочки отдельных событий.
    
    Аргументы внутри task:
        task['repeat']['interval_minutes'] = шаг в минутах (≥ 1)
        task['repeat']['until'] = время окончания в формате 'YYYY-MM-DDTHH:MM:SSZ'
                                  или пустая строка (бесконечно – не поддерживается в эмуляции)
    
    Возвращает список созданных UID (может быть пустым при ошибке).
    """
    repeat = task.get("repeat", {})
    if repeat.get("type") != "interval":
        print("# create_interval_events: передан не интервальный repeat")
        return []

    interval_min = repeat.get("interval_minutes", 5)
    if interval_min < MIN_INTERVAL_MINUTES:
        print(f"# Интервал {interval_min} мин меньше минимального ({MIN_INTERVAL_MINUTES} мин). Установлен {MIN_INTERVAL_MINUTES} мин.")
        interval_min = MIN_INTERVAL_MINUTES

    until_str = repeat.get("until", "").strip()
    if not until_str:
        print("# Для эмуляции интервала обязательно указывать время окончания (until).")
        return []

    # Парсим until (ожидается 'YYYY-MM-DDTHH:MM:SSZ')
    try:
        until_clean = until_str.replace("Z", "").replace("+03:00", "")
        end_dt = datetime.strptime(until_clean, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        print(f"# Не удалось разобрать until: {until_str}")
        return []

    # Парсим start задачи
    start_str = f"{task['date']} {task['time']}"
    try:
        start_dt = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
    except ValueError:
        print(f"# Не удалось разобрать start: {start_str}")
        return []

    if end_dt <= start_dt:
        print(f"# Время окончания ({until_str}) раньше или совпадает с началом ({start_str}). События не созданы.")
        return []

    # Считаем количество событий
    delta = end_dt - start_dt
    total_minutes = int(delta.total_seconds() // 60)
    count = total_minutes // interval_min
    if count > MAX_INTERVAL_EVENTS:
        print(f"# Слишком много событий ({count}). Ограничено до {MAX_INTERVAL_EVENTS}.")
        count = MAX_INTERVAL_EVENTS

    if count == 0:
        print("# Интервал больше оставшегося времени. Ничего не создано.")
        return []

    print(f"# Эмуляция интервала: каждые {interval_min} мин, всего событий: {count}")
    uids = []
    for i in range(count):
        event_start = start_dt + timedelta(minutes=i * interval_min)
        # Проверка: не вышли за until
        if event_start >= end_dt:
            break

        single_task = {
            "date": event_start.strftime("%Y-%m-%d"),
            "time": event_start.strftime("%H:%M"),
            "title": task.get("title", "Интервал"),
            "duration": task.get("duration", 5),
            "place": task.get("place", ""),
            "description": task.get("description", ""),
            "slot": task.get("slot", ""),
            "repeat": {"type": "none"}
        }

        uid = create_event(single_task)
        if uid:
            uids.append(uid)
            print(f"  [{i+1}/{count}] {uid}")
            time.sleep(SAFE_DELAY_SEC)
        else:
            print(f"  [{i+1}/{count}] ОШИБКА – остановка")
            break

    print(f"# Эмуляция завершена. Создано: {len(uids)} из {count}")
    return uids


# ---------- УДАЛЕНИЕ СОБЫТИЯ ----------
def delete_event(uid, calendar_url=None):
    if not calendar_url:
        calendar_url = get_calendar_url()
    if not calendar_url or not uid:
        return False
    ok, result = _call_mcp("delete-event", {"uid": uid, "calendarUrl": calendar_url}, timeout=15)
    return ok