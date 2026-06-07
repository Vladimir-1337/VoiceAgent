
# main.py — Главный цикл Органайзера (MVP)
# Автоматический мониторинг папки Recordings, сортировка задач, меню.

import sys
import os
import time
import glob
import threading

import json
import io
import contextlib
NULL_OUT = io.StringIO()

# --- Чтение версии из файла ---
def get_version():
    try:
        with open("/storage/emulated/0/VoiceAgent/version.txt", "r") as f:
            return f.read().strip()
    except:
        return "?.?.?"

# --- Импорты (с защитой от отсутствия) ---
try:
    from voice_sender import send_latest_recording
except ImportError:
    send_latest_recording = None

try:
    from voice_cleaner import delete_latest_recording
except ImportError:
    delete_latest_recording = None

try:
    from intent_parser import parse_intent
except ImportError:
    parse_intent = None

try:
    from task_data import load_tasks, save_tasks
except ImportError:
    load_tasks = None
    save_tasks = None

try:
    from task_storage import add_raw_task
except ImportError:
    add_raw_task = None

try:
    from caldav_client import create_event
except ImportError:
    create_event = None

from mode_3 import run_mode_3
from profile import edit_profile

# --- Константы (из voice_config) ---
from voice_config import RECORDINGS_DIR, READY_FILE, RAW_FILE

# --- Глобальный флаг мониторинга ---
monitor_running = True


# ======================================================================
# ОЧИСТКА ЭКРАНА
# ======================================================================
def clear_screen():
    print("\n" * 50)


# ======================================================================
# ШАПКА
# ======================================================================
def print_header(section):
    print("=" * 50)
    print(f"  ОРГАНАЙЗЕР v{get_version()} > {section}")
    print("=" * 50)


# ======================================================================
# ОБРАБОТКА НОВЫХ ФАЙЛОВ
# ======================================================================
def process_new_files():
    """Обрабатывает новые аудиофайлы. Возвращает список результатов."""
    if not os.path.exists(RECORDINGS_DIR):
        return []

    all_files = glob.glob(os.path.join(RECORDINGS_DIR, "*.m4a"))
    if not all_files:
        return []

    results = []
    processed = 0
    MAX_PER_CYCLE = 5

    from ai_normalizer import ai_normalize
    from ai_distributor import distribute, merge_task
    from split_tasks import split_tasks
    from datetime import datetime
    from task_data import cleanup_exported_tasks, is_new_file, mark_file_seen

    for filepath in all_files:
        if processed >= MAX_PER_CYCLE:
            break

        filename = os.path.basename(filepath)

        if not is_new_file(filepath):
            continue

        file_result = {
            "filename": filename,
            "text": "",
            "tasks": [],
            "errors": []
        }

        text = None
        if send_latest_recording:
            text, error = send_latest_recording()
            if error:
                if "длинная" in error.lower() or "длитель" in error.lower():
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass
                    mark_file_seen(filepath)
                    file_result["errors"].append(f"Слишком длинная запись: {error}")
                    results.append(file_result)
                    continue
                file_result["errors"].append(error)
                results.append(file_result)
                continue
        else:
            text = filename.replace(".m4a", "").replace("_", " ")

        if not text or not text.strip():
            try:
                os.remove(filepath)
            except OSError:
                pass
            file_result["errors"].append("Пустой текст после распознавания")
            results.append(file_result)
            continue

        file_result["text"] = text

        task_texts = split_tasks(text)

        for single_task_text in task_texts:
            if not single_task_text or not single_task_text.strip():
                continue

            clean_task_text = ai_normalize(single_task_text)

            task_result = {
                "title": clean_task_text[:80],
                "status": "неизвестно",
                "calendar_uid": None
            }

            if not parse_intent:
                if add_raw_task:
                    add_raw_task(clean_task_text, "не категоризировано")
                task_result["status"] = "📥 В сырых"
                file_result["tasks"].append(task_result)
                processed += 1
                continue

            intent = parse_intent(clean_task_text)

            if intent is None:
                if add_raw_task:
                    add_raw_task(clean_task_text, "не категоризировано")
                task_result["status"] = "📥 В сырых"
                file_result["tasks"].append(task_result)
                processed += 1
                continue

            remainder = intent.get("title", "")
            items = intent.get("items", [])
            distributed = distribute(remainder)
            task = merge_task(intent, distributed, items)
            task["last_edited"] = ""

            has_remind = intent.get("has_remind", False)
            is_valid = intent.get("is_valid", False)

            if has_remind and is_valid:
                if load_tasks and save_tasks:
                    tasks = load_tasks()
                    tasks.append(task)
                    save_tasks(tasks)
                if create_event:
                    uid = create_event(task)
                    if uid:
                        task["caldav_uid"] = uid
                        task["exported"] = True
                        task["exported_at"] = datetime.now().isoformat()
                        task_result["calendar_uid"] = uid
                        if load_tasks and save_tasks:
                            tasks = load_tasks()
                            for t in tasks:
                                if t.get("title") == task["title"] and t.get("date") == task["date"]:
                                    t["caldav_uid"] = uid
                                    t["exported"] = True
                                    t["exported_at"] = datetime.now().isoformat()
                            save_tasks(tasks)
                task_result["status"] = "📅 В календаре"
            elif not has_remind and is_valid:
                if load_tasks and save_tasks:
                    tasks = load_tasks()
                    tasks.append(task)
                    save_tasks(tasks)
                task_result["status"] = "📋 На подтверждении"
            else:
                if add_raw_task:
                    add_raw_task(clean_task_text, "не категоризировано")
                task_result["status"] = "📥 В сырых"

            file_result["tasks"].append(task_result)
            processed += 1

        mark_file_seen(filepath)
        try:
            os.remove(filepath)
        except OSError:
            pass

        results.append(file_result)

    return results


# ======================================================================
# ГЛАВНОЕ МЕНЮ
# ======================================================================
def main_menu():
    """Главное меню. 0 = выход, 5 = мониторинг."""
    global monitor_running

    while True:
        clear_screen()
        print_header("Главное меню")
        print("  1. 📥 Сырые задачи")
        print("  2. 📋 Готовые задачи")
        print("  3. 👤 Профиль")
        print("  4. 🗑️ Очистить всё")
        print("  5. 📡 Мониторинг")
        print("  0. Выход")
        print("=" * 50)

        choice = input("> ").strip()

        if choice == "0":
            monitor_running = False
            print("До свидания!")
            break

        elif choice == "1":
            clear_screen()
            print_header("Сырые задачи")
            raw_path = "/storage/emulated/0/VoiceAgent/raw_tasks.json"
            if os.path.exists(raw_path):
                with open(raw_path, "r", encoding="utf-8") as f:
                    raw_tasks = json.load(f)
                if raw_tasks:
                    for i, task in enumerate(raw_tasks, 1):
                        print(f"  {i}. {task.get('title', '—')[:80]}")
                        print(f"     Статус: {task.get('status', '—')}")
                        print()
                else:
                    print("  📭 Сырых задач нет.")
            else:
                print("  📭 Сырых задач нет.")
            print("\n  Нажмите Enter...")
            input()

        elif choice == "2":
            clear_screen()
            print_header("Готовые задачи")
            ready_path = "/storage/emulated/0/VoiceAgent/ready_tasks.json"
            if os.path.exists(ready_path):
                with open(ready_path, "r", encoding="utf-8") as f:
                    ready_tasks = json.load(f)
                if ready_tasks:
                    for i, task in enumerate(ready_tasks, 1):
                        print(f"  {i}. {task.get('title', '—')[:80]}")
                        print(f"     Статус: {task.get('status', '—')}")
                        if task.get('date'):
                            print(f"     Дата: {task['date']}")
                        print()
                else:
                    print("  📭 Готовых задач нет.")
            else:
                print("  📭 Готовых задач нет.")
            print("\n  Нажмите Enter...")
            input()

        elif choice == "3":
            from profile import edit_profile
            edit_profile()

        elif choice == "4":
            clear_screen()
            print_header("Очистка данных")
            print("  ВНИМАНИЕ: будет удалено ВСЁ, включая:")
            print("    📋 Все готовые задачи (ready_tasks.json)")
            print("    📥 Все сырые задачи (raw_tasks.json)")
            print("    👤 Профиль: город, места, люди, работа")
            print("    📍 Якорные места: адреса из профиля")
            print("    👥 Якорные люди: контакты из профиля")
            print("    📊 Лог мониторинга (monitor.log)")
            print("    📅 События из Яндекс.Календаря")
            print("    📁 Все временные и служебные файлы")
            print("  ⚠️ Аудиозаписи HE удаляются.")
            print("-" * 50)
            print("  1 = Да, удалить всё")
            print("  0 = Нет, отмена")
            confirm = input("> ").strip()

            if confirm == "1":
                try:
                    from task_data import load_tasks
                    from caldav_client import delete_event
                    tasks = load_tasks()
                    for t in tasks:
                        uid = t.get("caldav_uid", "")
                        if uid:
                            delete_event(uid)
                except ImportError:
                    pass

                for fname in ["ready_tasks.json", "raw_tasks.json", "progress.json",
                              "feedback.json", "raw_tasks_backup.json",
                              "current_analysis.json", "dialog_progress.json",
                              "seen_files.json", "monitor.log"]:
                    fpath = os.path.join("/storage/emulated/0/VoiceAgent", fname)
                    if os.path.exists(fpath):
                        os.remove(fpath)

                profile_path = "/storage/emulated/0/VoiceAgent/user_profile.json"
                empty_profile = {
                    "city": "", "places": [], "people": [],
                    "anchors": {}, "people_anchors": {}, "work": ""
                }
                with open(profile_path, "w", encoding="utf-8") as f:
                    json.dump(empty_profile, f, indent=2)

                print("  ✅ ВСЕ данные удалены, включая якоря.")
                print("  🎙️ Аудиозаписи сохранены.")
            else:
                print("  ❌ Очистка отменена.")
            print("\n  Нажмите Enter...")
            input()

        elif choice == "5":
            import time as _time
            log_file = "/storage/emulated/0/VoiceAgent/monitor.log"
            last_size = 0
            task_index = -1
            all_tasks = []

            clear_screen()
            print_header("Мониторинг · Реальное время")
            print("  ✅ Мониторинг активен")
            print("  🔄 Обновление каждые 3 сек")
            print("-" * 50)
            print("  ◄ 1 / 2 ►  — переключение между задачами")
            print("  📝 0 — пожаловаться на выбранную задачу")
            print("  🗑️ 3 — очистить лог")
            print("  ℹ️  Enter — выход")
            print("-" * 50)

            import select
            import sys as _sys

            while True:
                if _sys.stdin in select.select([_sys.stdin], [], [], 0)[0]:
                    key = _sys.stdin.readline().strip()

                    if key == "":
                        break

                    elif key == "1" and all_tasks:
                        task_index = max(0, task_index - 1)
                        _show_task_detail(all_tasks, task_index, log_file)

                    elif key == "2" and all_tasks:
                        task_index = min(len(all_tasks) - 1, task_index + 1)
                        _show_task_detail(all_tasks, task_index, log_file)

                    elif key == "3":
                        if os.path.exists(log_file):
                            with open(log_file, "w") as f:
                                f.write("")
                            last_size = 0
                            all_tasks = []
                            task_index = -1
                        print("\n  🗑️ Лог очищен!")
                        print("  Нажмите Enter...")
                        input()
                        clear_screen()
                        print_header("Мониторинг · Реальное время")
                        print("  ✅ Мониторинг активен")
                        print("  🔄 Обновление каждые 3 сек")
                        print("-" * 50)
                        print("  ◄ 1 / 2 ►  — переключение между задачами")
                        print("  📝 0 — пожаловаться на выбранную задачу")
                        print("  🗑️ 3 — очистить лог")
                        print("  ℹ️  Enter — выход")
                        print("-" * 50)

                    elif key == "0":
                        clear_screen()
                        print_header("Жалоба на задачу")

                        if all_tasks and task_index >= 0:
                            print(f"  📋 Задача: {all_tasks[task_index]['title'][:60]}")
                            print(f"  📊 Статус: {all_tasks[task_index].get('status', '—')}")
                            print("-" * 50)
                            print("  Проблема в ЭТОЙ задаче?")
                            print("    1 — Да, проблема в этой задаче")
                            print("    2 — Нет, проблема в другой задаче")
                            print("    0 — Отмена")
                            confirm = input("  > ").strip()

                            if confirm == "1":
                                _report_problem(all_tasks, task_index, log_file)
                            elif confirm == "2":
                                print("\n  Используйте кнопки 1/2 для выбора другой задачи.")
                        else:
                            print("  ⚠️ Нет задач для выбора.")
                            print("  Отправить общую жалобу?")
                            print("    1 — Да")
                            print("    0 — Отмена")
                            confirm = input("  > ").strip()
                            if confirm == "1":
                                _report_problem([], -1, log_file)

                        print("\n  Нажмите Enter...")
                        input()
                        clear_screen()
                        print_header("Мониторинг · Реальное время")
                        print("  ✅ Мониторинг активен")
                        print("  🔄 Обновление каждые 3 сек")
                        print("-" * 50)
                        print("  ◄ 1 / 2 ►  — переключение между задачами")
                        print("  📝 0 — пожаловаться на выбранную задачу")
                        print("  🗑️ 3 — очистить лог")
                        print("  ℹ️  Enter — выход")
                        print("-" * 50)

                current_size = os.path.getsize(log_file) if os.path.exists(log_file) else 0

                if current_size > last_size:
                    try:
                        with open(log_file, "r", encoding="utf-8") as f:
                            log_lines = f.readlines()

                        all_tasks = _extract_tasks_from_log(log_lines)

                        if all_tasks and task_index == -1:
                            task_index = len(all_tasks) - 1

                        recent = log_lines[-15:] if len(log_lines) > 15 else log_lines

                        print("\n" * 2)
                        print("-" * 50)
                        print(f"  📋 ЛОГ · {len(log_lines)} записей всего · Задач: {len(all_tasks)}")
                        print("-" * 50)

                        has_recent = False
                        for line in recent:
                            stripped = line.rstrip()
                            if stripped:
                                has_recent = True
                                if "Обработано:" in stripped or "Итого:" in stripped:
                                    print(f"  📊 {stripped}")
                                elif "ОШИБКА" in stripped or "ошибка" in stripped.lower() or "500" in stripped:
                                    print(f"  ❌ {stripped}")
                                elif "мониторинг запущен" in stripped.lower():
                                    print(f"  🟢 {stripped}")
                                elif "календарь" in stripped.lower():
                                    print(f"  📅 {stripped}")
                                elif "удалён" in stripped.lower():
                                    print(f"  🗑️ {stripped}")
                                else:
                                    print(f"  📋 {stripped}")

                        if not has_recent:
                            pass

                        print("-" * 50)
                        if all_tasks and task_index >= 0:
                            print(f"  📌 Задача {task_index+1}/{len(all_tasks)}: {all_tasks[task_index]['title'][:50]}")
                        print("  ◄ 1 / 2 ►  |  0 — пожаловаться  |  3 — очистить лог  |  Enter — выход")

                    except:
                        pass
                    last_size = current_size
                else:
                    pass

                _time.sleep(3)

        else:
            print("  ❌ Неверный выбор.")
            print("  Нажмите Enter...")
            input()


# ======================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ МОНИТОРИНГА
# ======================================================================

def _extract_tasks_from_log(lines):
    """Извлекает задачи из строк лога."""
    tasks = []
    current_task = None
    
    for line in lines:
        stripped = line.rstrip()
        
        if "НОВЫЙ ЦИКЛ" in stripped:
            if current_task:
                tasks.append(current_task)
            current_task = {"title": "", "status": "", "place": "", "error": "", "raw": []}
            current_task["raw"].append(stripped)
        
        elif current_task is not None:
            current_task["raw"].append(stripped)
            
            if "🎤 Распознано:" in stripped:
                text = stripped.split("«")[-1].replace("»", "").strip()
                current_task["title"] = text[:80]
            
            elif "📝 Задача:" in stripped:
                if not current_task["title"]:
                    text = stripped.split("«")[-1].replace("»", "").strip()
                    current_task["title"] = text[:80]
            
            elif "В календарь" in stripped or "✅ Событие создано" in stripped:
                current_task["status"] = "📅 В календаре"
            
            elif "На подтверждение" in stripped:
                current_task["status"] = "📋 На подтверждении"
            
            elif "В сырые" in stripped:
                current_task["status"] = "📥 В сырых"
            
            elif "❌ Ошибка VPS" in stripped or "500" in stripped:
                current_task["error"] = stripped[:100]
                current_task["status"] = "❌ Ошибка сервера"
            
            elif "SCAN_PLACE" in stripped and "✅" in stripped:
                # Извлекаем адрес из лога place
                if "place:" not in current_task["place"]:
                    current_task["place"] = stripped[-80:]
    
    if current_task:
        tasks.append(current_task)
    
    return tasks





def _show_task_detail(tasks, index, log_file):
    """Показывает детали выбранной задачи."""
    if not tasks or index >= len(tasks):
        return
    
    task = tasks[index]
    clear_screen()
    print_header(f"Задача {index+1}/{len(tasks)}")
    print(f"  📝 Название: {task.get('title', '—')}")
    print(f"  📊 Статус: {task.get('status', '—')}")
    if task.get('place'):
        print(f"  📍 Место: {task['place']}")
    if task.get('error'):
        print(f"  ❌ Ошибка: {task['error']}")
    print("-" * 50)
    print("  📋 Сырые строки лога:")
    for raw_line in task.get("raw", [])[-10:]:
        print(f"     {raw_line[:100]}")
    print("-" * 50)
    print("  ◄ 1 / 2 ►  |  0 — пожаловаться  |  Enter — назад")


def _report_problem(tasks, index, log_file):
    """Формирует жалобу и silently отправляет через VPS (до 5 попыток).
    Работает даже если задач нет (пустой лог / лог очищен)."""
    from datetime import datetime

    # Безопасно получаем задачу (или заглушку если задач нет)
    if tasks and index >= 0 and index < len(tasks):
        task = tasks[index]
    else:
        task = {"title": "задача не выбрана", "status": "—"}

    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    print("\n  📝 Опишите проблему (Enter — пустая строка для отправки):")

    # Многострочный ввод
    comment_lines = []
    while True:
        line = input()
        if line == "":
            break
        comment_lines.append(line)

    comment = "\n".join(comment_lines) if comment_lines else "(без комментария)"

    print("  ⏳ Отправляю...", end="", flush=True)

    report_lines = []
    report_lines.append(f"=== ОТЧЁТ О ПРОБЛЕМЕ ===")
    report_lines.append(f"Дата: {timestamp}")
    report_lines.append(f"Комментарий: {comment}")
    report_lines.append(f"Задача: {task.get('title', '—')}")
    report_lines.append(f"Статус: {task.get('status', '—')}")
    if task.get('error'):
        report_lines.append(f"Ошибка: {task['error']}")
    report_lines.append("")
    report_lines.append(f"Всего задач в логе: {len(tasks) if tasks else 0}")
    report_lines.append("")

    # Системная информация
    report_lines.append("--- СИСТЕМНАЯ ИНФОРМАЦИЯ ---")
    try:
        import subprocess
        model = subprocess.check_output(["getprop", "ro.product.model"], timeout=3).decode().strip()
        android = subprocess.check_output(["getprop", "ro.build.version.release"], timeout=3).decode().strip()
        report_lines.append(f"Модель: {model}")
        report_lines.append(f"Android: {android}")
    except:
        report_lines.append("Модель: неизвестно")
        report_lines.append("Android: неизвестно")
    try:
        import sys
        report_lines.append(f"Python: {sys.version.split()[0]}")
    except:
        pass
    try:
        with open("/storage/emulated/0/VoiceAgent/version.txt", "r") as f:
            report_lines.append(f"Версия: {f.read().strip()}")
    except:
        pass
    report_lines.append("")

    # Последние записи лога
    report_lines.append("--- ПОСЛЕДНИЕ ЗАПИСИ ЛОГА ---")
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.readlines()
        if log_content:
            report_lines.extend(log_content[-30:])
        else:
            report_lines.append("(лог пуст)")
    else:
        report_lines.append("(файл лога не существует)")

    report_text = "\n".join(report_lines)

    # Сохраняем локально
    report_file = "/storage/emulated/0/VoiceAgent/user_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_text)

    # Пытаемся отправить до 5 раз
    sent = False
    for attempt in range(5):
        try:
            import requests
            r = requests.post("http://157.22.202.232:8200/report",
                            data=report_text.encode("utf-8"),
                            timeout=5)
            if r.status_code == 200:
                sent = True
                break
        except:
            pass
        time.sleep(1)

    if sent:
        print("\r  ✅ Отправлено!                              ")
    else:
        print("\r  📎 Сохранено локально (сервер недоступен)   ")

    print(f"  📁 user_report.txt")





# ======================================================================
# ФОНОВЫЙ МОНИТОРИНГ
# ======================================================================
def background_monitor():
    """Фоновый мониторинг: обрабатывает аудио и пишет результаты в лог.
    ВЕСЬ вывод process_new_files() глушится в /dev/null — чистая консоль."""
    log_file = "/storage/emulated/0/VoiceAgent/monitor.log"
    cycle_count = 0

    from datetime import datetime

    # Пишем старт только один раз (если лог пустой)
    try:
        if not os.path.exists(log_file) or os.path.getsize(log_file) == 0:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] 🟢 Фоновый мониторинг запущен\n")
    except:
        pass

    while monitor_running:
        try:
            # ГЛУШИМ ВЕСЬ ВЫВОД process_new_files() В /dev/null
            with open(os.devnull, 'w') as devnull:
                with contextlib.redirect_stdout(devnull):
                    results = process_new_files()

            if results:
                timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n{'─' * 50}\n")
                    f.write(f"[{timestamp}] 📁 НОВЫЙ ЦИКЛ — {len(results)} файл(ов)\n")
                    f.write(f"{'─' * 50}\n")

                    for file_result in results:
                        f.write(f"\n  🎙️ Файл: {file_result['filename']}\n")

                        if file_result.get("errors"):
                            for err in file_result["errors"]:
                                f.write(f"  ❌ Ошибка: {err}\n")

                        if file_result.get("text"):
                            f.write(f"  🎤 Распознано: «{file_result['text']}»\n")

                        for task in file_result.get("tasks", []):
                            f.write(f"\n  📝 Задача: «{task['title']}»\n")
                            f.write(f"  📊 Статус: {task['status']}\n")
                            if task.get("calendar_uid"):
                                f.write(f"  📅 UID: {task['calendar_uid']}\n")

                    f.write(f"\n{'─' * 50}\n")
                    f.write(f"[{timestamp}] ✅ Итого задач: {sum(len(r.get('tasks', [])) for r in results)}\n")
                    f.write(f"{'─' * 50}\n\n")

                # Очистка старых записей (каждые 10 циклов)
                cycle_count += 1
                if cycle_count >= 10:
                    cycle_count = 0
                    try:
                        with open(log_file, "r", encoding="utf-8") as f:
                            all_lines = f.readlines()
                        if len(all_lines) > 500:
                            with open(log_file, "w", encoding="utf-8") as f:
                                f.writelines(all_lines[-500:])
                    except:
                        pass

        except Exception as e:
            try:
                timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] ⚠️ Ошибка монитора: {e}\n")
            except:
                pass

        time.sleep(3)




def bridge_all_recorders():
    """
    Универсальный мост: копирует аудио из ВСЕХ известных папок диктофонов
    в Recordings. Поддерживает Xiaomi, Samsung, Huawei, Realme, OPPO, Vivo, Pixel.
    Не удаляет оригиналы.
    """
    import shutil as _shutil
    
    # Все известные папки диктофонов на Android
    recorder_dirs = [
        # Xiaomi
        "/storage/emulated/0/MIUI/sound_recorder/",
        "/storage/emulated/0/Recorder/",
        # Samsung
        "/storage/emulated/0/Sounds/",
        "/storage/emulated/0/Voice Recorder/",
        "/storage/emulated/0/ Samsung/Voice Recorder/",
        # Huawei
        "/storage/emulated/0/record/",
        "/storage/emulated/0/Huawei/Recorder/",
        # Realme / OPPO
        "/storage/emulated/0/Music/Recordings/",
        "/storage/emulated/0/ColorOS/Recorder/",
        # Vivo
        "/storage/emulated/0/Vivo/Recorder/",
        # Pixel / Stock Android
        "/storage/emulated/0/DCIM/Voice/",
        "/storage/emulated/0/Music/Sound Records/",
        # Универсальные
        "/storage/emulated/0/Download/",
        "/storage/emulated/0/Recordings/",
    ]
    
    target_dir = "/storage/emulated/0/Recordings/"
    os.makedirs(target_dir, exist_ok=True)
    
    for src_dir in recorder_dirs:
        if not os.path.exists(src_dir) or src_dir == target_dir:
            continue
        try:
            for fname in os.listdir(src_dir):
                if fname.endswith((".m4a", ".mp3", ".aac", ".amr", ".wav", ".ogg", ".wma", ".flac")):
                    src = os.path.join(src_dir, fname)
                    dst = os.path.join(target_dir, fname)
                    if not os.path.exists(dst):
                        _shutil.copy2(src, dst)
        except:
            pass



# ======================================================================
# РЕГИСТРАЦИЯ
# ======================================================================
def get_password():
    password = ""
    while True:
        try:
            import msvcrt
            ch = msvcrt.getch()
        except ImportError:
            return input().strip()
        if ch in (b'\r', b'\n'):
            break
        elif ch == b'\x08':
            if password:
                password = password[:-1]
                print("\b \b", end="", flush=True)
        elif ch == b'\x03':
            return ""
        else:
            try:
                char = ch.decode('utf-8')
                password += char
                print("*", end="", flush=True)
            except:
                pass
    return password


def verify_and_save(login, password):
    import voice_config
    try:
        import requests
        from requests.auth import HTTPBasicAuth
        response = requests.get(
            "https://caldav.yandex.ru/",
            auth=HTTPBasicAuth(login, password),
            timeout=15
        )
        if response.status_code == 200:
            original_login = voice_config.YANDEX_LOGIN
            original_password = voice_config.YANDEX_APP_PASSWORD
            config_path = "/storage/emulated/0/VoiceAgent/config.py"
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace(
                f'YANDEX_LOGIN = "{original_login}"',
                f'YANDEX_LOGIN = "{login}"'
            )
            content = content.replace(
                f'YANDEX_APP_PASSWORD = "{original_password}"',
                f'YANDEX_APP_PASSWORD = "{password}"'
            )
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(content)
            voice_config.YANDEX_LOGIN = login
            voice_config.YANDEX_APP_PASSWORD = password
            return (True, "✅ Доступ подтверждён! Данные сохранены.")
        elif response.status_code == 401:
            return (False, "❌ Неверный логин или пароль приложения.")
        else:
            return (False, f"❌ Ошибка сервера ({response.status_code}).")
    except requests.exceptions.ConnectionError:
        return (False, "❌ Нет интернета.")
    except requests.exceptions.Timeout:
        return (False, "❌ Сервер не отвечает.")
    except Exception as e:
        return (False, f"❌ Ошибка: {str(e)[:60]}")


def check_registration():
    clear_screen()
    print_header("Регистрация")
    print("  Для работы нужен доступ к Яндекс.Календарю.")
    
    print("  Как получить пароль приложения:")
    print("    1. Откройте passport.yandex.ru")
    print("    2. Войдите в свой аккаунт")
    print("    3. Перейдите: Пароли приложений")
    print("    4. Нажмите: Создать пароль")
    print("    5. Выберите: Календарь")
    print("    6. Скопируйте пароль (16 букв)")
    
    print("  Введите свои данные ниже.")
    print("-" * 50)

    login = input("  Логин Яндекс: ").strip()
    if not login:
        print("\n  ❌ Логин не может быть пустым.")
        input("  Нажмите Enter для выхода...")
        return False

    print("  Пароль приложения: ", end="", flush=True)
    password = get_password()
    print()

    if not password:
        print("\n  ❌ Пароль не может быть пустым.")
        input("  Нажмите Enter для выхода...")
        return False

    print("\n  Проверяем...")
    result, message = verify_and_save(login, password)
    print(f"  {message}")

    if result:
        input("\n  Нажмите Enter для продолжения...")
        return True
    else:
        input("\n  Нажмите Enter, чтобы попробовать снова...")
        return check_registration()






def main():
    import time as _time
    import os as _os
    
    clear_screen()
    print_header("Загрузка")
    print("  Проверка системы...")
    print("")

    import voice_config
    LOCAL_VERSION = get_version()
    
    # [1] Папки
    print("  [1] Папки...", end="", flush=True)
    v_ok = _os.path.exists("/storage/emulated/0/VoiceAgent")
    r_ok = _os.path.exists(voice_config.RECORDINGS_DIR)
    if not v_ok:
        _os.makedirs("/storage/emulated/0/VoiceAgent", exist_ok=True)
    if not r_ok:
        _os.makedirs(voice_config.RECORDINGS_DIR, exist_ok=True)
    print(f"\r  ✅ Папки готовы                    ")
    
    # [2] Библиотеки
    print("  [2] Библиотеки...", end="", flush=True)
    try:
        import requests
        print(f"\r  ✅ Библиотеки готовы                ")
    except ImportError:
        print(f"\r  ⏳ Устанавливаю requests...", end="", flush=True)
        import subprocess, sys
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
            import requests
            print(f"\r  ✅ Библиотеки готовы                ")
        except:
            print(f"\r  ⚠️ requests не установлен          ")
    
    # [3] VPS + замер времени
    print("  [3] VPS...", end="", flush=True)
    for attempt in range(5):
        try:
            t_start = _time.time()
            requests.get(voice_config.SERVER_URL.replace("/voice", ""), timeout=3)
            t_elapsed = _time.time() - t_start
            print(f"\r  ✅ VPS отвечает ({t_elapsed:.1f} сек, попытка {attempt+1})   ")
            break
        except:
            if attempt == 4:
                print(f"\r  ⚠️ VPS не отвечает                  ")
            else:
                _time.sleep(1)
    
    # [4] Whisper + замер времени
    print("  [4] Whisper...", end="", flush=True)
    for attempt in range(3):
        try:
            t_start = _time.time()
            r = requests.post(voice_config.SERVER_URL, 
                            files={"file": ("test.m4a", b"", "audio/mp4")},
                            timeout=5)
            t_elapsed = _time.time() - t_start
            if r.status_code in (200, 400):
                print(f"\r  ✅ Whisper отвечает ({t_elapsed:.1f} сек, попытка {attempt+1})   ")
                if t_elapsed > 3:
                    print("  ⚠️ Whisper МЕДЛЕННЫЙ — меню может тормозить")
                break
        except:
            if attempt == 2:
                print(f"\r  ⚠️ Whisper не отвечает               ")
            else:
                _time.sleep(1)
    
    # [5] Интернет + замер времени
    print("  [5] Интернет...", end="", flush=True)
    for attempt in range(5):
        try:
            t_start = _time.time()
            requests.get("https://google.com", timeout=3)
            t_elapsed = _time.time() - t_start
            print(f"\r  ✅ Интернет ({t_elapsed:.1f} сек, попытка {attempt+1})        ")
            break
        except:
            if attempt == 4:
                print(f"\r  ⚠️ Нет интернета                    ")
                print("\n  Проверьте интернет и перезапустите.")
                input("\n  Нажмите Enter...")
                return
            else:
                _time.sleep(1)
    
    # [6] Календарь
    print("  [6] Календарь...", end="", flush=True)
    for attempt in range(5):
        try:
            from caldav_client import get_calendar_url
            if get_calendar_url():
                print(f"\r  ✅ Календарь доступен               ")
                break
        except:
            pass
        if attempt == 4:
            print(f"\r  ⚠️ Календарь не отвечает            ")
        else:
            _time.sleep(1)
    
    # [7] Поддержка
    print("  [7] Поддержка...", end="", flush=True)
    for attempt in range(3):
        try:
            r = requests.post("http://157.22.202.232:8200/report", data="ping", timeout=5)
            if r.status_code in (200, 500):
                print(f"\r  ✅ Поддержка: В СЕТИ                ")
                break
        except:
            if attempt == 2:
                print(f"\r  ⚠️ Поддержка: ОФФЛАЙН               ")
            else:
                _time.sleep(1)
    
    # [8] Обновления — проверяет GitHub и доступность установщика
    print("  [8] Обновления...", end="", flush=True)
    try:
        # Сброс кеша для старых Android
        requests.get("https://raw.githubusercontent.com", timeout=3)
        r_ver = requests.get(
            "https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/version.txt",
            timeout=5
        )
        if r_ver.status_code == 200:
            remote = r_ver.text.strip()
            if remote == LOCAL_VERSION:
                print(f"\r  ✅ Версия {LOCAL_VERSION} — последняя      ")
            else:
                # Проверяем, доступен ли установщик
                try:
                    r_inst = requests.head(
                        "https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/install_organizer.py",
                        timeout=5
                    )
                    if r_inst.status_code == 200:
                        print(f"\r  🆕 Новая версия: {remote}. Запустите установщик.   ")
                    else:
                        print(f"\r  🆕 Новая версия: {remote}. Установщик недоступен.  ")
                except:
                    print(f"\r  🆕 Новая версия: {remote}. Запустите установщик.   ")
        else:
            print(f"\r  ⚠️ Не удалось проверить обновления       ")
    except:
        print(f"\r  ⚠️ Не удалось проверить обновления       ")
    
    # [9] JSON-файлы
    print("  [9] JSON-файлы...", end="", flush=True)
    json_files = {
        "ready_tasks.json": [],
        "raw_tasks.json": [],
        "user_profile.json": {"city": "", "places": [], "people": [], "anchors": {}, "people_anchors": {}, "work": ""},
        "seen_files.json": []
    }
    import json as _json
    for jf, default in json_files.items():
        path = os.path.join("/storage/emulated/0/VoiceAgent", jf)
        if not os.path.exists(path):
            for attempt in range(3):
                try:
                    with open(path, "w") as f:
                        _json.dump(default, f)
                    print(f"\r  ✅ {jf} создан (попытка {attempt+1})              ")
                    break
                except:
                    if attempt == 2:
                        print(f"\r  ⚠️ {jf} НЕ создан                          ")
                    else:
                        _time.sleep(1)
        else:
            print(f"\r  ✅ {jf} уже существует                        ")
    print("\r  ✅ JSON-файлы готовы                            ")
    
    need_register = (
        voice_config.YANDEX_APP_PASSWORD == "введите_пароль_приложения" or
        voice_config.YANDEX_APP_PASSWORD == "" or
        voice_config.YANDEX_LOGIN == "введите_логин@yandex.ru" or
        voice_config.YANDEX_LOGIN == ""
    )
    print(f"  [10] {'⚠️ Нужна регистрация' if need_register else '✅ Регистрация пройдена'}")

    print("\n" + "=" * 50)
    print("  Все проверки завершены.")
    print("  Нажмите Enter для продолжения...")
    input()
    
    if need_register:
        registered = check_registration()
        if not registered:
            print("\n  Регистрация не завершена. Выход.")
            return

    clear_screen()
    print_header("Запуск")
    print("  🟢 Мониторинг запущен")
    print("=" * 50)

    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()

    main_menu()
    print("До свидания!")

if __name__ == "__main__":
    BASE_DIR = "/storage/emulated/0/VoiceAgent"

if __name__ == "__main__":
    BASE_DIR = "/storage/emulated/0/VoiceAgent"
    main()
