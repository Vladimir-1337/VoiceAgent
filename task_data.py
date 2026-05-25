# task_data.py — Блок 1: Работа с ready_tasks.json
# Подблок 1.1: load_tasks() — чтение задач из файла

import os
import json

# Пути из voice_config
from voice_config import READY_FILE as _JSON_PATH, SEEN_FILE as _SEEN_PATH


def load_tasks():
    """
    Загрузка списка задач из ready_tasks.json.
    Возвращает список словарей.
    При отсутствии файла или битом JSON возвращает пустой список [].
    Никогда не кидает исключений наружу.
    """
    # Проверка: есть ли файл вообще
    # Если нет — это норма для первого запуска, тихо возвращаем []
    if not os.path.exists(_JSON_PATH):
        # print("# ready_tasks.json не найден, возвращаю пустой список")  # раскомментировать для отладки
        return []

    # Пытаемся открыть и прочитать JSON
    try:
        with open(_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        # Файл есть, но внутри не JSON (мусор, обрыв записи, ручная правка с ошибкой)
        print("# ОШИБКА: ready_tasks.json повреждён, не является валидным JSON")
        return []
    except Exception as e:
        # Любая другая ошибка ввода-вывода (нет прав, диск отвалился)
        print(f"# ОШИБКА чтения ready_tasks.json: {e}")
        return []

    # Проверка: содержимое — это список?
    # Если кто-то руками записал туда словарь {} или строку — не наш формат
    if not isinstance(data, list):
        print("# ОШИБКА: ready_tasks.json содержит не список (ожидается массив [])")
        return []

    # Всё хорошо — возвращаем данные как есть
    return data
    





# task_data.py — продолжение
# Подблок 1.2: save_tasks() — запись задач в файл

import tempfile


def save_tasks(tasks):
    """
    Сохранение списка задач в ready_tasks.json.
    Принимает список словарей.
    Возвращает True при успехе, False при ошибке.
    Использует атомарную запись: сначала во временный файл, потом переименование.
    """
    # Проверка: на вход подан именно список
    # Если передали словарь или строку — не пишем, это ошибка вызывающего кода
    if not isinstance(tasks, list):
        print("# ОШИБКА: save_tasks ожидает список, получен", type(tasks).__name__)
        return False

    # Атомарная запись:
    # 1. Пишем во временный файл в той же папке (чтобы переименование было мгновенным)
    # 2. Если запись успешна — заменяем оригинал
    # 3. Если запись оборвалась — оригинал не пострадал
    try:
        # Создаём временный файл рядом с целевым (та же файловая система — rename атомарен)
        dir_path = os.path.dirname(_JSON_PATH)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=dir_path,
            delete=False,
            suffix=".tmp"
        ) as tmp:
            json.dump(tasks, tmp, ensure_ascii=False, indent=2)
            tmp_path = tmp.name

        # Замена оригинального файла временным
        os.replace(tmp_path, _JSON_PATH)
        return True

    except Exception as e:
        # Любая ошибка: нет места на диске, нет прав, файловая система отвалилась
        print(f"# ОШИБКА записи ready_tasks.json: {e}")
        # Подчищаем временный файл, если он остался
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
        return False
        
        
     
        
           
              
 # task_data.py — продолжение
# V.2: cleanup_exported_tasks() — авто-удаление выгруженных задач


def cleanup_exported_tasks():
    """
    Удаляет из ready_tasks.json задачи, которые уже выгружены
    и время события которых прошло.
    
    Вход:  ready_tasks.json
    Выход: обновлённый ready_tasks.json (без отработанных задач)
    
    Возвращает количество удалённых задач.
    """
    from datetime import datetime
    
    tasks = load_tasks()
    if not tasks:
        return 0
    
    now = datetime.now()
    remaining = []
    removed = 0
    
    for task in tasks:
        # Пропускаем невыгруженные задачи
        if not task.get("exported", False):
            remaining.append(task)
            continue
        
        # Собираем время события из date + time
        date_str = task.get("date", "")
        time_str = task.get("time", "")
        
        if not date_str or not time_str:
            # Нет даты/времени — оставляем (не должны сюда попасть, но на всякий случай)
            remaining.append(task)
            continue
        
        try:
            event_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            # Кривой формат — оставляем
            remaining.append(task)
            continue
        
        # Если время события прошло — удаляем
        if event_dt <= now:
            removed += 1
        else:
            remaining.append(task)
    
    if removed > 0:
        save_tasks(remaining)
        print(f"🧹 Авто-очистка: удалено {removed} отработанных задач.")
    
    return removed   
        
        
        
        
        
        
        


# task_data.py — продолжение
# OV.1: Кеш обработанных аудиофайлов

import os
import json


def load_seen_cache():
    """
    Загружает кеш обработанных файлов: {имя_файла: (дата_создания, размер)}.
    Если файла нет — возвращает пустой словарь.
    """
    if not os.path.exists(_SEEN_PATH):
        return {}
    try:
        with open(_SEEN_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except:
        return {}


def save_seen_cache(cache):
    """
    Сохраняет кеш обработанных файлов в seen_files.json.
    """
    try:
        with open(_SEEN_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


# task_data.py — продолжение
# OV.2: Проверка, является ли файл новым


def is_new_file(filepath):
    """
    Проверяет, является ли файл новым (ещё не обработанным).
    
    Вход:  путь к файлу
    Выход: True — файл новый, нужно обработать
           False — файл уже был обработан или не изменился
    
    Сравнивает имя, дату создания и размер с кешем.
    """
    cache = load_seen_cache()
    filename = os.path.basename(filepath)
    
    # Если файла нет в кеше — он новый
    if filename not in cache:
        return True
    
    # Если файл есть в кеше — сравниваем дату и размер
    try:
        stat = os.stat(filepath)
        current_mtime = int(stat.st_mtime)  # дата последнего изменения
        current_size = stat.st_size         # размер в байтах
    except OSError:
        # Не удалось прочитать — считаем новым (на всякий случай)
        return True
    
    cached_mtime, cached_size = cache[filename]
    
    # Если дата или размер изменились — это новый файл
    if current_mtime != cached_mtime or current_size != cached_size:
        return True
    
    # Всё совпадает — файл уже обработан
    return False


def mark_file_seen(filepath):
    """
    Помечает файл как обработанный (сохраняет в кеш).
    
    Вход:  путь к файлу
    Выход: True/False — успешно ли сохранено
    """
    cache = load_seen_cache()
    filename = os.path.basename(filepath)
    
    try:
        stat = os.stat(filepath)
        cache[filename] = [int(stat.st_mtime), stat.st_size]
        save_seen_cache(cache)
        return True
    except OSError:
        return False


        
# task_data.py — продолжение
# Подблок 1.3: validate_task() — проверка одной задачи

from datetime import datetime

# Пытаемся импортировать STOP_VERBS из intent_parser
try:
    from intent_parser import STOP_VERBS
except ImportError:
    STOP_VERBS = []   # если модуль недоступен — проверка только по окончаниям


# Подблок 1.3: validate_task() — проверка одной задачи

from datetime import datetime

try:
    from intent_parser import STOP_VERBS
except ImportError:
    STOP_VERBS = []


def validate_task(task):
    """
    Проверяет словарь задачи на соответствие ТЗ.
    Возвращает список ошибок (пустой список = задача валидна).
    Никогда не кидает исключений.
    """
    errors = []

    if not isinstance(task, dict):
        return ["Задача должна быть словарём"]

    # --- date: строка ГГГГ-ММ-ДД, реальная дата ---
    date = task.get("date")
    if not date or not isinstance(date, str):
        errors.append("Поле 'date' обязательно и должно быть строкой ГГГГ-ММ-ДД")
    else:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            errors.append(f"Поле 'date' не является реальной датой: {date}")

    # --- time: строка ЧЧ:ММ, 00-23:00-59 ---
    time = task.get("time")
    if not time or not isinstance(time, str):
        errors.append("Поле 'time' обязательно и должно быть строкой ЧЧ:ММ")
    else:
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            errors.append(f"Поле 'time' не является реальным временем: {time}")

    # --- title: непустая строка + должно содержать действие ---
    title = task.get("title", "").strip()
    if not title:
        errors.append("Поле 'title' обязательно и не может быть пустым")
    else:
        has_verb = False
        words = title.split()
        for word in words:
            clean = word.strip(",.!?;:«»\"'()[]").lower()
            if not clean:
                continue
            if clean in STOP_VERBS:
                has_verb = True
                break
            if clean.endswith(("ть", "ти", "чь", "тся", "ться", "и", "й")):
                if clean.endswith(("и", "й")) and len(clean) <= 4:
                    has_verb = True
                    break
                if clean.endswith(("ть", "ти", "чь", "тся", "ться")):
                    has_verb = True
                    break
        if not has_verb:
            errors.append("Поле 'title' должно содержать конкретное действие (глагол), например: купить, позвонить, сделать")

    # --- duration: целое >= 1 ---
    duration = task.get("duration", 5)
    if not isinstance(duration, int) or duration < 1:
        errors.append(f"Поле 'duration' должно быть целым числом >= 1, получено: {duration}")

    # --- repeat: объект с type ---
    repeat = task.get("repeat")
    if not isinstance(repeat, dict):
        errors.append("Поле 'repeat' обязательно и должно быть словарём")
    else:
        rtype = repeat.get("type")
        allowed_types = ["none", "daily", "weekly", "interval"]
        if rtype not in allowed_types:
            errors.append(f"repeat.type должен быть одним из {allowed_types}, получено: {rtype}")

        days = repeat.get("days", [])
        if rtype == "weekly":
            if not isinstance(days, list) or len(days) == 0:
                errors.append("repeat.days обязателен для weekly (список чисел 1-7)")
            else:
                for d in days:
                    if not isinstance(d, int) or d < 1 or d > 7:
                        errors.append(f"repeat.days содержит недопустимое значение: {d} (должно быть 1-7)")

        interval = repeat.get("interval_minutes", 0)
        if rtype == "interval":
            if not isinstance(interval, int) or interval < 1:
                errors.append(f"repeat.interval_minutes обязателен для interval и должен быть > 0, получено: {interval}")

    # --- exported: булево ---
    exported = task.get("exported", False)
    if not isinstance(exported, bool):
        errors.append(f"Поле 'exported' должно быть true или false, получено: {exported}")

    # --- caldav_uid: строка (может быть пустой) ---
    uid = task.get("caldav_uid", "")
    if not isinstance(uid, str):
        errors.append(f"Поле 'caldav_uid' должно быть строкой, получено: {type(uid).__name__}")

    # --- place, description, slot: строки (могут быть пустыми) ---
    for field in ["place", "description", "slot"]:
        val = task.get(field, "")
        if not isinstance(val, str):
            errors.append(f"Поле '{field}' должно быть строкой, получено: {type(val).__name__}")

    # --- third_party: строка (опционально) ---
    third_party = task.get("third_party", "")
    if not isinstance(third_party, str):
        errors.append(f"Поле 'third_party' должно быть строкой, получено: {type(third_party).__name__}")

    # --- invite: булево (опционально, только если есть third_party) ---
    invite = task.get("invite", False)
    if not isinstance(invite, bool):
        errors.append(f"Поле 'invite' должно быть true или false, получено: {invite}")

    if invite and not third_party.strip():
        errors.append("Поле 'invite' не может быть true без указания 'third_party'")

    # --- last_edited: строка (опционально) ---
    last_edited = task.get("last_edited", "")
    if not isinstance(last_edited, str):
        errors.append(f"Поле 'last_edited' должно быть строкой, получено: {type(last_edited).__name__}")

    return errors
    
    