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
    print(f"  ОРГАНАЙЗЕР v1.0 > {section}")
    print("=" * 50)


# ======================================================================
# ОБРАБОТКА НОВЫХ ФАЙЛОВ
# ======================================================================
def process_new_files():
    if not os.path.exists(RECORDINGS_DIR):
        return (0, 0, 0, 0)

    all_files = glob.glob(os.path.join(RECORDINGS_DIR, "*.m4a"))
    if not all_files:
        return (0, 0, 0, 0)

    processed = 0
    to_calendar = 0
    to_confirm = 0
    to_raw = 0
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

        print(f"\n🎙️ Обрабатываю: {filename}")

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
                    continue
                continue
        else:
            text = filename.replace(".m4a", "").replace("_", " ")

        if not text or not text.strip():
            try:
                os.remove(filepath)
            except OSError:
                pass
            continue

        print(f"   🎤 Распознано: «{text}»")

        task_texts = split_tasks(text)

        for single_task_text in task_texts:
            if not single_task_text or not single_task_text.strip():
                continue

            clean_task_text = ai_normalize(single_task_text)

            if not parse_intent:
                if add_raw_task:
                    add_raw_task(clean_task_text, "не категоризировано")
                to_raw += 1
                processed += 1
                continue

            intent = parse_intent(clean_task_text)

            if intent is None:
                if add_raw_task:
                    add_raw_task(clean_task_text, "не категоризировано")
                to_raw += 1
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
                        if load_tasks and save_tasks:
                            tasks = load_tasks()
                            for t in tasks:
                                if t.get("title") == task["title"] and t.get("date") == task["date"]:
                                    t["caldav_uid"] = uid
                                    t["exported"] = True
                                    t["exported_at"] = datetime.now().isoformat()
                            save_tasks(tasks)
                to_calendar += 1
            elif not has_remind and is_valid:
                if load_tasks and save_tasks:
                    tasks = load_tasks()
                    tasks.append(task)
                    save_tasks(tasks)
                to_confirm += 1
            else:
                if add_raw_task:
                    add_raw_task(clean_task_text, "не категоризировано")
                to_raw += 1

            processed += 1

        mark_file_seen(filepath)
        try:
            os.remove(filepath)
        except OSError:
            pass

    return (processed, to_calendar, to_confirm, to_raw)


# ======================================================================
# ГЛАВНОЕ МЕНЮ
# ======================================================================
def main_menu():
    """Главное меню. 0 = выход, 5 = мониторинг."""
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
            global monitor_running
            monitor_running = False
            return False

        elif choice == "1":
            try:
                from mode_1 import show_raw_tasks
                show_raw_tasks()
            except ImportError:
                print("  📭 mode_1.py не найден.")
                input("  Нажмите Enter...")

        elif choice == "2":
            run_mode_3()

        elif choice == "3":
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
            print("")
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
                    
                    elif key == "0":  # хотфикс 1.0.1: поддержка без задач
                        clear_screen()
                        print_header("Жалоба на задачу")
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
                            print("\n  Нажмите Enter для продолжения...")
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
                        elif confirm == "2":
                            print("\n  Используйте кнопки 1/2 для выбора другой задачи.")
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
                
                current_size = os.path.getsize(log_file) if os.path.exists(log_file) else 0
                
                if current_size > last_size:
                    try:
                        with open(log_file, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                        
                        all_tasks = _extract_tasks_from_log(lines)
                        
                        if all_tasks and task_index == -1:
                            task_index = len(all_tasks) - 1
                        
                        recent = lines[-15:] if len(lines) > 15 else lines
                        
                        print("\n" * 2)
                        print("-" * 50)
                        print(f"  📋 ЛОГ · {len(lines)} записей всего · Задач: {len(all_tasks)}")
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
                            print("  ⏳ Ожидание аудиозаписи...")
                        
                        print("-" * 50)
                        if all_tasks and task_index >= 0:
                            print(f"  📌 Задача {task_index+1}/{len(all_tasks)}: {all_tasks[task_index]['title'][:50]}")
                        print("  ◄ 1 / 2 ►  |  0 — пожаловаться  |  3 — очистить лог  |  Enter — выход")
                        
                    except:
                        pass
                    last_size = current_size
                else:
                    print("\r  ⏳ Ожидание аудиозаписи...   ", end="")
                
                _time.sleep(3)

        else:
            print("  ❌ Неверный выбор.")
            input("  Нажмите Enter...")


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
    """Формирует жалобу и silently отправляет через VPS (до 5 попыток)."""
    from datetime import datetime
    
    task = tasks[index] if tasks and index < len(tasks) else {"title": "неизвестно", "status": "неизвестно"}
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    print("\n  📝 Опишите проблему (одна строка):")
    comment = input("  > ").strip()
    if not comment:
        comment = "(без комментария)"
    
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
    report_lines.append("--- ПОСЛЕДНИЕ ЗАПИСИ ЛОГА ---")
    
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            log_content = f.readlines()
        report_lines.extend(log_content[-30:])
    
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
    log_file = "/storage/emulated/0/VoiceAgent/monitor.log"
    cycle_count = 0

    from datetime import datetime
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] 🟢 Фоновый мониторинг запущен\n")

    while monitor_running:
        try:
            capture = io.StringIO()
            with contextlib.redirect_stdout(capture):
                processed, to_calendar, to_confirm, to_raw = process_new_files()
            output = capture.getvalue()

            if output.strip():
                timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                try:
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"[{timestamp}] === НОВЫЙ ЦИКЛ ===\n")
                        for line in output.strip().split("\n"):
                            if line.strip():
                                f.write(f"   {line.strip()}\n")
                        f.write(f"[{timestamp}] 📊 Итого: {processed} (📅={to_calendar} 📋={to_confirm} 📥={to_raw})\n\n")
                except:
                    pass

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
                    f.write(f"[{timestamp}] ⚠️ Ошибка: {e}\n")
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
    print("")
    print("  Как получить пароль приложения:")
    print("    1. Откройте passport.yandex.ru")
    print("    2. Войдите в свой аккаунт")
    print("    3. Перейдите: Пароли приложений")
    print("    4. Нажмите: Создать пароль")
    print("    5. Выберите: Календарь")
    print("    6. Скопируйте пароль (16 букв)")
    print("")
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
    clear_screen()
    print_header("Загрузка")
    print("  Проверка системы...\n")

    import voice_config
    
    print("  ✅ Папка VoiceAgent" if os.path.exists("/storage/emulated/0/VoiceAgent") else "  ❌ Папка VoiceAgent")
    
    rec_dir = voice_config.RECORDINGS_DIR
    if not os.path.exists(rec_dir):
        try:
            os.makedirs(rec_dir)
        except:
            pass
    print("  ✅ Папка Recordings" if os.path.exists(rec_dir) else "  ❌ Папка Recordings")
    
    # Проверка библиотек
    print("  ⏳ Библиотеки — проверяем...", end="", flush=True)
    try:
        import requests
        print(f"\r  ✅ Библиотеки готовы              ")
    except ImportError:
        print(f"\r  ⏳ Устанавливаю requests...", end="", flush=True)
        import subprocess, sys
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
            import requests
            print(f"\r  ✅ Библиотеки готовы              ")
        except:
            print(f"\r  ⚠️ requests не установлен (нет интернета?)")
    
    # VPS Whisper
    print("  ⏳ VPS — проверяем...", end="", flush=True)
    vps_ok = False
    for attempt in range(5):
        try:
            import requests
            requests.get(voice_config.SERVER_URL.replace("/voice", ""), timeout=3)
            vps_ok = True
            print(f"\r  ✅ VPS отвечает (попытка {attempt+1})   ")
            break
        except:
            print(f"\r  ⏳ VPS — попытка {attempt+1}/5...", end="", flush=True)
            _time.sleep(1)
    if not vps_ok:
        print("\r  ⚠️ VPS не отвечает после 5 попыток        ")
    
    # Интернет
    print("  ⏳ Интернет — проверяем...", end="", flush=True)
    net_ok = False
    for attempt in range(5):
        try:
            import requests
            requests.get("https://google.com", timeout=3)
            net_ok = True
            print(f"\r  ✅ Интернет (попытка {attempt+1})        ")
            break
        except:
            print(f"\r  ⏳ Интернет — попытка {attempt+1}/5...", end="", flush=True)
            _time.sleep(1)
    if not net_ok:
        print("\r  ⚠️ Нет интернета после 5 попыток          ")
        print("\n  Проверьте подключение к интернету")
        print("  и перезапустите приложение.")
        print("\n  Нажмите Enter для выхода...")
        input()
        return
    
    # Календарь
    print("  ⏳ Календарь — проверяем...", end="", flush=True)
    cal_ok = False
    for attempt in range(5):
        try:
            from caldav_client import get_calendar_url
            url = get_calendar_url()
            if url:
                cal_ok = True
                print(f"\r  ✅ Календарь доступен (попытка {attempt+1})   ")
                break
        except:
            pass
        if not cal_ok:
            print(f"\r  ⏳ Календарь — попытка {attempt+1}/5...", end="", flush=True)
            _time.sleep(1)
    if not cal_ok:
        print("\r  ⚠️ Календарь не отвечает после 5 попыток   ")
    
    # Служба поддержки
    print("  ⏳ Поддержка — проверяем...", end="", flush=True)
    support_ok = False
    for attempt in range(3):
        try:
            r = requests.post("http://157.22.202.232:8200/report", data="ping", timeout=5)
            if r.status_code in (200, 500):
                support_ok = True
                print(f"\r  ✅ Поддержка: В СЕТИ (попытка {attempt+1})   ")
                break
        except:
            print(f"\r  ⏳ Поддержка — попытка {attempt+1}/3...", end="", flush=True)
            _time.sleep(1)
    if not support_ok:
        print("\r  ⚠️ Поддержка: ОФФЛАЙН (программа работает)   ")
    
    # Проверка обновлений + автообновление (Блок 6.1)
    LOCAL_VERSION = "1.0.3"
    update_available = False
    print("  ⏳ Обновления — проверяем...", end="", flush=True)
    try:
        r = requests.get(
            "https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/version.txt",
            timeout=5
        )
        if r.status_code == 200:
            remote_version = r.text.strip()
            if remote_version != LOCAL_VERSION:
                print(f"\r  🆕 Доступна новая версия: {remote_version}   ")
                update_available = True
            else:
                print(f"\r  ✅ Версия {LOCAL_VERSION} — актуальна      ")
        else:
            print(f"\r  ⚠️ Не удалось проверить обновления       ")
    except:
        print(f"\r  ⚠️ Не удалось проверить обновления       ")
    
    # Автообновление: молча, без вопроса
    if update_available:
        print(f"\n  {'='*50}")
        print(f"  \u26a0\ufe0f Новая версия: {remote_version}. Обновляю...")
        try:
            # Качаем свежий main.py
            r_main = requests.get(
                "https://raw.githubusercontent.com/Vladimir-1337/VoiceAgent/main/main.py",
                timeout=10
            )
            if r_main.status_code == 200:
                with open("/storage/emulated/0/VoiceAgent/main.py", "w", encoding="utf-8") as f:
                    f.write(r_main.text)
                # Обновляем локальный version.txt чтобы больше не предлагать
                with open("/storage/emulated/0/VoiceAgent/version.txt", "w") as f:
                    f.write(remote_version)
                print(f"  \u2705 Обновлено до {remote_version}. Перезапустите.")
                print(f"  {'='*50}")
                print("\n  Нажмите Enter чтобы перезапустить...")
                input()
                return
        except:
            print(f"  \u26a0\ufe0f Не удалось обновить. Продолжаю на старой версии.")
    
    need_register = (
        voice_config.YANDEX_APP_PASSWORD == "введите_пароль_приложения" or
        voice_config.YANDEX_APP_PASSWORD == "" or
        voice_config.YANDEX_LOGIN == "введите_логин@yandex.ru" or
        voice_config.YANDEX_LOGIN == ""
    )
    print("  ⚠️ Нужна регистрация" if need_register else "  ✅ Регистрация пройдена")

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
    main()