
import json
import sys
import os
import time

# Пути из voice_config
from voice_config import BASE_DIR, RAW_FILE as TASKS_FILE, READY_FILE

BACKUP_FILE = os.path.join(BASE_DIR, "raw_tasks_backup.json")




# ==================== ВНУТРЕННИЕ ФУНКЦИИ ====================

def _load_tasks():
    tasks = []
    try:
        if os.path.exists(TASKS_FILE):
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
        if not tasks:
            return _restore_from_backup()
        return tasks
    except (json.JSONDecodeError, IOError):
        return _restore_from_backup()

def _save_tasks(tasks):
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    _backup_tasks(tasks)

def _backup_tasks(tasks=None):
    if tasks is None:
        tasks = _load_tasks()
    with open(BACKUP_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)

def _restore_from_backup():
    if os.path.exists(BACKUP_FILE):
        try:
            with open(BACKUP_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
                print("⚠️ Восстановлены задачи из резервной копии.")
                return tasks
        except (json.JSONDecodeError, IOError):
            print("❌ Резервная копия повреждена.")
    print("❌ Нет задач ни в основном файле, ни в резервной копии.")
    return []

def _load_ready_tasks():
    if not os.path.exists(READY_FILE):
        return []
    try:
        with open(READY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def add_ready_task(task_data):
    """Добавляет задачу в ready_tasks.json"""
    ready_file = "ready_tasks.json"
    if os.path.exists(ready_file):
        with open(ready_file, "r", encoding="utf-8") as f:
            tasks = json.load(f)
    else:
        tasks = []
    tasks.append(task_data)
    with open(ready_file, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    print(f"✅ Задача добавлена в готовые: {task_data['text'][:50]}...")
# ==================== ОСНОВНЫЕ ФУНКЦИИ (API) ====================

def add_raw_task(text, category):
    tasks = _load_tasks()
    tasks.append({
        "text": text,
        "category": category,
        "created_at": time.time()
    })
    _save_tasks(tasks)
    print(f"✅ Задача добавлена: {text} → {category}")

def get_raw_tasks():
    return _load_tasks()

def remove_raw_task(index):
    tasks = _load_tasks()
    if 0 <= index < len(tasks):
        removed = tasks.pop(index)
        _save_tasks(tasks)
        print(f"🗑️ Удалена задача: {removed['text']}")
        return True
    else:
        print("❌ Неверный индекс")
        return False

def clear_raw_tasks():
    _save_tasks([])
    print("🧹 Все сырые задачи удалены")

def update_raw_task_details(task_id, details_dict):
    tasks = _load_tasks()
    if 0 <= task_id < len(tasks):
        if "details" not in tasks[task_id]:
            tasks[task_id]["details"] = {}
        tasks[task_id]["details"].update(details_dict)
        _save_tasks(tasks)
        print(f"📝 Частичные ответы сохранены для задачи #{task_id}")
        return True
    else:
        print(f"❌ Неверный индекс задачи: {task_id}")
        return False

def add_ready_task(task_data):
    """Добавляет задачу в ready_tasks.json"""
    ready_tasks = _load_ready_tasks()
    ready_tasks.append(task_data)
    _save_ready_tasks(ready_tasks)
    print(f"✅ Задача добавлена в готовые: {task_data['text'][:50]}...")

def move_to_ready(task_id, ready_task_data=None):
    tasks = _load_tasks()
    if 0 <= task_id < len(tasks):
        removed = tasks.pop(task_id)
        _save_tasks(tasks)
        print(f"🗑️ Задача '{removed['text']}' удалена из сырых (перенесена в готовые)")
        return removed
    else:
        print(f"❌ Неверный индекс задачи: {task_id}")
        return None

def clear_ready_tasks():
    _save_ready_tasks([])
    print("🧹 Все готовые задачи удалены")

def get_ready_tasks():
    return _load_ready_tasks()

# ==================== ЗАГЛУШКИ ДЛЯ БУДУЩИХ РАСШИРЕНИЙ ====================
def get_priority_task(tasks):
    if not tasks:
        return None
    import random
    return random.choice(tasks)

def sync_to_cloud():
    print("☁️ ЗАГЛУШКА: синхронизация с облаком (не реализовано)")

def archive_task(task):
    print(f"📦 ЗАГЛУШКА: задача '{task.get('text', '')}' отправлена в архив")